"""
Parser Factory
解析器工厂，根据文件类型选择合适的解析器
"""

import logging
from typing import List
from .base import BaseParser, ParsedDocument
from .pdf_parser import PDFParser
from .docx_parser import DOCXParser
from .markdown_parser import MarkdownParser
from .html_parser import HTMLParser

logger = logging.getLogger(__name__)


class ParserFactory:
    """解析器工厂"""

    def __init__(self):
        """初始化解析器工厂"""
        self.parsers: List[BaseParser] = [
            PDFParser(),
            DOCXParser(),
            MarkdownParser(),
            HTMLParser()
        ]

    def get_parser(self, file_path: str) -> BaseParser:
        """
        根据文件类型获取解析器

        Args:
            file_path: 文件路径

        Returns:
            BaseParser: 解析器实例

        Raises:
            ValueError: 找不到合适的解析器
        """
        for parser in self.parsers:
            if parser.can_parse(file_path):
                logger.info(f"Selected parser: {parser.__class__.__name__} for {file_path}")
                return parser

        raise ValueError(f"No parser found for file: {file_path}")

    async def parse_file(self, file_path: str) -> ParsedDocument:
        """
        解析文件

        Args:
            file_path: 文件路径

        Returns:
            ParsedDocument: 解析后的文档对象
        """
        parser = self.get_parser(file_path)
        return await parser.parse(file_path)

    def get_supported_extensions(self) -> List[str]:
        """
        获取支持的文件扩展名列表

        Returns:
            List[str]: 支持的扩展名列表
        """
        return [".pdf", ".docx", ".doc", ".md", ".html", ".htm"]


# 全局单例
_parser_factory = None


def get_parser_factory() -> ParserFactory:
    """获取解析器工厂单例"""
    global _parser_factory
    if _parser_factory is None:
        _parser_factory = ParserFactory()
    return _parser_factory
