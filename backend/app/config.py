"""全局配置：全部可通过环境变量覆盖。"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 服务地址
    qdrant_url: str = "http://localhost:6333"
    ollama_url: str = "http://localhost:11434"

    # 模型
    embed_model: str = "bge-m3"
    llm_model: str = "qwen2.5:3b"

    # 检索参数
    top_k: int = 5
    use_rerank: bool = False

    # 路径
    docs_dir: str = "./data/documents"
    collection_name: str = "localrag"

    # 切块参数
    chunk_size: int = 500
    chunk_overlap: int = 80

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()