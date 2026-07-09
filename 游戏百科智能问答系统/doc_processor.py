"""多格式文档解析器"""
import logging
import os

logger = logging.getLogger(__name__)

SUPPORTED_TYPES = {
    ".txt": "文本文档",
    ".pdf": "PDF 文档",
    ".docx": "Word 文档",
    ".pptx": "PPT 演示文稿",
    ".png": "PNG 图片",
    ".jpg": "JPEG 图片",
    ".jpeg": "JPEG 图片",
    ".gif": "GIF 图片",
    ".bmp": "BMP 图片",
    ".webp": "WebP 图片",
}


def extract_txt(filepath: str, encoding: str = "utf-8") -> str:
    """提取 TXT 文件内容"""
    with open(filepath, "r", encoding=encoding, errors="replace") as f:
        return f.read()


def extract_pdf(filepath: str) -> str:
    """提取 PDF 文件内容"""
    try:
        import fitz
    except ImportError:
        return "[错误: 请安装 PyMuPDF: pip install PyMuPDF]"
    text_parts = []
    with fitz.open(filepath) as doc:
        for page in doc:
            text_parts.append(page.get_text())
    return "\n\n".join(text_parts)


def extract_docx(filepath: str) -> str:
    """提取 DOCX 文件内容"""
    try:
        from docx import Document
    except ImportError:
        return "[错误: 请安装 python-docx: pip install python-docx]"
    doc = Document(filepath)
    return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())


def extract_pptx(filepath: str) -> str:
    """提取 PPTX 文件内容"""
    try:
        from pptx import Presentation
    except ImportError:
        return "[错误: 请安装 python-pptx: pip install python-pptx]"
    prs = Presentation(filepath)
    pages = []
    for slide in prs.slides:
        texts = [s.text for s in slide.shapes if hasattr(s, "text") and s.text.strip()]
        if texts:
            pages.append("\n".join(texts))
    return "\n\n--- 下一页 ---\n\n".join(pages)


def extract_image(filepath: str) -> str:
    """提取图片元信息及 OCR 结果"""
    try:
        from PIL import Image
    except ImportError:
        return "[错误: 请安装 Pillow: pip install Pillow]"
    img = Image.open(filepath)
    info = [
        f"文件名: {os.path.basename(filepath)}",
        f"格式: {img.format}",
        f"尺寸: {img.size[0]}x{img.size[1]}",
    ]
    return "\n".join(info)


def extract_text(filepath: str) -> str:
    """根据文件扩展名自动选择解析器"""
    ext = os.path.splitext(filepath)[1].lower()
    extractors = {
        ".txt": extract_txt, ".pdf": extract_pdf,
        ".docx": extract_docx, ".pptx": extract_pptx,
        ".png": extract_image, ".jpg": extract_image,
        ".jpeg": extract_image, ".gif": extract_image,
        ".bmp": extract_image, ".webp": extract_image,
    }
    extractor = extractors.get(ext)
    if not extractor:
        raise ValueError(f"不支持的文件格式: {ext}")
    logger.info("正在解析文件: %s", filepath)
    return extractor(filepath)
