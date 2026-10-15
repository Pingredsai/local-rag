"""答案生成：调用 Ollama 的 LLM。"""
import logging
from typing import Iterator

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一个严谨的企业知识库助手。请仔细阅读【资料】，找到与问题直接相关的句子，然后基于资料回答。

规则：
1. 资料中明确包含答案时，必须直接回答，不能回答“资料不足”。
2. 只有资料确实没有相关信息时，才回答“资料不足”。
3. 回答简洁准确，使用中文，不补充资料中没有的结论。
4. 不要提及“根据资料”这类表述。
5. 不要输出与最终答案相互矛盾的内容。

【资料】
{context}
"""


class Generator:
    def __init__(self, model: str | None = None, base_url: str | None = None):
        self.model = model or settings.llm_model
        self.base_url = (base_url or settings.ollama_url).rstrip("/")
        self.options = {"temperature": 0.1, "top_p": 0.8, "num_ctx": 4096}

    def build_prompt(self, question: str, contexts: list[str]) -> str:
        context_text = "\n\n---\n\n".join(contexts) if contexts else "（无相关资料）"
        system = SYSTEM_PROMPT.format(context=context_text)
        return f"{system}\n\n【问题】\n{question}\n\n【回答】\n"

    def generate(self, question: str, contexts: list[str]) -> str:
        """非流式生成。"""
        prompt = self.build_prompt(question, contexts)
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": self.options,
        }

        with httpx.Client(timeout=600.0) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            return resp.json().get("response", "").strip()

    def generate_stream(self, question: str, contexts: list[str]) -> Iterator[str]:
        """流式生成（逐段返回）。"""
        prompt = self.build_prompt(question, contexts)
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": self.options,
        }

        with httpx.Client(timeout=600.0) as client:
            with client.stream("POST", url, json=payload) as resp:
                resp.raise_for_status()
                import json

                for line in resp.iter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    piece = data.get("response", "")
                    if piece:
                        yield piece