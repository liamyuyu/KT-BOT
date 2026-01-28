"""
Base Filter
过滤器基类：定义过滤器的通用接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

from ..models import RetrievalResult


class BaseFilter(ABC):
    """
    过滤器基类

    定义所有过滤器的通用接口
    支持两种过滤模式：
    1. Pre-filtering: 在检索之前通过 ChromaDB where 子句过滤（效率更高）
    2. Post-filtering: 在检索之后通过代码过滤（更灵活）
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化过滤器

        Args:
            config: 过滤器配置字典
        """
        self.config = config or {}

    @abstractmethod
    def to_chroma_where(self) -> Optional[Dict[str, Any]]:
        """
        转换为 ChromaDB where 子句格式（Pre-filtering）

        Returns:
            ChromaDB where 子句字典，如果不支持 pre-filtering 则返回 None
        """
        pass

    @abstractmethod
    def apply(self, results: List[RetrievalResult]) -> List[RetrievalResult]:
        """
        应用过滤器到检索结果（Post-filtering）

        Args:
            results: 检索结果列表

        Returns:
            过滤后的结果列表
        """
        pass

    @abstractmethod
    def is_empty(self) -> bool:
        """
        检查过滤器是否为空（没有任何过滤条件）

        Returns:
            bool: True 表示没有任何过滤条件
        """
        pass

    def __repr__(self) -> str:
        """字符串表示"""
        return f"{self.__class__.__name__}(config={self.config})"
