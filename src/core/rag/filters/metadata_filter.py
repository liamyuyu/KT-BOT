"""
Metadata Filter
元数据过滤器：按元数据字段（如 priority, status, type）过滤检索结果
"""

import logging
from typing import Dict, Any, Optional, List, Union

from .base import BaseFilter
from ..models import RetrievalResult

logger = logging.getLogger(__name__)


class MetadataFilter(BaseFilter):
    """
    元数据过滤器

    支持的操作符：
    - 相等（默认）：{"priority": "High"}
    - 列表包含：{"priority": ["High", "Medium"]}
    - 嵌套条件：{"priority": {"$in": ["High", "Medium"]}}
    """

    def __init__(self, metadata: Dict[str, Any] = None):
        """
        初始化元数据过滤器

        Args:
            metadata: 元数据过滤条件字典
                例如：{"priority": "High", "status": "Open", "project_key": "PROJ"}
        """
        super().__init__({"metadata": metadata})
        self.metadata = metadata or {}

        logger.info(f"MetadataFilter initialized with {len(self.metadata)} conditions: {self.metadata}")

    def to_chroma_where(self) -> Optional[Dict[str, Any]]:
        """
        转换为 ChromaDB where 子句格式

        Returns:
            ChromaDB where 子句字典，如果没有过滤条件则返回 None
        """
        if not self.metadata:
            return None

        conditions = []

        for key, value in self.metadata.items():
            # 如果值是列表，使用 $in 操作符
            if isinstance(value, list):
                conditions.append({key: {"$in": value}})
            # 如果值是字典（已经包含操作符）
            elif isinstance(value, dict):
                conditions.append({key: value})
            # 否则直接相等比较
            else:
                conditions.append({key: value})

        # 如果只有一个条件，直接返回
        if len(conditions) == 1:
            return conditions[0]

        # 多个条件，使用 AND 组合
        return {"$and": conditions}

    def apply(self, results: List[RetrievalResult]) -> List[RetrievalResult]:
        """
        应用过滤器到检索结果（Post-filtering）

        Args:
            results: 检索结果列表

        Returns:
            过滤后的结果列表
        """
        if not self.metadata:
            return results

        filtered_results = []
        for result in results:
            if self._match_metadata(result.metadata):
                filtered_results.append(result)

        logger.debug(
            f"MetadataFilter applied: {len(results)} -> {len(filtered_results)} results "
            f"(conditions: {self.metadata})"
        )

        return filtered_results

    def _match_metadata(self, result_metadata: Dict[str, Any]) -> bool:
        """
        检查结果元数据是否匹配过滤条件

        Args:
            result_metadata: 结果的元数据

        Returns:
            bool: True 表示匹配
        """
        for key, value in self.metadata.items():
            # 如果元数据中没有这个字段，不匹配
            if key not in result_metadata:
                return False

            result_value = result_metadata[key]

            # 如果过滤值是列表，检查结果值是否在列表中
            if isinstance(value, list):
                if result_value not in value:
                    return False

            # 如果过滤值是字典（包含操作符）
            elif isinstance(value, dict):
                if not self._match_operator(result_value, value):
                    return False

            # 否则直接比较
            else:
                if result_value != value:
                    return False

        return True

    def _match_operator(self, result_value: Any, operator_dict: Dict[str, Any]) -> bool:
        """
        检查结果值是否匹配操作符条件

        Args:
            result_value: 结果中的值
            operator_dict: 操作符字典（如 {"$in": ["High", "Medium"]}）

        Returns:
            bool: True 表示匹配
        """
        for operator, op_value in operator_dict.items():
            if operator == "$in":
                if result_value not in op_value:
                    return False
            elif operator == "$nin":
                if result_value in op_value:
                    return False
            elif operator == "$eq":
                if result_value != op_value:
                    return False
            elif operator == "$ne":
                if result_value == op_value:
                    return False
            elif operator == "$gt":
                if not (result_value > op_value):
                    return False
            elif operator == "$gte":
                if not (result_value >= op_value):
                    return False
            elif operator == "$lt":
                if not (result_value < op_value):
                    return False
            elif operator == "$lte":
                if not (result_value <= op_value):
                    return False
            else:
                logger.warning(f"Unknown operator: {operator}")
                return False

        return True

    def is_empty(self) -> bool:
        """
        检查过滤器是否为空

        Returns:
            bool: True 表示没有任何过滤条件
        """
        return not self.metadata

    def add_condition(self, key: str, value: Any) -> None:
        """
        添加过滤条件

        Args:
            key: 元数据字段名
            value: 过滤值
        """
        self.metadata[key] = value
        logger.debug(f"Added condition: {key}={value}")

    def remove_condition(self, key: str) -> None:
        """
        移除过滤条件

        Args:
            key: 元数据字段名
        """
        if key in self.metadata:
            del self.metadata[key]
            logger.debug(f"Removed condition: {key}")

    def clear(self) -> None:
        """清空所有条件"""
        self.metadata.clear()
        logger.debug("Cleared all conditions")

    def get_condition(self, key: str) -> Optional[Any]:
        """
        获取特定条件的值

        Args:
            key: 元数据字段名

        Returns:
            条件值，如果不存在则返回 None
        """
        return self.metadata.get(key)
