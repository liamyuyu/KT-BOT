"""
监控指标 API 端点

提供系统资源、数据库、API 性能等指标的查询接口。
"""

import asyncio
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException

from src.monitoring.metrics_collector import get_metrics_collector

logger = logging.getLogger(__name__)
from src.api.middleware.timing import get_timing_middleware
from src.api.schemas.metrics import (
    SystemMetricsResponse,
    DatabaseMetricsResponse,
    APIMetricsResponse,
    RetrievalMetricsResponse,
    AllMetricsResponse,
    SystemMetricsData,
    DatabaseMetricsData,
    APIStatisticsData,
    RetrievalMetricsData,
    AllMetricsData,
)

router = APIRouter()


@router.get("/system", response_model=SystemMetricsResponse)
async def get_system_metrics():
    """
    获取系统资源指标

    Returns:
        SystemMetricsResponse: 包含 CPU、内存、磁盘使用情况
    """
    try:
        collector = get_metrics_collector()
        metrics = collector.get_system_metrics()

        return SystemMetricsResponse(
            success=True,
            data=SystemMetricsData(**metrics.to_dict())
        )
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        raise HTTPException(status_code=500, detail=f"获取系统指标失败: {str(e)}")


@router.get("/database", response_model=DatabaseMetricsResponse)
async def get_database_metrics():
    """
    获取数据库连接池状态

    Returns:
        DatabaseMetricsResponse: 包含连接池大小、已签出连接数等
    """
    try:
        collector = get_metrics_collector()
        metrics = collector.get_database_metrics()

        return DatabaseMetricsResponse(
            success=True,
            data=DatabaseMetricsData(**metrics.to_dict())
        )
    except Exception as e:
        logger.error(f"Failed to get database metrics: {e}")
        raise HTTPException(status_code=500, detail=f"获取数据库指标失败: {str(e)}")


@router.get("/api", response_model=APIMetricsResponse)
async def get_api_metrics():
    """
    获取 API 性能统计

    Returns:
        APIMetricsResponse: 包含请求数、响应时间百分位、最慢端点等
    """
    try:
        middleware = get_timing_middleware()
        if middleware is None:
            raise HTTPException(
                status_code=503,
                detail="性能监控中间件未初始化"
            )

        stats = middleware.get_statistics()

        return APIMetricsResponse(
            success=True,
            data=APIStatisticsData(**stats.to_dict())
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get API metrics: {e}")
        raise HTTPException(status_code=500, detail=f"获取 API 指标失败: {str(e)}")


@router.get("/retrieval", response_model=RetrievalMetricsResponse)
async def get_retrieval_metrics():
    """
    获取检索性能指标

    Returns:
        RetrievalMetricsResponse: 包含搜索次数、平均搜索时间等
    """
    try:
        # 简单实现：从 timing_middleware 过滤 /search 端点的请求
        middleware = get_timing_middleware()
        if middleware is None:
            # 返回默认值
            return RetrievalMetricsResponse(
                success=True,
                data=RetrievalMetricsData(
                    total_searches=0,
                    avg_search_time_ms=0.0,
                    p95_search_time_ms=0.0,
                    timestamp=datetime.now().isoformat()
                )
            )

        # 过滤搜索请求
        search_records = [
            r for r in middleware.records
            if "/search" in r.path.lower()
        ]

        if not search_records:
            return RetrievalMetricsResponse(
                success=True,
                data=RetrievalMetricsData(
                    total_searches=0,
                    avg_search_time_ms=0.0,
                    p95_search_time_ms=0.0,
                    timestamp=datetime.now().isoformat()
                )
            )

        # 计算统计值
        import numpy as np
        durations = [r.duration_ms for r in search_records]
        avg_search_time = float(np.mean(durations))
        p95_search_time = float(np.percentile(durations, 95))

        return RetrievalMetricsResponse(
            success=True,
            data=RetrievalMetricsData(
                total_searches=len(search_records),
                avg_search_time_ms=round(avg_search_time, 2),
                p95_search_time_ms=round(p95_search_time, 2),
                timestamp=datetime.now().isoformat()
            )
        )
    except Exception as e:
        logger.error(f"Failed to get retrieval metrics: {e}")
        raise HTTPException(status_code=500, detail=f"获取检索指标失败: {str(e)}")


@router.get("/all", response_model=AllMetricsResponse)
async def get_all_metrics():
    """
    一次性获取所有指标

    并发获取所有指标以提高性能。

    Returns:
        AllMetricsResponse: 包含所有指标数据
    """
    try:
        # 并发获取所有指标
        results = await asyncio.gather(
            get_system_metrics(),
            get_database_metrics(),
            get_api_metrics(),
            get_retrieval_metrics(),
            return_exceptions=True
        )

        # 检查错误
        errors = [r for r in results if isinstance(r, Exception)]
        if errors:
            logger.error(f"Failed to get some metrics: {errors}")
            raise HTTPException(
                status_code=500,
                detail=f"获取部分指标失败: {errors[0]}"
            )

        system_resp, database_resp, api_resp, retrieval_resp = results

        return AllMetricsResponse(
            success=True,
            data=AllMetricsData(
                system=system_resp.data,
                database=database_resp.data,
                api=api_resp.data,
                retrieval=retrieval_resp.data
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get all metrics: {e}")
        raise HTTPException(status_code=500, detail=f"获取所有指标失败: {str(e)}")
