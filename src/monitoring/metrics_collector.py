"""
性能指标收集器

使用 psutil 收集系统资源指标和数据库连接池状态。
实现缓存机制以减少性能开销。
"""

import time
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Tuple, Any, Optional, Callable
import psutil

from src.storage.database.base import engine

logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    """系统资源指标"""
    cpu_percent: float
    memory_percent: float
    memory_available_gb: float
    memory_total_gb: float
    disk_percent: float
    disk_free_gb: float
    disk_total_gb: float
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class DatabaseMetrics:
    """数据库连接池指标"""
    pool_size: int
    pool_checked_out: int
    pool_overflow: int
    pool_checked_in: int
    pool_usage_percent: float
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


class MetricsCollector:
    """指标收集器（带缓存）"""

    # 类级别缓存
    _cache: Dict[str, Tuple[Any, float]] = {}
    _cache_ttl: int = 5  # 5 秒缓存

    @classmethod
    def get_system_metrics(cls) -> SystemMetrics:
        """
        获取系统资源指标（带缓存）

        Returns:
            SystemMetrics: 系统指标数据
        """
        return cls._get_cached("system_metrics", cls._fetch_system_metrics)

    @classmethod
    def get_database_metrics(cls) -> DatabaseMetrics:
        """
        获取数据库连接池指标（带缓存）

        Returns:
            DatabaseMetrics: 数据库指标数据
        """
        return cls._get_cached("database_metrics", cls._fetch_database_metrics)

    @classmethod
    def _get_cached(cls, cache_key: str, fetch_func: Callable) -> Any:
        """
        通用缓存逻辑

        Args:
            cache_key: 缓存键
            fetch_func: 数据获取函数

        Returns:
            Any: 缓存或新获取的数据
        """
        now = time.time()

        # 检查缓存是否存在且未过期
        if cache_key in cls._cache:
            cached_data, cached_time = cls._cache[cache_key]
            if now - cached_time < cls._cache_ttl:
                logger.debug(f"Using cached {cache_key} (age: {now - cached_time:.1f}s)")
                return cached_data

        # 缓存过期或不存在，重新获取
        logger.debug(f"Fetching fresh {cache_key}")
        fresh_data = fetch_func()
        cls._cache[cache_key] = (fresh_data, now)
        return fresh_data

    @staticmethod
    def _fetch_system_metrics() -> SystemMetrics:
        """
        实际获取系统指标（无缓存）

        Returns:
            SystemMetrics: 系统指标数据
        """
        try:
            # CPU 使用率 (需要 1 秒采样)
            cpu_percent = psutil.cpu_percent(interval=1)

            # 内存信息
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_gb = memory.available / (1024 ** 3)
            memory_total_gb = memory.total / (1024 ** 3)

            # 磁盘信息
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_free_gb = disk.free / (1024 ** 3)
            disk_total_gb = disk.total / (1024 ** 3)

            return SystemMetrics(
                cpu_percent=round(cpu_percent, 2),
                memory_percent=round(memory_percent, 2),
                memory_available_gb=round(memory_available_gb, 2),
                memory_total_gb=round(memory_total_gb, 2),
                disk_percent=round(disk_percent, 2),
                disk_free_gb=round(disk_free_gb, 2),
                disk_total_gb=round(disk_total_gb, 2),
                timestamp=datetime.now().isoformat()
            )
        except Exception as e:
            logger.error(f"Failed to fetch system metrics: {e}")
            # 返回默认值
            return SystemMetrics(
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_available_gb=0.0,
                memory_total_gb=0.0,
                disk_percent=0.0,
                disk_free_gb=0.0,
                disk_total_gb=0.0,
                timestamp=datetime.now().isoformat()
            )

    @staticmethod
    def _fetch_database_metrics() -> DatabaseMetrics:
        """
        实际获取数据库连接池指标（无缓存）

        Returns:
            DatabaseMetrics: 数据库指标数据
        """
        try:
            pool = engine.pool

            # 获取连接池状态
            pool_size = pool.size()
            pool_checked_out = pool.checkedout()
            pool_overflow_raw = pool.overflow()
            # overflow() 返回负值表示没有溢出，取 max(0, overflow) 确保非负
            pool_overflow = max(0, pool_overflow_raw)
            pool_checked_in = pool_size - pool_checked_out

            # 计算使用率
            pool_usage_percent = 0.0
            if pool_size > 0:
                pool_usage_percent = (pool_checked_out / pool_size) * 100

            return DatabaseMetrics(
                pool_size=pool_size,
                pool_checked_out=pool_checked_out,
                pool_overflow=pool_overflow,
                pool_checked_in=pool_checked_in,
                pool_usage_percent=round(pool_usage_percent, 2),
                timestamp=datetime.now().isoformat()
            )
        except Exception as e:
            logger.error(f"Failed to fetch database metrics: {e}")
            # 返回默认值
            return DatabaseMetrics(
                pool_size=0,
                pool_checked_out=0,
                pool_overflow=0,
                pool_checked_in=0,
                pool_usage_percent=0.0,
                timestamp=datetime.now().isoformat()
            )

    @classmethod
    def clear_cache(cls):
        """清空缓存（用于测试）"""
        cls._cache.clear()
        logger.debug("Metrics cache cleared")


# 全局单例
_collector_instance: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """
    获取指标收集器单例

    Returns:
        MetricsCollector: 指标收集器实例
    """
    global _collector_instance
    if _collector_instance is None:
        _collector_instance = MetricsCollector()
    return _collector_instance
