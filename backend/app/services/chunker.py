"""文本切块：把长文本切成适合检索的小块。"""
import re


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 80) -> list[str]:
    """
    按段落优先切块，超长段落再按句子切。

    :param text: 原始文本
    :param chunk_size: 每块目标字符数
    :param overlap: 相邻块的重叠字符数（保持上下文连贯）
    """
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        return []

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) <= chunk_size:
            current = f"{current}\n\n{para}".strip()
        else:
            if current:
                chunks.append(current)
            # 段落本身超长 → 按句子切
            if len(para) > chunk_size:
                chunks.extend(_split_long_paragraph(para, chunk_size, overlap))
                current = ""
            else:
                current = para

    if current:
        chunks.append(current)

    return [c for c in chunks if len(c) > 20]


def _split_long_paragraph(text: str, chunk_size: int, overlap: int) -> list[str]:
    """把超长段落按句号/换行切成小块。"""
    sentences = re.split(r"(?<=[。！？.!?])\s*", text)
    chunks, current = [], ""

    for sent in sentences:
        if not sent.strip():
            continue
        if len(current) + len(sent) <= chunk_size:
            current += sent
        else:
            if current:
                chunks.append(current)
            current = sent

    if current:
        chunks.append(current)

    return chunks