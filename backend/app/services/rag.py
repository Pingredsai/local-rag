"""RAG 编排：把解析、切块、向量化、检索、生成串起来。"""
import logging
import uuid
from pathlib import Path
from typing import Iterator

from app.config import settings
from app.services.chunker import chunk_text
from app.services.embedder import Embedder
from app.services.generator import Generator
from app.services.parser import parse_document
from app.services.vectorstore import VectorStore

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(self):
        self.embedder = Embedder()
        self.store = VectorStore()
        self.generator = Generator()

    # ---------- 索引 ----------
    def index_document(self, path: Path, document_id: str | None = None) -> dict:
        """
        解析 → 切块 → 向量化 → 入库。
        返回 {document_id, filename, chunks}
        """
        doc_id = document_id or str(uuid.uuid4())
        filename = path.name

        logger.info("开始索引: %s", filename)
        text = parse_document(path)
        if not text.strip():
            raise ValueError(f"无法从 {filename} 提取文本（可能是不支持的格式或扫描件）")

        chunks = chunk_text(text, settings.chunk_size, settings.chunk_overlap)
        if not chunks:
            raise ValueError(f"{filename} 切块后为空")

        logger.info("  %s → %d 个文本块", filename, len(chunks))

        vectors = self.embedder.embed(chunks)
        self.store.add_chunks(doc_id, filename, chunks, vectors)

        logger.info("  %s 索引完成", filename)
        return {"document_id": doc_id, "filename": filename, "chunks": len(chunks)}

    # ---------- 问答 ----------
    def retrieve(self, question: str, top_k: int | None = None) -> list[dict]:
        k = top_k or settings.top_k
        qvec = self.embedder.embed_one(question)
        return self.store.search(qvec, top_k=k)

    def answer(self, question: str, top_k: int | None = None) -> tuple[str, list[dict]]:
        hits = self.retrieve(question, top_k)
        contexts = [h["text"] for h in hits]
        answer = self.generator.generate(question, contexts)
        return answer, hits

    def answer_stream(self, question: str, top_k: int | None = None) -> Iterator[str]:
        hits = self.retrieve(question, top_k)
        contexts = [h["text"] for h in hits]
        yield from self.generator.generate_stream(question, contexts)

    # ---------- 文档管理 ----------
    def list_documents(self) -> list[dict]:
        return self.store.list_documents()

    def delete_document(self, document_id: str) -> None:
        self.store.delete_document(document_id)


# 全局单例（进程内复用）
_service: RAGService | None = None


def get_service() -> RAGService:
    global _service
    if _service is None:
        _service = RAGService()
    return _service