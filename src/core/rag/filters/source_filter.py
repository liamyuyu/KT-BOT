"""
Source Filter
来源过滤器：按数据来源（jira/confluence/local）过滤检索结果
"""

import logging
from typing import Dict, Any, Optional, List

from .base import BaseFilter
from ..models import RetrievalResult

logger = logging.getLogger(__name__)


class SourceFilter(BaseFilter):
    """
    来源过滤器

    支持的来源类型：
    - jira: Jira Issues
    - confluence: Confluence Pages
    - local: 本地文档
    """

    VALID_SOURCES = {"jira", "confluence", "local"}

    def __init__(self, sources: List[str]):
        """
        初始化来源过滤器

        Args:
            sources: 允许的来源列表（如 ["jira", "confluence"]）

        Raises:
            ValueError: 如果提供了无效的来源类型
        """
        super().__init__({"sources": sources})
        self.sources = [s.lower() for s in sources] if sources else []

        # 验证来源类型
        invalid_sources = set(self.sources) - self.VALID_SOURCES
        if invalid_sources:
            logger.warning(f"Invalid sources: {invalid_sources}. Valid sources: {self.VALID_SOURCES}")

        logger.info(f"SourceFilter initialized with sources: {self.sources}")

    def to_chroma_where(self) -> Optional[Dict[str, Any]]:
        """
        转换为 ChromaDB where 子句格式

        Returns:
            ChromaDB where 子句字典，如果没有过滤条件则返回 None
        """
        if not self.sources:
            return None

        # 单个来源
        if len(self.sources) == 1:
            return {"source": self.sources[0]}

        # 多个来源（使用 $in 操作符）
        return {"source": {"$in": self.sources}}

    def apply(self, results: List[RetrievalResult]) -> List[RetrievalResult]:
        """
        应用过滤器到检索结果（Post-filtering）

        Args:
            results: 检索结果列表

        Returns:
            过滤后的结果列表
        """
        if not self.sources:
            return results

        filtered_results = []
        for result in results:
            source = result.metadata.get("source", "").lower()
            if source in self.sources:
                filtered_results.append(result)

        logger.debug(
            f"SourceFilter applied: {len(results)} -> {len(filtered_results)} results "
            f"(sources: {self.sources})"
        )

        return filtered_results

    def is_empty(self) -> bool:
        """
        检查过滤器是否为空

        Returns:
            bool: True 表示没有任何过滤条件
        """
        return not self.sources

    def add_source(self, source: str) -> None:
        """
        添加来源到过滤器

        Args:
            source: 来源类型
        """
        source = source.lower()
        if source not in self.sources and source in self.VALID_SOURCES:
            self.sources.append(source)
            logger.debug(f"Added source: {source}")

    def remove_source(self, source: str) -> None:
        """
        从过滤器移除来源

        Args:
            source: 来源类型
        """
        source = source.lower()
        if source in self.sources:
            self.sources.remove(source)
            logger.debug(f"Removed source: {source}")

    def clear(self) -> None:
        """清空所有来源"""
        self.sources.clear()
        logger.debug("Cleared all sources")
