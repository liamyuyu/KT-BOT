"""
API 性能监控中间件

记录每个请求的耗时、端点、状态码，计算统计信息。
使用滑动窗口存储最近 1000 条请求记录。
"""

import time
import logging
from collections import deque
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Deque, List, Dict, Any, Optional
import numpy as np
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


@dataclass
class RequestRecord:
    """请求记录"""
    path: str
    method: str
    status_code: int
    duration_ms: float
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class APIStatistics:
    """API 性能统计"""
    total_requests: int
    avg_response_time_ms: float
    p50_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    slowest_endpoints: List[Dict[str, Any]]
    requests_per_minute: float
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


class TimingMiddleware(BaseHTTPMiddleware):
    """
    性能监控中间件

    记录所有 API 请求的耗时和状态，计算统计信息。
    使用固定大小的滑动窗口避免内存泄漏。
    """

    # Class-level storage shared across all instances
    _shared_records: Deque[RequestRecord] = deque(maxlen=1000)
    _max_records: int = 1000

    def __init__(self, app, max_records: int = 1000):
        """
        初始化中间件

        Args:
            app: FastAPI 应用实例
            max_records: 最大记录数（滑动窗口大小）
        """
        super().__init__(app)
        # Update class-level max_records if different
        if max_records != TimingMiddleware._max_records:
            TimingMiddleware._max_records = max_records
            TimingMiddleware._shared_records = deque(maxlen=max_records)
        self.max_records = max_records
        logger.info(f"TimingMiddleware initialized with max_records={max_records}")

    @property
    def records(self) -> Deque[RequestRecord]:
        """Access shared records"""
        return TimingMiddleware._shared_records

    async def dispatch(self, request: Request, call_next):
        """
        处理请求并记录耗时

        Args:
            request: HTTP 请求
            call_next: 下一个中间件或路由处理器

        Returns:
            Response: HTTP 响应
        """
        # 跳过健康检查和指标端点（避免自循环）
        skip_paths = {"/health", "/metrics", "/api/v1/metrics/system",
                      "/api/v1/metrics/database", "/api/v1/metrics/api",
                      "/api/v1/metrics/retrieval", "/api/v1/metrics/all"}

        if request.url.path in skip_paths:
            return await call_next(request)

        # 记录开始时间
        start_time = time.time()

        # 处理请求
        response = await call_next(request)

        # 计算耗时
        duration_ms = (time.time() - start_time) * 1000

        # 记录请求
        record = RequestRecord(
            path=request.url.path,
            method=request.method,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
            timestamp=datetime.now().isoformat()
        )
        self.records.append(record)

        logger.debug(f"{request.method} {request.url.path} - {response.status_code} - {duration_ms:.2f}ms")

        return response

    def get_statistics(self) -> APIStatistics:
        """
        计算 API 性能统计

        Returns:
            APIStatistics: 统计信息
        """
        if not self.records:
            # 无请求记录，返回默认值
            return APIStatistics(
                total_requests=0,
                avg_response_time_ms=0.0,
                p50_response_time_ms=0.0,
                p95_response_time_ms=0.0,
                p99_response_time_ms=0.0,
                slowest_endpoints=[],
                requests_per_minute=0.0,
                timestamp=datetime.now().isoformat()
            )

        # 提取所有耗时
        durations = [record.duration_ms for record in self.records]

        # 计算统计值
        avg_response_time = float(np.mean(durations))
        p50_response_time = float(np.percentile(durations, 50))
        p95_response_time = float(np.percentile(durations, 95))
        p99_response_time = float(np.percentile(durations, 99))

        # 计算最慢端点（按端点分组）
        endpoint_stats: Dict[str, Dict[str, Any]] = {}
        for record in self.records:
            endpoint = f"{record.method} {record.path}"
            if endpoint not in endpoint_stats:
                endpoint_stats[endpoint] = {
                    "endpoint": endpoint,
                    "count": 0,
                    "total_duration_ms": 0.0,
                    "avg_duration_ms": 0.0,
                    "max_duration_ms": 0.0
                }

            endpoint_stats[endpoint]["count"] += 1
            endpoint_stats[endpoint]["total_duration_ms"] += record.duration_ms
            endpoint_stats[endpoint]["max_duration_ms"] = max(
                endpoint_stats[endpoint]["max_duration_ms"],
                record.duration_ms
            )

        # 计算每个端点的平均耗时
        for stats in endpoint_stats.values():
            stats["avg_duration_ms"] = round(
                stats["total_duration_ms"] / stats["count"], 2
            )

        # 按平均耗时排序，取前 10
        slowest_endpoints = sorted(
            endpoint_stats.values(),
            key=lambda x: x["avg_duration_ms"],
            reverse=True
        )[:10]

        # 计算请求速率（请求/分钟）
        requests_per_minute = 0.0
        if len(self.records) >= 2:
            # 使用第一条和最后一条记录计算时间跨度
            first_timestamp = datetime.fromisoformat(self.records[0].timestamp)
            last_timestamp = datetime.fromisoformat(self.records[-1].timestamp)
            time_span_minutes = (last_timestamp - first_timestamp).total_seconds() / 60.0

            if time_span_minutes > 0:
                requests_per_minute = len(self.records) / time_span_minutes

        return APIStatistics(
            total_requests=len(self.records),
            avg_response_time_ms=round(avg_response_time, 2),
            p50_response_time_ms=round(p50_response_time, 2),
            p95_response_time_ms=round(p95_response_time, 2),
            p99_response_time_ms=round(p99_response_time, 2),
            slowest_endpoints=slowest_endpoints,
            requests_per_minute=round(requests_per_minute, 2),
            timestamp=datetime.now().isoformat()
        )

    def clear_records(self):
        """清空所有记录（用于测试）"""
        self.records.clear()
        logger.info("Timing records cleared")


# 全局中间件实例（在 main.py 中初始化）
timing_middleware: Optional[TimingMiddleware] = None


def set_timing_middleware(middleware: TimingMiddleware):
    """设置全局中间件实例"""
    global timing_middleware
    timing_middleware = middleware


def get_timing_middleware() -> Optional[TimingMiddleware]:
    """获取全局中间件实例"""
    return timing_middleware
