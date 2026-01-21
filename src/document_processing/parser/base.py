"""
Document Parser Base Classes
文档解析器基类
"""

from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ParsedDocument(BaseModel):
    """解析后的文档模型"""
    title: str = Field(..., description="文档标题")
    content: str = Field(..., description="文档内容")
    metadata: dict = Field(default_factory=dict, description="文档元数据")
    page_count: Optional[int] = Field(None, description="页数（如果适用）")
    word_count: int = Field(..., description="字数")
    file_type: str = Field(..., description="文件类型")


class BaseParser(ABC):
    """文档解析器基类"""

    @abstractmethod
    def can_parse(self, file_path: str) -> bool:
        """
        判断是否可以解析该文件

        Args:
            file_path: 文件路径

        Returns:
            bool: 是否可以解析
        """
        pass

    @abstractmethod
    async def parse(self, file_path: str) -> ParsedDocument:
        """
        解析文档

        Args:
            file_path: 文件路径

        Returns:
            ParsedDocument: 解析后的文档对象
        """
        pass

    def _extract_metadata(self, file_path: str) -> dict:
        """
        提取文件元数据

        Args:
            file_path: 文件路径

        Returns:
            dict: 元数据字典
        """
        path = Path(file_path)
        stat = path.stat()

        return {
            "file_name": path.name,
            "file_size": stat.st_size,
            "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
        }
