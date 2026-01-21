"""
PDF Parser
PDF 文档解析器
"""

import logging
from pathlib import Path
from .base import BaseParser, ParsedDocument

logger = logging.getLogger(__name__)


class PDFParser(BaseParser):
    """PDF 文档解析器"""

    def can_parse(self, file_path: str) -> bool:
        """判断是否为 PDF 文件"""
        return file_path.lower().endswith('.pdf')

    async def parse(self, file_path: str) -> ParsedDocument:
        """
        解析 PDF 文档

        Args:
            file_path: PDF 文件路径

        Returns:
            ParsedDocument: 解析后的文档对象
        """
        try:
            from pypdf import PdfReader
        except ImportError:
            raise ImportError("pypdf not installed. Run: pip install pypdf")

        reader = PdfReader(file_path)

        # 提取文本
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text.strip():
                pages.append(text)

        content = "\n\n".join(pages)

        # 元数据
        metadata = self._extract_metadata(file_path)
        metadata.update({
            "page_count": len(reader.pages),
            "pdf_info": dict(reader.metadata) if reader.metadata else {}
        })

        # 标题提取
        title = None
        if reader.metadata and reader.metadata.get("/Title"):
            title = reader.metadata.get("/Title")
        elif pages:
            # 使用第一页第一行作为标题
            first_line = pages[0].split("\n")[0][:100] if pages[0] else None
            title = first_line
        
        if not title:
            title = Path(file_path).stem

        return ParsedDocument(
            title=title,
            content=content,
            metadata=metadata,
            page_count=len(reader.pages),
            word_count=len(content.split()),
            file_type="pdf"
        )
