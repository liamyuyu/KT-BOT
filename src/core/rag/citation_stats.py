"""
Citation Statistics Collector Module
引用统计信息收集模块 - 使用 Redis 存储和查询统计数据
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import logging

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class CitationStatisticsCollector:
    """
    引用统计信息收集器
    使用 Redis 存储和管理引用使用统计
    """

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """
        初始化统计收集器

        Args:
            redis_url: Redis 连接 URL
        """
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self._initialized = False

    async def initialize(self) -> bool:
        """
        初始化 Redis 连接

        Returns:
            bool: 是否成功初始化
        """
        if not REDIS_AVAILABLE:
            logger.warning("redis package not installed, statistics collection disabled")
            return False

        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # 测试连接
            await self.redis_client.ping()
            self._initialized = True
            logger.info("Citation statistics collector initialized successfully")
            return True
        except Exception as e:
            logger.warning(f"Failed to initialize Redis for statistics: {e}")
            self._initialized = False
            return False

    async def close(self):
        """关闭 Redis 连接"""
        if self.redis_client:
            await self.redis_client.close()
            self._initialized = False

    def _get_stats_key(self, source_id: str) -> str:
        """获取统计数据的 Redis key"""
        return f"citation_stats:{source_id}"

    def _get_popular_key(self, time_range: str = "7d") -> str:
        """获取热门引用的 Redis key"""
        return f"citation_popular:{time_range}"

    async def record_citation_usage(
        self,
        source_id: str,
        query: str,
        relevance_score: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        记录引用使用情况

        Args:
            source_id: 来源 ID
            query: 查询文本
            relevance_score: 相关性分数
            metadata: 额外元数据

        Returns:
            bool: 是否成功记录
        """
        if not self._initialized or not self.redis_client:
            return False

        try:
            stats_key = self._get_stats_key(source_id)
            now = datetime.now().isoformat()

            # 使用 pipeline 批量操作
            async with self.redis_client.pipeline() as pipe:
                # 1. 更新 Hash 统计数据
                pipe.hincrby(stats_key, "total_references", 1)
                pipe.hset(stats_key, "last_referenced", now)

                # 2. 更新唯一查询计数（使用 HyperLogLog）
                query_key = f"citation_queries:{source_id}"
                pipe.pfadd(query_key, query)
                pipe.expire(query_key, 60 * 60 * 24 * 90)  # 90天过期

                # 3. 累加平均相关度（存储总和和计数，按需计算平均值）
                pipe.hincrbyfloat(stats_key, "relevance_sum", relevance_score)
                pipe.hincrby(stats_key, "relevance_count", 1)

                # 4. 更新热门引用排行（7天、30天）
                pipe.zincrby(self._get_popular_key("7d"), 1, source_id)
                pipe.zincrby(self._get_popular_key("30d"), 1, source_id)

                # 5. 设置过期时间（90天）
                pipe.expire(stats_key, 60 * 60 * 24 * 90)
                pipe.expire(self._get_popular_key("7d"), 60 * 60 * 24 * 7)
                pipe.expire(self._get_popular_key("30d"), 60 * 60 * 24 * 30)

                # 执行所有操作
                await pipe.execute()

            return True

        except Exception as e:
            logger.error(f"Failed to record citation usage for {source_id}: {e}")
            return False

    async def get_citation_stats(self, source_id: str) -> Optional[Dict[str, Any]]:
        """
        获取引用统计信息

        Args:
            source_id: 来源 ID

        Returns:
            Dict: 统计信息，包含 total_references, unique_queries, last_referenced, avg_relevance
        """
        if not self._initialized or not self.redis_client:
            return None

        try:
            stats_key = self._get_stats_key(source_id)
            query_key = f"citation_queries:{source_id}"

            # 批量获取数据
            async with self.redis_client.pipeline() as pipe:
                pipe.hgetall(stats_key)
                pipe.pfcount(query_key)
                results = await pipe.execute()

            stats_data = results[0]
            unique_queries = results[1]

            if not stats_data:
                return None

            # 解析统计数据
            total_references = int(stats_data.get("total_references", 0))
            last_referenced = stats_data.get("last_referenced")
            relevance_sum = float(stats_data.get("relevance_sum", 0))
            relevance_count = int(stats_data.get("relevance_count", 1))

            # 计算平均相关度
            avg_relevance = relevance_sum / relevance_count if relevance_count > 0 else 0.0

            return {
                "total_references": total_references,
                "unique_queries": unique_queries,
                "last_referenced": last_referenced,
                "avg_relevance": round(avg_relevance, 3)
            }

        except Exception as e:
            logger.error(f"Failed to get citation stats for {source_id}: {e}")
            return None

    async def get_popular_citations(
        self,
        limit: int = 10,
        time_range: str = "7d"
    ) -> List[Dict[str, Any]]:
        """
        获取热门引用列表

        Args:
            limit: 返回数量限制
            time_range: 时间范围（7d, 30d）

        Returns:
            List[Dict]: 热门引用列表，包含 source_id 和 usage_count
        """
        if not self._initialized or not self.redis_client:
            return []

        try:
            popular_key = self._get_popular_key(time_range)

            # 获取热门引用（降序，分数最高的在前）
            popular_items = await self.redis_client.zrevrange(
                popular_key,
                0,
                limit - 1,
                withscores=True
            )

            # 格式化结果
            results = []
            for source_id, usage_count in popular_items:
                results.append({
                    "source_id": source_id,
                    "usage_count": int(usage_count)
                })

            return results

        except Exception as e:
            logger.error(f"Failed to get popular citations: {e}")
            return []

    async def batch_update_stats(self, citations: List[Dict[str, Any]]) -> int:
        """
        批量更新引用统计信息

        Args:
            citations: 引用列表，每个引用包含 source_id, query, relevance_score

        Returns:
            int: 成功更新的数量
        """
        if not self._initialized or not self.redis_client:
            return 0

        success_count = 0
        for citation in citations:
            source_id = citation.get("source_id")
            query = citation.get("query", "")
            relevance_score = citation.get("relevance_score", 0.0)
            metadata = citation.get("metadata")

            if source_id:
                success = await self.record_citation_usage(
                    source_id=source_id,
                    query=query,
                    relevance_score=relevance_score,
                    metadata=metadata
                )
                if success:
                    success_count += 1

        return success_count

    async def get_batch_stats(
        self,
        source_ids: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        批量获取多个引用的统计信息

        Args:
            source_ids: 来源 ID 列表

        Returns:
            Dict: {source_id: stats} 映射
        """
        if not self._initialized or not self.redis_client:
            return {}

        results = {}
        for source_id in source_ids:
            stats = await self.get_citation_stats(source_id)
            if stats:
                results[source_id] = stats

        return results

    async def clear_stats(self, source_id: str) -> bool:
        """
        清除指定来源的统计数据

        Args:
            source_id: 来源 ID

        Returns:
            bool: 是否成功清除
        """
        if not self._initialized or not self.redis_client:
            return False

        try:
            stats_key = self._get_stats_key(source_id)
            query_key = f"citation_queries:{source_id}"

            async with self.redis_client.pipeline() as pipe:
                pipe.delete(stats_key)
                pipe.delete(query_key)
                # 从热门列表中移除
                pipe.zrem(self._get_popular_key("7d"), source_id)
                pipe.zrem(self._get_popular_key("30d"), source_id)
                await pipe.execute()

            return True

        except Exception as e:
            logger.error(f"Failed to clear stats for {source_id}: {e}")
            return False

    async def get_global_stats(self) -> Dict[str, Any]:
        """
        获取全局统计信息

        Returns:
            Dict: 全局统计信息
        """
        if not self._initialized or not self.redis_client:
            return {}

        try:
            # 获取热门引用总数
            popular_7d_count = await self.redis_client.zcard(self._get_popular_key("7d"))
            popular_30d_count = await self.redis_client.zcard(self._get_popular_key("30d"))

            # 获取最大使用次数（用于归一化）
            popular_7d = await self.get_popular_citations(limit=1, time_range="7d")
            max_usage_7d = popular_7d[0]["usage_count"] if popular_7d else 0

            popular_30d = await self.get_popular_citations(limit=1, time_range="30d")
            max_usage_30d = popular_30d[0]["usage_count"] if popular_30d else 0

            return {
                "total_tracked_citations_7d": popular_7d_count,
                "total_tracked_citations_30d": popular_30d_count,
                "max_usage_7d": max_usage_7d,
                "max_usage_30d": max_usage_30d
            }

        except Exception as e:
            logger.error(f"Failed to get global stats: {e}")
            return {}


# 全局单例
_stats_collector: Optional[CitationStatisticsCollector] = None


async def get_stats_collector(redis_url: str = "redis://localhost:6379/0") -> Optional[CitationStatisticsCollector]:
    """
    获取全局统计收集器单例

    Args:
        redis_url: Redis 连接 URL

    Returns:
        CitationStatisticsCollector: 统计收集器实例，失败返回 None
    """
    global _stats_collector

    if _stats_collector is None:
        _stats_collector = CitationStatisticsCollector(redis_url)
        initialized = await _stats_collector.initialize()
        if not initialized:
            _stats_collector = None

    return _stats_collector
