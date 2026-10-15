"""向量化：调用 Ollama 的 embedding 接口。"""
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class Embedder:
    """
    使用 Ollama 提供的 embedding 模型（默认 bge-m3）。

    不依赖 sentence-transformers，减少部署体积。
    """

    def __init__(self, model: str | None = None, base_url: str | None = None):
        self.model = model or settings.embed_model
        self.base_url = (base_url or settings.ollama_url).rstrip("/")

    def embed(self, texts: list[str]) -> list[list[float]]:
        """批量向量化。"""
        if not texts:
            return []

        url = f"{self.base_url}/api/embed"
        payload = {"model": self.model, "input": texts}

        with httpx.Client(timeout=300.0) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()

        embeddings = data.get("embeddings", [])
        if not embeddings:
            raise RuntimeError(f"Ollama 未返回向量，响应: {data}")

        return embeddings

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]