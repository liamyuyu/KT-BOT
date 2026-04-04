"""
HTML Parser
HTML 文档解析器
"""

import logging
from pathlib import Path
from bs4 import BeautifulSoup
from .base import BaseParser, ParsedDocument

logger = logging.getLogger(__name__)


class HTMLParser(BaseParser):
    """HTML 文档解析器"""

    def can_parse(self, file_path: str) -> bool:
        """判断是否为 HTML 文件"""
        return file_path.lower().endswith(('.html', '.htm'))

    async def parse(self, file_path: str) -> ParsedDocument:
        """
        解析 HTML 文档

        Args:
            file_path: HTML 文件路径

        Returns:
            ParsedDocument: 解析后的文档对象
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
        except UnicodeDecodeError:
            # 尝试其他编码
            with open(file_path, 'r', encoding='latin-1') as f:
                html_content = f.read()

        soup = BeautifulSoup(html_content, 'html.parser')

        # 移除 script 和 style 标签
        for script in soup(['script', 'style', 'noscript']):
            script.decompose()

        # 提取标题
        title = self._extract_title(soup, file_path)

        # 提取主要内容
        content = self._extract_content(soup)

        # 提取表格
        tables = self._extract_tables(soup)
        if tables:
            content += "\n\n" + tables

        # 元数据
        metadata = self._extract_metadata(file_path)
        metadata.update(self._extract_html_metadata(soup))

        return ParsedDocument(
            title=title,
            content=content.strip(),
            metadata=metadata,
            word_count=len(content.split()),
            file_type="html"
        )

    def _extract_title(self, soup: BeautifulSoup, file_path: str) -> str:
        """
        提取文档标题

        优先级:
        1. <title> 标签
        2. <h1> 标签
        3. 文件名
        """
        # 尝试 title 标签
        if soup.title and soup.title.string:
            return soup.title.string.strip()

        # 尝试第一个 h1 标签
        h1 = soup.find('h1')
        if h1 and h1.get_text():
            return h1.get_text().strip()

        # 降级到文件名
        return Path(file_path).stem

    def _extract_content(self, soup: BeautifulSoup) -> str:
        """
        提取文本内容

        优先提取 <main>, <article>, <body> 中的内容
        """
        # 尝试按优先级提取内容区域
        content_containers = [
            soup.find('main'),
            soup.find('article'),
            soup.find('div', {'class': ['content', 'main-content', 'article-content']}),
            soup.find('body')
        ]

        for container in content_containers:
            if container:
                text = container.get_text(separator='\n', strip=True)
                if text:
                    return text

        # 降级到整个文档
        return soup.get_text(separator='\n', strip=True)

    def _extract_tables(self, soup: BeautifulSoup) -> str:
        """
        提取表格内容并格式化为文本

        Returns:
            str: 格式化的表格文本
        """
        tables = soup.find_all('table')
        if not tables:
            return ""

        result = []
        for idx, table in enumerate(tables, 1):
            result.append(f"\n### Table {idx} ###")

            rows = table.find_all('tr')
            for row in rows:
                # 提取表头和单元格
                cells = row.find_all(['th', 'td'])
                row_text = " | ".join(cell.get_text(strip=True) for cell in cells)
                if row_text:
                    result.append(row_text)

        return "\n".join(result)

    def _extract_html_metadata(self, soup: BeautifulSoup) -> dict:
        """
        提取 HTML meta 标签信息

        Returns:
            dict: meta 信息字典
        """
        metadata = {}

        # 提取常见 meta 标签
        meta_tags = {
            'description': ['name', 'description'],
            'keywords': ['name', 'keywords'],
            'author': ['name', 'author'],
            'og:title': ['property', 'og:title'],
            'og:description': ['property', 'og:description']
        }

        for key, (attr_name, attr_value) in meta_tags.items():
            meta = soup.find('meta', {attr_name: attr_value})
            if meta and meta.get('content'):
                metadata[key] = meta.get('content')

        return metadata
