"""
Composite Filter
组合过滤器：组合多个过滤器，支持 AND/OR 逻辑
"""

import logging
from typing import Dict, Any, Optional, List, Literal

from .base import BaseFilter
from ..models import RetrievalResult

logger = logging.getLogger(__name__)


class CompositeFilter(BaseFilter):
    """
    组合过滤器

    支持将多个过滤器组合在一起：
    - AND 逻辑：所有过滤器都必须匹配
    - OR 逻辑：任一过滤器匹配即可
    """

    def __init__(
        self,
        filters: List[BaseFilter],
        logic: Literal["AND", "OR"] = "AND"
    ):
        """
        初始化组合过滤器

        Args:
            filters: 要组合的过滤器列表
            logic: 组合逻辑（AND/OR）
        """
        super().__init__({"filters": filters, "logic": logic})
        self.filters = filters or []
        self.logic = logic.upper()

        if self.logic not in ["AND", "OR"]:
            raise ValueError(f"Invalid logic: {logic}. Must be 'AND' or 'OR'")

        logger.info(f"CompositeFilter initialized with {len(self.filters)} filters (logic={self.logic})")

    def to_chroma_where(self) -> Optional[Dict[str, Any]]:
        """
        转换为 ChromaDB where 子句格式

        Returns:
            ChromaDB where 子句字典，如果没有过滤条件则返回 None
        """
        if not self.filters:
            return None

        # 收集所有非空的 where 子句
        where_clauses = []
        for filter_obj in self.filters:
            where_clause = filter_obj.to_chroma_where()
            if where_clause:
                where_clauses.append(where_clause)

        # 如果没有任何条件，返回 None
        if not where_clauses:
            return None

        # 如果只有一个条件，直接返回
        if len(where_clauses) == 1:
            return where_clauses[0]

        # 多个条件，根据 logic 组合
        if self.logic == "OR":
            return {"$or": where_clauses}
        else:  # AND
            return {"$and": where_clauses}

    def apply(self, results: List[RetrievalResult]) -> List[RetrievalResult]:
        """
        应用过滤器到检索结果（Post-filtering）

        Args:
            results: 检索结果列表

        Returns:
            过滤后的结果列表
        """
        if not self.filters:
            return results

        # 根据逻辑应用过滤器
        if self.logic == "AND":
            return self._apply_and(results)
        else:  # OR
            return self._apply_or(results)

    def _apply_and(self, results: List[RetrievalResult]) -> List[RetrievalResult]:
        """
        应用 AND 逻辑：依次应用所有过滤器

        Args:
            results: 检索结果列表

        Returns:
            过滤后的结果列表
        """
        filtered_results = results

        for filter_obj in self.filters:
            filtered_results = filter_obj.apply(filtered_results)
            # 如果已经没有结果了，可以提前退出
            if not filtered_results:
                break

        logger.debug(
            f"CompositeFilter (AND) applied: {len(results)} -> {len(filtered_results)} results "
            f"({len(self.filters)} filters)"
        )

        return filtered_results

    def _apply_or(self, results: List[RetrievalResult]) -> List[RetrievalResult]:
        """
        应用 OR 逻辑：合并所有过滤器的结果（去重）

        Args:
            results: 检索结果列表

        Returns:
            过滤后的结果列表
        """
        # 用 set 存储已匹配的 chunk_id 以去重
        matched_chunk_ids = set()
        filtered_results = []

        for filter_obj in self.filters:
            filter_results = filter_obj.apply(results)

            for result in filter_results:
                if result.chunk_id not in matched_chunk_ids:
                    matched_chunk_ids.add(result.chunk_id)
                    filtered_results.append(result)

        # 按原始顺序排序（保持相关性排序）
        chunk_id_to_index = {r.chunk_id: i for i, r in enumerate(results)}
        filtered_results.sort(key=lambda r: chunk_id_to_index.get(r.chunk_id, float('inf')))

        logger.debug(
            f"CompositeFilter (OR) applied: {len(results)} -> {len(filtered_results)} results "
            f"({len(self.filters)} filters)"
        )

        return filtered_results

    def is_empty(self) -> bool:
        """
        检查过滤器是否为空

        Returns:
            bool: True 表示没有任何过滤条件
        """
        # 如果没有子过滤器，或所有子过滤器都为空，则为空
        return not self.filters or all(f.is_empty() for f in self.filters)

    def add_filter(self, filter_obj: BaseFilter) -> None:
        """
        添加过滤器

        Args:
            filter_obj: 要添加的过滤器
        """
        if filter_obj not in self.filters:
            self.filters.append(filter_obj)
            logger.debug(f"Added filter: {filter_obj}")

    def remove_filter(self, filter_obj: BaseFilter) -> None:
        """
        移除过滤器

        Args:
            filter_obj: 要移除的过滤器
        """
        if filter_obj in self.filters:
            self.filters.remove(filter_obj)
            logger.debug(f"Removed filter: {filter_obj}")

    def clear(self) -> None:
        """清空所有过滤器"""
        self.filters.clear()
        logger.debug("Cleared all filters")

    def get_filter_count(self) -> int:
        """
        获取过滤器数量

        Returns:
            int: 过滤器数量
        """
        return len(self.filters)

    def set_logic(self, logic: Literal["AND", "OR"]) -> None:
        """
        设置组合逻辑

        Args:
            logic: 组合逻辑（AND/OR）

        Raises:
            ValueError: 如果逻辑无效
        """
        logic = logic.upper()
        if logic not in ["AND", "OR"]:
            raise ValueError(f"Invalid logic: {logic}. Must be 'AND' or 'OR'")

        self.logic = logic
        logger.debug(f"Set logic: {logic}")


def create_filter_from_config(config: Dict[str, Any]) -> Optional[BaseFilter]:
    """
    从配置字典创建过滤器

    Args:
        config: 过滤配置字典，格式如：
            {
                "sources": ["jira", "confluence"],
                "time_range": {"preset": "7d"},
                "metadata": {"priority": "High"},
                "logic": "AND"
            }

    Returns:
        BaseFilter 实例，如果配置为空则返回 None
    """
    from .source_filter import SourceFilter
    from .time_filter import TimeRangeFilter
    from .metadata_filter import MetadataFilter
    from ..models import TimeRange

    filters = []

    # 来源过滤
    if config.get("sources"):
        filters.append(SourceFilter(config["sources"]))

    # 时间范围过滤
    if config.get("time_range"):
        time_range_dict = config["time_range"]
        time_range = TimeRange(**time_range_dict)
        filters.append(TimeRangeFilter(time_range))

    # 元数据过滤
    if config.get("metadata"):
        filters.append(MetadataFilter(config["metadata"]))

    # 如果没有任何过滤器，返回 None
    if not filters:
        return None

    # 如果只有一个过滤器，直接返回
    if len(filters) == 1:
        return filters[0]

    # 多个过滤器，创建组合过滤器
    logic = config.get("logic", "AND")
    return CompositeFilter(filters, logic)
