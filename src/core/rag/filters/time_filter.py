"""
Time Range Filter
时间范围过滤器：按时间范围过滤检索结果
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from .base import BaseFilter
from ..models import RetrievalResult, TimeRange

logger = logging.getLogger(__name__)


class TimeRangeFilter(BaseFilter):
    """
    时间范围过滤器

    支持的时间范围：
    - 预设范围：1d（最近1天）、7d（最近7天）、30d（最近30天）、90d（最近90天）
    - 自定义范围：指定 start 和 end 时间
    """

    PRESET_DAYS = {
        "1d": 1,
        "7d": 7,
        "30d": 30,
        "90d": 90
    }

    def __init__(
        self,
        time_range: TimeRange = None,
        field_name: str = "created_at"
    ):
        """
        初始化时间范围过滤器

        Args:
            time_range: TimeRange 对象
            field_name: 要过滤的时间字段名（默认：created_at）
        """
        super().__init__({"time_range": time_range, "field_name": field_name})
        self.time_range = time_range
        self.field_name = field_name

        if time_range:
            logger.info(
                f"TimeRangeFilter initialized: preset={time_range.preset}, "
                f"start={time_range.start}, end={time_range.end}, field={field_name}"
            )

    def to_chroma_where(self) -> Optional[Dict[str, Any]]:
        """
        转换为 ChromaDB where 子句格式

        Returns:
            ChromaDB where 子句字典，如果没有过滤条件则返回 None
        """
        if not self.time_range:
            return None

        return self.time_range.to_filter_dict(self.field_name)

    def apply(self, results: List[RetrievalResult]) -> List[RetrievalResult]:
        """
        应用过滤器到检索结果（Post-filtering）

        Args:
            results: 检索结果列表

        Returns:
            过滤后的结果列表
        """
        if not self.time_range:
            return results

        # 计算实际的时间范围
        start_time, end_time = self._get_time_bounds()

        if start_time is None and end_time is None:
            return results

        filtered_results = []
        for result in results:
            # 从元数据获取时间字段
            time_str = result.metadata.get(self.field_name)
            if not time_str:
                # 如果没有时间字段，根据配置决定是否包含
                continue

            try:
                # 解析时间字符串
                result_time = self._parse_time(time_str)

                # 检查是否在范围内
                if start_time and result_time < start_time:
                    continue
                if end_time and result_time > end_time:
                    continue

                filtered_results.append(result)

            except Exception as e:
                logger.warning(f"Failed to parse time field '{self.field_name}': {time_str}, error: {e}")
                continue

        logger.debug(
            f"TimeRangeFilter applied: {len(results)} -> {len(filtered_results)} results "
            f"(start={start_time}, end={end_time})"
        )

        return filtered_results

    def _get_time_bounds(self) -> tuple[Optional[datetime], Optional[datetime]]:
        """
        获取时间范围的边界

        Returns:
            (start_time, end_time) 元组
        """
        if not self.time_range:
            return None, None

        # 如果使用预设时间范围
        if self.time_range.preset and self.time_range.preset in self.PRESET_DAYS:
            days = self.PRESET_DAYS[self.time_range.preset]
            start_time = datetime.now() - timedelta(days=days)
            end_time = None
            return start_time, end_time

        # 使用自定义时间范围
        return self.time_range.start, self.time_range.end

    def _parse_time(self, time_str: Any) -> datetime:
        """
        解析时间字符串

        Args:
            time_str: 时间字符串或 datetime 对象

        Returns:
            datetime 对象

        Raises:
            ValueError: 如果无法解析时间
        """
        if isinstance(time_str, datetime):
            return time_str

        if isinstance(time_str, str):
            # 尝试多种格式
            for fmt in [
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d",
            ]:
                try:
                    return datetime.strptime(time_str, fmt)
                except ValueError:
                    continue

            # 尝试 ISO 格式
            try:
                return datetime.fromisoformat(time_str.replace("Z", "+00:00"))
            except ValueError:
                pass

        raise ValueError(f"Unable to parse time: {time_str}")

    def is_empty(self) -> bool:
        """
        检查过滤器是否为空

        Returns:
            bool: True 表示没有任何过滤条件
        """
        return self.time_range is None

    def set_preset(self, preset: str) -> None:
        """
        设置预设时间范围

        Args:
            preset: 预设类型（1d/7d/30d/90d）
        """
        if preset not in self.PRESET_DAYS:
            logger.warning(f"Invalid preset: {preset}. Valid presets: {list(self.PRESET_DAYS.keys())}")
            return

        self.time_range = TimeRange(preset=preset)
        logger.debug(f"Set preset time range: {preset}")

    def set_custom_range(self, start: datetime = None, end: datetime = None) -> None:
        """
        设置自定义时间范围

        Args:
            start: 开始时间
            end: 结束时间
        """
        self.time_range = TimeRange(start=start, end=end, preset="custom")
        logger.debug(f"Set custom time range: start={start}, end={end}")

    def clear(self) -> None:
        """清空时间范围"""
        self.time_range = None
        logger.debug("Cleared time range")
