"""
Redis Citation Cache Module
Redis 引用缓存模块 - L2 缓存层
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import hashlib
import json
import logging

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class RedisCitationCache:
    """
    Redis 引用结果缓存
    作为 L2 缓存层（L1 为内存缓存）
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        default_ttl: int = 1800  # 30分钟
    ):
        """
        初始化 Redis 缓存

        Args:
            redis_url: Redis 连接 URL
            default_ttl: 默认 TTL（秒）
        """
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.redis_client: Optional[redis.Redis] = None
        self._initialized = False
        self._cache_hits = 0
        self._cache_misses = 0

    async def initialize(self) -> bool:
        """
        初始化 Redis 连接

        Returns:
            bool: 是否成功初始化
        """
        if not REDIS_AVAILABLE:
            logger.warning("redis package not installed, L2 cache disabled")
            return False

        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=False,  # 处理二进制数据
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # 测试连接
            await self.redis_client.ping()
            self._initialized = True
            logger.info("Redis citation cache initialized successfully")
            return True
        except Exception as e:
            logger.warning(f"Failed to initialize Redis cache: {e}")
            self._initialized = False
            return False

    async def close(self):
        """关闭 Redis 连接"""
        if self.redis_client:
            await self.redis_client.close()
            self._initialized = False

    def _generate_cache_key(self, query: str, params: Dict[str, Any]) -> str:
        """
        生成缓存键

        格式: citation:query:{md5(query+params)}

        Args:
            query: 查询文本
            params: 查询参数（top_k, filters 等）

        Returns:
            str: 缓存键
        """
        # 序列化参数
        params_str = json.dumps(params, sort_keys=True)
        content = f"{query}|{params_str}"

        # MD5 哈希
        hash_key = hashlib.md5(content.encode()).hexdigest()

        return f"citation:query:{hash_key}"

    async def get_citations(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        从缓存获取引用结果

        Args:
            query: 查询文本
            params: 查询参数

        Returns:
            List[Dict]: 缓存的引用列表，未命中返回 None
        """
        if not self._initialized or not self.redis_client:
            return None

        if params is None:
            params = {}

        try:
            cache_key = self._generate_cache_key(query, params)
            cached_data = await self.redis_client.get(cache_key)

            if cached_data:
                self._cache_hits += 1
                # 解析 JSON
                citations = json.loads(cached_data)
                logger.debug(f"Cache HIT for query: {query[:50]}...")
                return citations
            else:
                self._cache_misses += 1
                logger.debug(f"Cache MISS for query: {query[:50]}...")
                return None

        except Exception as e:
            logger.error(f"Failed to get citations from cache: {e}")
            return None

    async def set_citations(
        self,
        query: str,
        citations: List[Dict[str, Any]],
        params: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None
    ) -> bool:
        """
        缓存引用结果

        Args:
            query: 查询文本
            citations: 引用列表
            params: 查询参数
            ttl: 缓存过期时间（秒），默认使用 default_ttl

        Returns:
            bool: 是否成功缓存
        """
        if not self._initialized or not self.redis_client:
            return False

        if params is None:
            params = {}

        if ttl is None:
            ttl = self.default_ttl

        try:
            cache_key = self._generate_cache_key(query, params)

            # 序列化为 JSON
            cached_data = json.dumps(citations, ensure_ascii=False, default=str)

            # 存储到 Redis
            await self.redis_client.setex(
                cache_key,
                ttl,
                cached_data
            )

            logger.debug(f"Cached {len(citations)} citations for query: {query[:50]}...")
            return True

        except Exception as e:
            logger.error(f"Failed to cache citations: {e}")
            return False

    async def invalidate_by_source(self, source_id: str) -> int:
        """
        按来源 ID 失效缓存

        注意：由于缓存键是查询哈希，无法直接按 source_id 失效
        此方法扫描所有缓存键并检查内容（性能较差，仅用于必要时）

        Args:
            source_id: 来源 ID

        Returns:
            int: 失效的缓存数量
        """
        if not self._initialized or not self.redis_client:
            return 0

        try:
            # 扫描所有引用缓存键
            invalidated_count = 0
            cursor = 0

            while True:
                cursor, keys = await self.redis_client.scan(
                    cursor,
                    match="citation:query:*",
                    count=100
                )

                for key in keys:
                    try:
                        # 获取缓存数据
                        cached_data = await self.redis_client.get(key)
                        if not cached_data:
                            continue

                        citations = json.loads(cached_data)

                        # 检查是否包含指定 source_id
                        for citation in citations:
                            if citation.get("source_id") == source_id:
                                await self.redis_client.delete(key)
                                invalidated_count += 1
                                break

                    except Exception:
                        continue

                if cursor == 0:
                    break

            logger.info(f"Invalidated {invalidated_count} cache entries for source: {source_id}")
            return invalidated_count

        except Exception as e:
            logger.error(f"Failed to invalidate cache by source: {e}")
            return 0

    async def clear_all(self) -> bool:
        """
        清除所有引用缓存

        Returns:
            bool: 是否成功清除
        """
        if not self._initialized or not self.redis_client:
            return False

        try:
            cursor = 0
            deleted_count = 0

            while True:
                cursor, keys = await self.redis_client.scan(
                    cursor,
                    match="citation:query:*",
                    count=100
                )

                if keys:
                    deleted = await self.redis_client.delete(*keys)
                    deleted_count += deleted

                if cursor == 0:
                    break

            logger.info(f"Cleared {deleted_count} citation cache entries")
            return True

        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False

    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            Dict: 缓存统计信息
        """
        if not self._initialized or not self.redis_client:
            return {
                "enabled": False,
                "cache_hits": 0,
                "cache_misses": 0,
                "hit_rate": 0.0,
                "total_entries": 0
            }

        try:
            # 统计缓存条目数量
            cursor = 0
            total_entries = 0

            while True:
                cursor, keys = await self.redis_client.scan(
                    cursor,
                    match="citation:query:*",
                    count=100
                )
                total_entries += len(keys)

                if cursor == 0:
                    break

            # 计算命中率
            total_requests = self._cache_hits + self._cache_misses
            hit_rate = (self._cache_hits / total_requests * 100) if total_requests > 0 else 0.0

            return {
                "enabled": True,
                "cache_hits": self._cache_hits,
                "cache_misses": self._cache_misses,
                "hit_rate": round(hit_rate, 2),
                "total_entries": total_entries
            }

        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {
                "enabled": True,
                "cache_hits": self._cache_hits,
                "cache_misses": self._cache_misses,
                "hit_rate": 0.0,
                "total_entries": 0,
                "error": str(e)
            }


# 全局单例
_redis_cache: Optional[RedisCitationCache] = None


async def get_redis_cache(
    redis_url: str = "redis://localhost:6379/0",
    default_ttl: int = 1800
) -> Optional[RedisCitationCache]:
    """
    获取全局 Redis 缓存单例

    Args:
        redis_url: Redis 连接 URL
        default_ttl: 默认 TTL（秒）

    Returns:
        RedisCitationCache: 缓存实例，失败返回 None
    """
    global _redis_cache

    if _redis_cache is None:
        _redis_cache = RedisCitationCache(redis_url, default_ttl)
        initialized = await _redis_cache.initialize()
        if not initialized:
            _redis_cache = None

    return _redis_cache
