"""健康检查：确认 Qdrant 和 Ollama 都活着。"""
import logging

import httpx
from fastapi import APIRouter

from app.config import settings
from app.models.schemas import HealthResponse

logger = logging.getLogger(__name__)
router = APIRouter()


def _check(url: str) -> str:
    try:
        with httpx.Client(timeout=5.0) as c:
            r = c.get(url)
            return "ok" if r.status_code == 200 else f"error({r.status_code})"
    except Exception as e:
        logger.warning("健康检查失败 %s: %s", url, e)
        return "unreachable"


@router.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="ok",
        qdrant=_check(f"{settings.qdrant_url}/collections"),
        ollama=_check(f"{settings.ollama_url}/api/tags"),
        llm_model=settings.llm_model,
        embed_model=settings.embed_model,
    )