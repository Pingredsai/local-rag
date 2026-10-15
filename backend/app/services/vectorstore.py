"""向量库操作：封装 Qdrant。"""
import logging
import uuid
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from app.config import settings

logger = logging.getLogger(__name__)

# BGE-M3 的输出维度
VECTOR_SIZE = 1024


class VectorStore:
    def __init__(self, url: str | None = None, collection: str | None = None):
        self.client = QdrantClient(url=url or settings.qdrant_url)
        self.collection = collection or settings.collection_name
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        existing = [c.name for c in self.client.get_collections().collections]
        if self.collection not in existing:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )
            logger.info("已创建向量集合: %s", self.collection)

    def add_chunks(
        self,
        document_id: str,
        filename: str,
        chunks: list[str],
        vectors: list[list[float]],
    ) -> None:
        """把切块和向量写入库。"""
        points = []
        for i, (chunk, vec) in enumerate(zip(chunks, vectors)):
            # 用 document_id + 序号生成确定性 ID
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{document_id}-{i}"))
            points.append(
                PointStruct(
                    id=point_id,
                    vector=vec,
                    payload={
                        "document_id": document_id,
                        "filename": filename,
                        "chunk_index": i,
                        "text": chunk,
                    },
                )
            )

        self.client.upsert(collection_name=self.collection, points=points)

    def search(self, query_vector: list[float], top_k: int = 5) -> list[dict[str, Any]]:
        """向量检索，返回命中的块。"""
        # 注意：qdrant-client 新版为 query_points，旧版为 search
        try:
            hits = self.client.search(
                collection_name=self.collection,
                query_vector=query_vector,
                limit=top_k,
                with_payload=True,
            )
        except AttributeError:
            result = self.client.query_points(
                collection_name=self.collection,
                query=query_vector,
                limit=top_k,
                with_payload=True,
            )
            hits = result.points

        return [
            {
                "text": h.payload.get("text", ""),
                "filename": h.payload.get("filename", ""),
                "chunk_index": h.payload.get("chunk_index", 0),
                "score": float(h.score),
                "document_id": h.payload.get("document_id", ""),
            }
            for h in hits
        ]

    def delete_document(self, document_id: str) -> None:
        self.client.delete(
            collection_name=self.collection,
            points_selector=Filter(
                must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
            ),
        )

    def list_documents(self) -> list[dict[str, Any]]:
        """列出已索引的文档（按 document_id 聚合）。"""
        docs: dict[str, dict[str, Any]] = {}
        offset = None

        while True:
            records, offset = self.client.scroll(
                collection_name=self.collection,
                limit=256,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            for r in records:
                did = r.payload.get("document_id", "")
                if did not in docs:
                    docs[did] = {
                        "document_id": did,
                        "filename": r.payload.get("filename", ""),
                        "chunks": 0,
                    }
                docs[did]["chunks"] += 1

            if offset is None:
                break

        return list(docs.values())