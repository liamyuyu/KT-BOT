"""
Base Retriever
检索器基类：定义检索器的通用接口
"""

from abc import ABC, abstractmethod
from typing import List

from ..models import RetrievalResult, RetrievalConfig


class BaseRetriever(ABC):
    """
    检索器基类
    定义所有检索器的通用接口
    """

    def __init__(self, config: RetrievalConfig = None):
        """
        初始化检索器

        Args:
            config: 检索配置
        """
        self.config = config or RetrievalConfig()

    @abstractmethod
    async def retrieve(
        self,
        query: str,
        top_k: int = None,
        **kwargs
    ) -> List[RetrievalResult]:
        """
        检索相关文档

        Args:
            query: 查询文本
            top_k: 返回结果数量（覆盖配置）
            **kwargs: 其他检索参数

        Returns:
            RetrievalResult 列表

        Raises:
            RetrievalError: 检索失败时抛出
        """
        pass

    @abstractmethod
    async def batch_retrieve(
        self,
        queries: List[str],
        top_k: int = None,
        **kwargs
    ) -> List[List[RetrievalResult]]:
        """
        批量检索

        Args:
            queries: 查询文本列表
            top_k: 每个查询返回的结果数量
            **kwargs: 其他检索参数

        Returns:
            嵌套的 RetrievalResult 列表（每个查询对应一个列表）

        Raises:
            RetrievalError: 检索失败时抛出
        """
        pass
