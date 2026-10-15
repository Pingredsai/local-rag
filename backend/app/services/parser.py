"""文档解析：把各种格式转成纯文本。"""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

SUPPORTED = {".pdf", ".txt", ".md", ".docx"}


def parse_document(path: Path) -> str:
    """解析文档并返回纯文本。不支持的格式返回空字符串。"""
    suffix = path.suffix.lower()

    if suffix not in SUPPORTED:
        logger.warning("不支持的格式: %s", suffix)
        return ""

    try:
        if suffix == ".pdf":
            return _parse_pdf(path)
        if suffix == ".docx":
            return _parse_docx(path)
        if suffix in (".txt", ".md"):
            return path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        logger.exception("解析失败 %s: %s", path.name, e)
        return ""


def _parse_pdf(path: Path) -> str:
    import fitz  # PyMuPDF

    parts = []
    with fitz.open(str(path)) as doc:
        for i, page in enumerate(doc):
            text = page.get_text()
            if text.strip():
                parts.append(f"[第 {i + 1} 页]\n{text}")
    return "\n\n".join(parts)


def _parse_docx(path: Path) -> str:
    import docx

    doc = docx.Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())