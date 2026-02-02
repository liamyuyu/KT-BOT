"""
Citations API Routes
引用管理相关的 API 端点
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/citations", tags=["citations"])

# 延迟导入（避免循环依赖）
try:
    from ...core.cache.redis_cache import get_redis_cache
    from ...core.rag.citation_stats import get_stats_collector
    from ...core.rag.citation_scoring import batch_calculate_quality_scores, sort_by_quality
    REDIS_MODULES_AVAILABLE = True
except ImportError:
    REDIS_MODULES_AVAILABLE = False
    logger.warning("Redis modules not available for citations API")


# Pydantic 模型定义

class CitationFilterRequest(BaseModel):
    """引用过滤请求"""
    source_types: Optional[List[str]] = Field(None, description="来源类型过滤（jira, confluence, local）")
    min_quality: Optional[float] = Field(0.0, ge=0.0, le=1.0, description="最低质量分数")
    sort_by: str = Field("quality", description="排序方式（quality, relevance, usage, freshness）")
    limit: Optional[int] = Field(None, ge=1, le=100, description="返回数量限制")


class BatchScoreRequest(BaseModel):
    """批量质量评分请求"""
    citations: List[Dict[str, Any]] = Field(..., description="引用列表")
    query: Optional[str] = Field(None, description="查询文本（用于覆盖度计算）")


class CitationStatsResponse(BaseModel):
    """引用统计响应"""
    source_id: str
    total_references: int
    unique_queries: int
    last_referenced: Optional[str]
    avg_relevance: float


class PopularCitationResponse(BaseModel):
    """热门引用响应"""
    source_id: str
    usage_count: int


class GlobalStatsResponse(BaseModel):
    """全局统计响应"""
    total_tracked_citations_7d: int
    total_tracked_citations_30d: int
    max_usage_7d: int
    max_usage_30d: int


class CacheStatsResponse(BaseModel):
    """缓存统计响应"""
    enabled: bool
    cache_hits: int
    cache_misses: int
    hit_rate: float
    total_entries: int


@router.get("/filter")
async def filter_citations(
    source_types: Optional[str] = Query(None, description="逗号分隔的来源类型（如：jira,confluence）"),
    min_quality: float = Query(0.0, ge=0.0, le=1.0, description="最低质量分数"),
    sort_by: str = Query("quality", description="排序方式"),
    limit: Optional[int] = Query(None, ge=1, le=100, description="返回数量限制")
) -> Dict[str, Any]:
    """
    过滤和排序引用

    支持的排序方式：
    - quality: 质量优先
    - relevance: 相关度优先
    - usage: 热门优先
    - freshness: 时效性优先
    """
    if not REDIS_MODULES_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Citation filtering requires Redis, which is not available"
        )

    try:
        # 解析来源类型
        source_type_list = None
        if source_types:
            source_type_list = [s.strip() for s in source_types.split(",")]

        # TODO: 从缓存或数据库获取引用列表
        # 这里需要根据实际情况实现，当前返回示例响应
        logger.info(
            f"Filter request: source_types={source_type_list}, "
            f"min_quality={min_quality}, sort_by={sort_by}, limit={limit}"
        )

        return {
            "message": "Filter endpoint is ready",
            "filters": {
                "source_types": source_type_list,
                "min_quality": min_quality,
                "sort_by": sort_by,
                "limit": limit
            },
            "note": "Full implementation requires context-specific citation data"
        }

    except Exception as e:
        logger.error(f"Failed to filter citations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/{source_id}", response_model=CitationStatsResponse)
async def get_citation_stats(source_id: str) -> CitationStatsResponse:
    """
    获取指定来源的统计信息

    Args:
        source_id: 来源 ID（如 Jira Issue Key 或 Document ID）

    Returns:
        引用统计信息
    """
    if not REDIS_MODULES_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Citation statistics require Redis, which is not available"
        )

    try:
        stats_collector = await get_stats_collector()
        if not stats_collector:
            raise HTTPException(
                status_code=503,
                detail="Statistics collector not initialized"
            )

        stats = await stats_collector.get_citation_stats(source_id)
        if not stats:
            raise HTTPException(
                status_code=404,
                detail=f"No statistics found for source: {source_id}"
            )

        return CitationStatsResponse(
            source_id=source_id,
            total_references=stats["total_references"],
            unique_queries=stats["unique_queries"],
            last_referenced=stats["last_referenced"],
            avg_relevance=stats["avg_relevance"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get citation stats for {source_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=GlobalStatsResponse)
async def get_global_stats() -> GlobalStatsResponse:
    """
    获取全局统计信息
    """
    if not REDIS_MODULES_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Citation statistics require Redis, which is not available"
        )

    try:
        stats_collector = await get_stats_collector()
        if not stats_collector:
            raise HTTPException(
                status_code=503,
                detail="Statistics collector not initialized"
            )

        stats = await stats_collector.get_global_stats()

        return GlobalStatsResponse(
            total_tracked_citations_7d=stats.get("total_tracked_citations_7d", 0),
            total_tracked_citations_30d=stats.get("total_tracked_citations_30d", 0),
            max_usage_7d=stats.get("max_usage_7d", 0),
            max_usage_30d=stats.get("max_usage_30d", 0)
        )

    except Exception as e:
        logger.error(f"Failed to get global stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/popular", response_model=List[PopularCitationResponse])
async def get_popular_citations(
    limit: int = Query(10, ge=1, le=100, description="返回数量"),
    time_range: str = Query("7d", description="时间范围（7d 或 30d）")
) -> List[PopularCitationResponse]:
    """
    获取热门引用列表

    Args:
        limit: 返回数量
        time_range: 时间范围（7d, 30d）

    Returns:
        热门引用列表
    """
    if not REDIS_MODULES_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Popular citations require Redis, which is not available"
        )

    if time_range not in ["7d", "30d"]:
        raise HTTPException(
            status_code=400,
            detail="time_range must be '7d' or '30d'"
        )

    try:
        stats_collector = await get_stats_collector()
        if not stats_collector:
            raise HTTPException(
                status_code=503,
                detail="Statistics collector not initialized"
            )

        popular = await stats_collector.get_popular_citations(limit, time_range)

        return [
            PopularCitationResponse(
                source_id=item["source_id"],
                usage_count=item["usage_count"]
            )
            for item in popular
        ]

    except Exception as e:
        logger.error(f"Failed to get popular citations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-score")
async def batch_score_citations(request: BatchScoreRequest) -> Dict[str, Any]:
    """
    批量计算引用质量分数

    Args:
        request: 批量评分请求

    Returns:
        添加了质量分数的引用列表
    """
    if not REDIS_MODULES_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Quality scoring requires Redis modules, which are not available"
        )

    try:
        # 获取统计信息
        stats_collector = await get_stats_collector()
        usage_stats_map = None

        if stats_collector:
            # 收集所有 source_id
            source_ids = [c.get("source_id") for c in request.citations if c.get("source_id")]
            usage_stats_map = await stats_collector.get_batch_stats(source_ids)

        # 批量计算质量分数
        enriched_citations = batch_calculate_quality_scores(
            citations=request.citations,
            usage_stats_map=usage_stats_map
        )

        return {
            "count": len(enriched_citations),
            "citations": enriched_citations
        }

    except Exception as e:
        logger.error(f"Failed to batch score citations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/stats", response_model=CacheStatsResponse)
async def get_cache_stats() -> CacheStatsResponse:
    """
    获取缓存统计信息
    """
    if not REDIS_MODULES_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Cache statistics require Redis, which is not available"
        )

    try:
        redis_cache = await get_redis_cache()
        if not redis_cache:
            raise HTTPException(
                status_code=503,
                detail="Redis cache not initialized"
            )

        stats = await redis_cache.get_cache_stats()

        return CacheStatsResponse(
            enabled=stats["enabled"],
            cache_hits=stats["cache_hits"],
            cache_misses=stats["cache_misses"],
            hit_rate=stats["hit_rate"],
            total_entries=stats["total_entries"]
        )

    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cache")
async def clear_cache() -> Dict[str, str]:
    """
    清除所有引用缓存
    """
    if not REDIS_MODULES_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Cache clearing requires Redis, which is not available"
        )

    try:
        redis_cache = await get_redis_cache()
        if not redis_cache:
            raise HTTPException(
                status_code=503,
                detail="Redis cache not initialized"
            )

        success = await redis_cache.clear_all()
        if success:
            return {"message": "Cache cleared successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to clear cache")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))
