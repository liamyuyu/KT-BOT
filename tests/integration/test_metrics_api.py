"""
测试监控指标 API 端点集成
"""

import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

from src.api.main import create_fastapi_app
from src.api.middleware.timing import set_timing_middleware, TimingMiddleware


@pytest.fixture
async def app():
    """创建测试用 FastAPI 应用"""
    app = create_fastapi_app()
    return app


@pytest.mark.asyncio
async def test_get_system_metrics(app):
    """测试系统指标 API"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/metrics/system")

        # 验证响应状态
        assert response.status_code == 200

        # 验证响应结构
        data = response.json()
        assert "success" in data
        assert data["success"] is True
        assert "data" in data

        # 验证数据字段
        metrics = data["data"]
        assert "cpu_percent" in metrics
        assert "memory_percent" in metrics
        assert "memory_available_gb" in metrics
        assert "memory_total_gb" in metrics
        assert "disk_percent" in metrics
        assert "disk_free_gb" in metrics
        assert "disk_total_gb" in metrics
        assert "timestamp" in metrics

        # 验证数据合理性
        assert 0 <= metrics["cpu_percent"] <= 100
        assert 0 <= metrics["memory_percent"] <= 100


@pytest.mark.asyncio
async def test_get_database_metrics(app):
    """测试数据库指标 API"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/metrics/database")

        # 验证响应状态
        assert response.status_code == 200

        # 验证响应结构
        data = response.json()
        assert "success" in data
        assert data["success"] is True
        assert "data" in data

        # 验证数据字段
        metrics = data["data"]
        assert "pool_size" in metrics
        assert "pool_checked_out" in metrics
        assert "pool_overflow" in metrics
        assert "pool_checked_in" in metrics
        assert "pool_usage_percent" in metrics
        assert "timestamp" in metrics

        # 验证数据合理性
        assert metrics["pool_size"] >= 0
        assert 0 <= metrics["pool_usage_percent"] <= 100


@pytest.mark.asyncio
async def test_get_api_metrics(app):
    """测试 API 指标 API"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 先发送几个请求生成数据
        for _ in range(5):
            await client.get("/api/v1/health")

        # 获取 API 指标
        response = await client.get("/api/v1/metrics/api")

        # 验证响应状态
        assert response.status_code == 200

        # 验证响应结构
        data = response.json()
        assert "success" in data
        assert data["success"] is True
        assert "data" in data

        # 验证数据字段
        metrics = data["data"]
        assert "total_requests" in metrics
        assert "avg_response_time_ms" in metrics
        assert "p50_response_time_ms" in metrics
        assert "p95_response_time_ms" in metrics
        assert "p99_response_time_ms" in metrics
        assert "slowest_endpoints" in metrics
        assert "requests_per_minute" in metrics
        assert "timestamp" in metrics

        # 验证数据合理性
        assert metrics["total_requests"] >= 0
        assert metrics["avg_response_time_ms"] >= 0


@pytest.mark.asyncio
async def test_get_retrieval_metrics(app):
    """测试检索指标 API"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/metrics/retrieval")

        # 验证响应状态
        assert response.status_code == 200

        # 验证响应结构
        data = response.json()
        assert "success" in data
        assert data["success"] is True
        assert "data" in data

        # 验证数据字段
        metrics = data["data"]
        assert "total_searches" in metrics
        assert "avg_search_time_ms" in metrics
        assert "p95_search_time_ms" in metrics
        assert "timestamp" in metrics


@pytest.mark.asyncio
async def test_get_all_metrics(app):
    """测试获取所有指标"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/metrics/all")

        # 验证响应状态
        assert response.status_code == 200

        # 验证响应结构
        data = response.json()
        assert "success" in data
        assert data["success"] is True
        assert "data" in data

        # 验证包含所有子指标
        all_metrics = data["data"]
        assert "system" in all_metrics
        assert "database" in all_metrics
        assert "api" in all_metrics
        assert "retrieval" in all_metrics

        # 验证每个子指标的关键字段
        assert "cpu_percent" in all_metrics["system"]
        assert "pool_size" in all_metrics["database"]
        assert "total_requests" in all_metrics["api"]
        assert "total_searches" in all_metrics["retrieval"]


@pytest.mark.asyncio
async def test_metrics_api_error_handling(app):
    """测试 API 错误处理"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 测试不存在的端点
        response = await client.get("/api/v1/metrics/nonexistent")

        # 应该返回 404
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_concurrent_metrics_requests(app):
    """测试并发请求指标"""
    import asyncio

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 并发请求所有指标端点
        tasks = [
            client.get("/api/v1/metrics/system"),
            client.get("/api/v1/metrics/database"),
            client.get("/api/v1/metrics/api"),
            client.get("/api/v1/metrics/retrieval"),
            client.get("/api/v1/metrics/all"),
        ]

        responses = await asyncio.gather(*tasks)

        # 验证所有请求都成功
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
