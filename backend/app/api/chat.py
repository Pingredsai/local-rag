"""问答与文档管理接口。"""
import base64
import json
import logging
import shutil
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.config import settings
from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    Source,
    UploadResponse,
)
from app.services.rag import get_service
from app.services.parser import SUPPORTED

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------- 文档 ----------------
@router.post("/documents/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """上传并索引一个文档。"""
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的格式 {suffix}，当前支持: {', '.join(sorted(SUPPORTED))}",
        )

    docs_dir = Path(settings.docs_dir)
    docs_dir.mkdir(parents=True, exist_ok=True)
    dest = docs_dir / file.filename

    # 保存文件
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        result = get_service().index_document(dest)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("索引失败")
        raise HTTPException(status_code=500, detail=f"索引失败: {e}")

    return UploadResponse(
        document_id=result["document_id"],
        filename=result["filename"],
        chunks=result["chunks"],
        message=f"已索引 {result['chunks']} 个文本块",
    )


@router.get("/documents")
def list_documents():
    """列出已索引的文档。"""
    return {"documents": get_service().list_documents()}


@router.delete("/documents/{document_id}")
def delete_document(document_id: str):
    """删除文档及其向量。"""
    get_service().delete_document(document_id)
    return {"message": "已删除"}


# ---------------- 问答 ----------------
@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """提问（非流式）。"""
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="问题不能为空")

    try:
        answer, hits = get_service().answer(req.question, req.top_k)
    except Exception as e:
        logger.exception("问答失败")
        raise HTTPException(status_code=500, detail=f"问答失败: {e}")

    return ChatResponse(
        answer=answer,
        sources=[
            Source(
                file=h["filename"],
                chunk_index=h["chunk_index"],
                score=round(h["score"], 4),
                preview=h["text"][:150],
            )
            for h in hits
        ],
    )


@router.post("/chat/stream")
def chat_stream(req: ChatRequest):
    """提问（流式输出，来源通过响应头返回）。"""
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="问题不能为空")

    try:
        hits = get_service().retrieve(req.question, req.top_k)
    except Exception as e:
        logger.exception("流式问答检索失败")
        raise HTTPException(status_code=500, detail=f"检索失败: {e}")

    source_items = [
        {
            "file": h["filename"],
            "chunk_index": h["chunk_index"],
            "score": round(h["score"], 4),
        }
        for h in hits
    ]
    sources_header = base64.urlsafe_b64encode(
        json.dumps(source_items, ensure_ascii=False).encode("utf-8")
    ).decode("ascii")

    def gen():
        try:
            contexts = [h["text"] for h in hits]
            yield from get_service().generator.generate_stream(req.question, contexts)
        except Exception as e:
            logger.exception("流式问答失败")
            yield f"\n[错误] {e}"

    return StreamingResponse(
        gen(),
        media_type="text/plain; charset=utf-8",
        headers={
            "X-LocalRAG-Sources": sources_header,
            "Access-Control-Expose-Headers": "X-LocalRAG-Sources",
        },
    )