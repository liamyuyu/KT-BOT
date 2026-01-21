"""
Markdown Parser
Markdown 文档解析器
"""

import logging
from pathlib import Path
from .base import BaseParser, ParsedDocument

logger = logging.getLogger(__name__)


class MarkdownParser(BaseParser):
    """Markdown 文档解析器"""

    def can_parse(self, file_path: str) -> bool:
        """判断是否为 Markdown 文件"""
        return file_path.lower().endswith('.md')

    async def parse(self, file_path: str) -> ParsedDocument:
        """
        解析 Markdown 文档

        Args:
            file_path: Markdown 文件路径

        Returns:
            ParsedDocument: 解析后的文档对象
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取标题（第一个 # 标题）
        title = Path(file_path).stem
        for line in content.split('\n'):
            if line.startswith('# '):
                title = line[2:].strip()
                break

        # 元数据
        metadata = self._extract_metadata(file_path)

        return ParsedDocument(
            title=title,
            content=content,
            metadata=metadata,
            word_count=len(content.split()),
            file_type="markdown"
        )
