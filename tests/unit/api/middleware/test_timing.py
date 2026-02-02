"""
测试性能监控中间件
"""

import pytest
import asyncio
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from httpx import AsyncClient

from src.api.middleware.timing import (
    TimingMiddleware,
    RequestRecord,
    APIStatistics
)


class TestTimingMiddleware:
    """测试 TimingMiddleware 类"""

    @pytest.fixture
    def app(self):
        """创建测试用 FastAPI 应用"""
        app = FastAPI()

        # 添加中间件
        middleware = TimingMiddleware(app, max_records=10)
        app.add_middleware(TimingMiddleware, max_records=10)

        # 添加测试路由
        @app.get("/test")
        async def test_endpoint():
            await asyncio.sleep(0.01)  # 模拟处理时间
            return {"message": "test"}

        @app.get("/slow")
        async def slow_endpoint():
            await asyncio.sleep(0.1)  # 慢端点
            return {"message": "slow"}

        @app.get("/health")
        async def health():
            return {"status": "ok"}

        return app, middleware

    @pytest.mark.asyncio
    async def test_middleware_records_request(self, app):
        """测试中间件记录请求"""
        app_instance, middleware = app

        async with AsyncClient(app=app_instance, base_url="http://test") as client:
            response = await client.get("/test")
            assert response.status_code == 200

        # 验证请求被记录
        assert len(middleware.records) > 0

        # 验证记录内容
        record = list(middleware.records)[-1]
        assert record.path == "/test"
        assert record.method == "GET"
        assert record.status_code == 200
        assert record.duration_ms > 0

    @pytest.mark.asyncio
    async def test_middleware_skips_health_endpoint(self, app):
        """测试中间件跳过健康检查端点"""
        app_instance, middleware = app

        # 清空记录
        middleware.clear_records()

        async with AsyncClient(app=app_instance, base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200

        # 验证没有记录健康检查请求
        assert len(middleware.records) == 0

    @pytest.mark.asyncio
    async def test_get_statistics(self, app):
        """测试获取统计信息"""
        app_instance, middleware = app

        # 清空记录
        middleware.clear_records()

        # 发送多个请求
        async with AsyncClient(app=app_instance, base_url="http://test") as client:
            for _ in range(5):
                await client.get("/test")
            for _ in range(3):
                await client.get("/slow")

        # 获取统计信息
        stats = middleware.get_statistics()

        # 验证统计信息
        assert isinstance(stats, APIStatistics)
        assert stats.total_requests == 8  # 5 + 3
        assert stats.avg_response_time_ms > 0
        assert stats.p50_response_time_ms > 0
        assert stats.p95_response_time_ms > 0
        assert stats.p99_response_time_ms > 0

        # 验证百分位数递增
        assert stats.p50_response_time_ms <= stats.p95_response_time_ms
        assert stats.p95_response_time_ms <= stats.p99_response_time_ms

    @pytest.mark.asyncio
    async def test_slowest_endpoints(self, app):
        """测试最慢端点统计"""
        app_instance, middleware = app

        # 清空记录
        middleware.clear_records()

        # 发送不同端点的请求
        async with AsyncClient(app=app_instance, base_url="http://test") as client:
            for _ in range(3):
                await client.get("/test")
            for _ in range(2):
                await client.get("/slow")

        # 获取统计信息
        stats = middleware.get_statistics()

        # 验证最慢端点列表
        assert len(stats.slowest_endpoints) > 0

        # /slow 端点应该在最慢列表中排名靠前
        slowest = stats.slowest_endpoints[0]
        assert "/slow" in slowest["endpoint"]
        assert slowest["count"] == 2

    @pytest.mark.asyncio
    async def test_sliding_window(self, app):
        """测试滑动窗口"""
        app_instance, middleware = app

        # 清空记录
        middleware.clear_records()

        # 发送超过最大记录数的请求
        async with AsyncClient(app=app_instance, base_url="http://test") as client:
            for i in range(15):  # max_records=10
                await client.get("/test")

        # 验证只保留最后 10 条记录
        assert len(middleware.records) == 10

    @pytest.mark.asyncio
    async def test_empty_records(self, app):
        """测试空记录情况"""
        app_instance, middleware = app

        # 清空记录
        middleware.clear_records()

        # 获取统计信息
        stats = middleware.get_statistics()

        # 验证默认值
        assert stats.total_requests == 0
        assert stats.avg_response_time_ms == 0.0
        assert stats.p50_response_time_ms == 0.0
        assert stats.p95_response_time_ms == 0.0
        assert stats.p99_response_time_ms == 0.0
        assert len(stats.slowest_endpoints) == 0
        assert stats.requests_per_minute == 0.0

    def test_clear_records(self, app):
        """测试清空记录"""
        app_instance, middleware = app

        # 添加一些测试记录
        for i in range(5):
            middleware.records.append(
                RequestRecord(
                    path="/test",
                    method="GET",
                    status_code=200,
                    duration_ms=10.0,
                    timestamp=datetime.now().isoformat()
                )
            )

        # 验证有记录
        assert len(middleware.records) > 0

        # 清空记录
        middleware.clear_records()

        # 验证已清空
        assert len(middleware.records) == 0


class TestRequestRecord:
    """测试 RequestRecord 数据类"""

    def test_request_record_creation(self):
        """测试创建 RequestRecord 实例"""
        record = RequestRecord(
            path="/test",
            method="GET",
            status_code=200,
            duration_ms=15.5,
            timestamp="2024-01-01T00:00:00"
        )

        assert record.path == "/test"
        assert record.method == "GET"
        assert record.status_code == 200
        assert record.duration_ms == 15.5
        assert record.timestamp == "2024-01-01T00:00:00"

    def test_to_dict(self):
        """测试 to_dict 方法"""
        record = RequestRecord(
            path="/test",
            method="GET",
            status_code=200,
            duration_ms=15.5,
            timestamp="2024-01-01T00:00:00"
        )

        record_dict = record.to_dict()

        assert "path" in record_dict
        assert "method" in record_dict
        assert "status_code" in record_dict
        assert "duration_ms" in record_dict
        assert "timestamp" in record_dict


class TestAPIStatistics:
    """测试 APIStatistics 数据类"""

    def test_api_statistics_creation(self):
        """测试创建 APIStatistics 实例"""
        stats = APIStatistics(
            total_requests=100,
            avg_response_time_ms=50.0,
            p50_response_time_ms=45.0,
            p95_response_time_ms=95.0,
            p99_response_time_ms=150.0,
            slowest_endpoints=[],
            requests_per_minute=10.0,
            timestamp="2024-01-01T00:00:00"
        )

        assert stats.total_requests == 100
        assert stats.avg_response_time_ms == 50.0
        assert stats.p95_response_time_ms == 95.0
