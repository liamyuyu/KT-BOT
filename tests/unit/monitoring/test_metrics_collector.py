"""
测试指标收集器
"""

import time
import pytest
from src.monitoring.metrics_collector import (
    MetricsCollector,
    SystemMetrics,
    DatabaseMetrics,
    get_metrics_collector
)


class TestMetricsCollector:
    """测试 MetricsCollector 类"""

    def setup_method(self):
        """每个测试前清空缓存"""
        MetricsCollector.clear_cache()

    def test_get_system_metrics(self):
        """测试系统指标采集"""
        collector = get_metrics_collector()
        metrics = collector.get_system_metrics()

        # 验证数据类型
        assert isinstance(metrics, SystemMetrics)

        # 验证字段值合理性
        assert 0 <= metrics.cpu_percent <= 100
        assert 0 <= metrics.memory_percent <= 100
        assert metrics.memory_total_gb > 0
        assert metrics.memory_available_gb >= 0
        assert metrics.memory_available_gb <= metrics.memory_total_gb
        assert 0 <= metrics.disk_percent <= 100
        assert metrics.disk_total_gb > 0
        assert metrics.disk_free_gb >= 0
        assert metrics.disk_free_gb <= metrics.disk_total_gb

        # 验证时间戳格式
        assert metrics.timestamp is not None

    def test_get_database_metrics(self):
        """测试数据库指标采集"""
        collector = get_metrics_collector()
        metrics = collector.get_database_metrics()

        # 验证数据类型
        assert isinstance(metrics, DatabaseMetrics)

        # 验证字段值合理性
        assert metrics.pool_size >= 0
        assert metrics.pool_checked_out >= 0
        assert metrics.pool_overflow >= 0
        assert metrics.pool_checked_in >= 0
        assert 0 <= metrics.pool_usage_percent <= 100

        # 验证连接数逻辑
        assert metrics.pool_checked_out + metrics.pool_checked_in <= metrics.pool_size + metrics.pool_overflow

        # 验证时间戳格式
        assert metrics.timestamp is not None

    def test_cache_mechanism(self):
        """测试缓存机制"""
        collector = get_metrics_collector()

        # 第一次调用（无缓存）
        start1 = time.time()
        metrics1 = collector.get_system_metrics()
        duration1 = time.time() - start1

        # 立即第二次调用（应该从缓存读取）
        start2 = time.time()
        metrics2 = collector.get_system_metrics()
        duration2 = time.time() - start2

        # 验证返回相同的数据
        assert metrics1.timestamp == metrics2.timestamp

        # 验证缓存快很多（至少快 5 倍，因为 CPU 采集需要 1 秒）
        assert duration2 < duration1 * 0.2

    def test_cache_expiration(self):
        """测试缓存过期"""
        # 设置更短的 TTL 用于测试
        original_ttl = MetricsCollector._cache_ttl
        MetricsCollector._cache_ttl = 1  # 1 秒 TTL

        try:
            collector = get_metrics_collector()

            # 第一次调用
            metrics1 = collector.get_system_metrics()

            # 等待缓存过期
            time.sleep(1.5)

            # 第二次调用（缓存应该已过期）
            metrics2 = collector.get_system_metrics()

            # 时间戳应该不同
            assert metrics1.timestamp != metrics2.timestamp

        finally:
            # 恢复原始 TTL
            MetricsCollector._cache_ttl = original_ttl

    def test_clear_cache(self):
        """测试清空缓存"""
        collector = get_metrics_collector()

        # 填充缓存
        collector.get_system_metrics()
        collector.get_database_metrics()

        # 验证缓存中有数据
        assert len(MetricsCollector._cache) > 0

        # 清空缓存
        MetricsCollector.clear_cache()

        # 验证缓存已清空
        assert len(MetricsCollector._cache) == 0

    def test_to_dict(self):
        """测试 to_dict 方法"""
        collector = get_metrics_collector()
        metrics = collector.get_system_metrics()

        # 转换为字典
        metrics_dict = metrics.to_dict()

        # 验证字典包含所有字段
        assert "cpu_percent" in metrics_dict
        assert "memory_percent" in metrics_dict
        assert "memory_available_gb" in metrics_dict
        assert "memory_total_gb" in metrics_dict
        assert "disk_percent" in metrics_dict
        assert "disk_free_gb" in metrics_dict
        assert "disk_total_gb" in metrics_dict
        assert "timestamp" in metrics_dict

    def test_singleton_pattern(self):
        """测试单例模式"""
        collector1 = get_metrics_collector()
        collector2 = get_metrics_collector()

        # 应该返回同一个实例
        assert collector1 is collector2


class TestSystemMetrics:
    """测试 SystemMetrics 数据类"""

    def test_system_metrics_creation(self):
        """测试创建 SystemMetrics 实例"""
        metrics = SystemMetrics(
            cpu_percent=45.5,
            memory_percent=60.2,
            memory_available_gb=8.5,
            memory_total_gb=16.0,
            disk_percent=70.0,
            disk_free_gb=50.0,
            disk_total_gb=100.0,
            timestamp="2024-01-01T00:00:00"
        )

        assert metrics.cpu_percent == 45.5
        assert metrics.memory_percent == 60.2
        assert metrics.timestamp == "2024-01-01T00:00:00"


class TestDatabaseMetrics:
    """测试 DatabaseMetrics 数据类"""

    def test_database_metrics_creation(self):
        """测试创建 DatabaseMetrics 实例"""
        metrics = DatabaseMetrics(
            pool_size=5,
            pool_checked_out=3,
            pool_overflow=0,
            pool_checked_in=2,
            pool_usage_percent=60.0,
            timestamp="2024-01-01T00:00:00"
        )

        assert metrics.pool_size == 5
        assert metrics.pool_checked_out == 3
        assert metrics.pool_usage_percent == 60.0
