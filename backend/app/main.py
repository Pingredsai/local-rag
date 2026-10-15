"""LocalRAG 后端入口。"""
import logging
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import chat, health
from app.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("localrag")

app = FastAPI(
    title="LocalRAG",
    description="一键部署的私有化知识库问答系统",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 路由
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(chat.router, prefix="/api", tags=["chat"])

# 前端静态文件
# 路径自动计算：容器内为 /app/frontend，本地运行时为 <项目根>/frontend
_BASE = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = Path(os.getenv("FRONTEND_DIR", str(_BASE / "frontend")))

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    def index():
        return FileResponse(str(FRONTEND_DIR / "index.html"))


@app.on_event("startup")
def on_startup():
    Path(settings.docs_dir).mkdir(parents=True, exist_ok=True)
    logger.info("LocalRAG 启动完成")
    logger.info("  Qdrant   : %s", settings.qdrant_url)
    logger.info("  Ollama   : %s", settings.ollama_url)
    logger.info("  LLM 模型  : %s", settings.llm_model)
    logger.info("  嵌入模型  : %s", settings.embed_model)