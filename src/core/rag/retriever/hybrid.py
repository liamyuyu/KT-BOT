"""
Hybrid Retriever
混合检索器：融合向量检索和全文检索（BM25）
"""

import logging
import asyncio
import time
import hashlib
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from functools import lru_cache

from ..models import RetrievalResult, RetrievalConfig, HybridConfig
from ..exceptions import RetrievalError, InvalidConfigError
from .base import BaseRetriever
from .vector import VectorRetriever
from .bm25 import BM25Retriever

logger = logging.getLogger(__name__)


class HybridRetriever(BaseRetriever):
    """
    混合检索器

    融合向量检索（语义相似度）和 BM25 全文检索（关键词匹配）
    支持多种融合策略：RRF、加权平均、线性组合
    """

    def __init__(
        self,
        vector_retriever: VectorRetriever,
        bm25_retriever: BM25Retriever,
        retrieval_config: RetrievalConfig = None,
        hybrid_config: HybridConfig = None,
        enable_cache: bool = True,
        cache_size: int = 128,
        retrieval_timeout: float = 10.0
    ):
        """
        初始化混合检索器

        Args:
            vector_retriever: 向量检索器实例
            bm25_retriever: BM25 检索器实例
            retrieval_config: 检索配置
            hybrid_config: 混合检索配置
            enable_cache: 是否启用查询缓存
            cache_size: 缓存大小（条目数）
            retrieval_timeout: 检索超时时间（秒）
        """
        super().__init__(retrieval_config)
        self.vector_retriever = vector_retriever
        self.bm25_retriever = bm25_retriever
        self.hybrid_config = hybrid_config or HybridConfig()
        self.enable_cache = enable_cache
        self.cache_size = cache_size
        self.retrieval_timeout = retrieval_timeout

        # 缓存字典: query_hash -> (results, timestamp)
        self._cache: Dict[str, Tuple[List[RetrievalResult], float]] = {}
        self._cache_ttl = 300.0  # 缓存有效期 5 分钟

        # 性能统计
        self._stats = {
            "total_queries": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "vector_time_total": 0.0,
            "bm25_time_total": 0.0,
            "fusion_time_total": 0.0,
            "timeout_count": 0
        }

        # 验证配置
        if self.hybrid_config.fusion_method not in ["rrf", "weighted", "linear"]:
            raise InvalidConfigError(
                f"Invalid fusion_method: {self.hybrid_config.fusion_method}. "
                f"Must be one of: rrf, weighted, linear"
            )

        logger.info(
            f"HybridRetriever initialized with fusion_method={self.hybrid_config.fusion_method}, "
            f"cache_enabled={enable_cache}, timeout={retrieval_timeout}s"
        )

    def _get_cache_key(self, query: str, top_k: int, **kwargs) -> str:
        """生成查询缓存键"""
        cache_str = f"{query}|{top_k}|{kwargs.get('vector_top_k')}|{kwargs.get('bm25_top_k')}"
        return hashlib.md5(cache_str.encode()).hexdigest()

    def _get_from_cache(self, cache_key: str) -> Optional[List[RetrievalResult]]:
        """从缓存获取结果"""
        if not self.enable_cache:
            return None

        if cache_key in self._cache:
            results, timestamp = self._cache[cache_key]
            # 检查是否过期
            if time.time() - timestamp < self._cache_ttl:
                self._stats["cache_hits"] += 1
                logger.debug(f"Cache hit for key: {cache_key}")
                return results
            else:
                # 过期，删除缓存
                del self._cache[cache_key]
                logger.debug(f"Cache expired for key: {cache_key}")

        self._stats["cache_misses"] += 1
        return None

    def _add_to_cache(self, cache_key: str, results: List[RetrievalResult]) -> None:
        """添加结果到缓存"""
        if not self.enable_cache:
            return

        # LRU 策略：如果缓存已满，删除最旧的条目
        if len(self._cache) >= self.cache_size:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]
            logger.debug(f"Cache full, evicted key: {oldest_key}")

        self._cache[cache_key] = (results, time.time())
        logger.debug(f"Added to cache, key: {cache_key}, size: {len(self._cache)}")

    async def retrieve(
        self,
        query: str,
        top_k: int = None,
        **kwargs
    ) -> List[RetrievalResult]:
        """
        混合检索（支持并发、超时、缓存）

        Args:
            query: 查询文本
            top_k: 返回结果数量（覆盖配置）
            **kwargs: 其他参数
                - vector_top_k: 向量检索候选数量（默认 top_k * 2）
                - bm25_top_k: BM25 检索候选数量（默认 top_k * 2）

        Returns:
            融合后的检索结果列表

        Raises:
            RetrievalError: 检索失败时抛出
        """
        if not query or not query.strip():
            raise InvalidConfigError("Query cannot be empty")

        # 更新统计
        self._stats["total_queries"] += 1
        start_time = time.time()

        try:
            # 使用配置的 top_k 或传入的 top_k
            k = top_k if top_k is not None else self.config.top_k

            # 候选数量：获取更多候选以提高融合效果
            vector_top_k = kwargs.get("vector_top_k", k * 2)
            bm25_top_k = kwargs.get("bm25_top_k", k * 2)

            # 检查缓存
            cache_key = self._get_cache_key(query, k, **kwargs)
            cached_results = self._get_from_cache(cache_key)
            if cached_results is not None:
                logger.info(f"Returned {len(cached_results)} cached results for query: {query[:50]}...")
                return cached_results

            # 并发执行两种检索（使用 asyncio.gather）
            logger.debug(f"Concurrent retrieval: vector_top_k={vector_top_k}, bm25_top_k={bm25_top_k}")

            # 记录各检索器的开始时间
            vector_start = time.time()
            bm25_start = time.time()

            try:
                # 使用 asyncio.gather 并发执行，带超时控制
                vector_results, bm25_results = await asyncio.wait_for(
                    asyncio.gather(
                        self.vector_retriever.retrieve(query, top_k=vector_top_k),
                        self.bm25_retriever.retrieve(query, top_k=bm25_top_k),
                        return_exceptions=False
                    ),
                    timeout=self.retrieval_timeout
                )

                # 记录检索耗时
                vector_time = time.time() - vector_start
                bm25_time = time.time() - bm25_start
                self._stats["vector_time_total"] += vector_time
                self._stats["bm25_time_total"] += bm25_time

                logger.info(
                    f"Concurrent retrieval completed: "
                    f"vector={len(vector_results)} results ({vector_time:.3f}s), "
                    f"bm25={len(bm25_results)} results ({bm25_time:.3f}s)"
                )

            except asyncio.TimeoutError:
                self._stats["timeout_count"] += 1
                logger.error(f"Retrieval timeout after {self.retrieval_timeout}s for query: {query[:50]}...")
                raise RetrievalError(
                    f"Retrieval timeout after {self.retrieval_timeout}s"
                )

            # 融合结果（记录融合时间）
            fusion_start = time.time()

            if self.hybrid_config.fusion_method == "rrf":
                fused_results = self._rrf_fusion(
                    vector_results,
                    bm25_results,
                    k=self.hybrid_config.rrf_k
                )
            elif self.hybrid_config.fusion_method == "weighted":
                fused_results = self._weighted_fusion(
                    vector_results,
                    bm25_results,
                    vector_weight=self.hybrid_config.vector_weight,
                    bm25_weight=self.hybrid_config.bm25_weight
                )
            elif self.hybrid_config.fusion_method == "linear":
                fused_results = self._linear_fusion(
                    vector_results,
                    bm25_results,
                    vector_weight=self.hybrid_config.vector_weight,
                    bm25_weight=self.hybrid_config.bm25_weight
                )
            else:
                raise InvalidConfigError(f"Unknown fusion method: {self.hybrid_config.fusion_method}")

            # 去重
            if self.hybrid_config.deduplicate:
                fused_results = self._deduplicate(fused_results)

            # 归一化分数
            if self.hybrid_config.normalize_scores and fused_results:
                fused_results = self._normalize_scores(fused_results)

            # 记录融合时间
            fusion_time = time.time() - fusion_start
            self._stats["fusion_time_total"] += fusion_time

            # 取 top-k
            final_results = fused_results[:k]

            # 过滤低分结果
            if self.config.min_score:
                final_results = [r for r in final_results if r.score >= self.config.min_score]

            # 添加到缓存
            self._add_to_cache(cache_key, final_results)

            # 记录总耗时
            total_time = time.time() - start_time

            logger.info(
                f"Hybrid retrieval completed: {len(final_results)} results, "
                f"total_time={total_time:.3f}s, fusion_time={fusion_time:.3f}s"
            )

            return final_results

        except asyncio.TimeoutError:
            # 已在上面处理
            raise
        except InvalidConfigError:
            # 配置错误直接抛出
            raise
        except Exception as e:
            logger.error(f"Hybrid retrieval failed: {e}", exc_info=True)
            raise RetrievalError(f"Hybrid retrieval failed: {str(e)}")

    async def batch_retrieve(
        self,
        queries: List[str],
        top_k: int = None,
        **kwargs
    ) -> List[List[RetrievalResult]]:
        """
        批量混合检索

        Args:
            queries: 查询文本列表
            top_k: 每个查询返回的结果数量
            **kwargs: 其他参数

        Returns:
            嵌套的检索结果列表
        """
        results = []
        for query in queries:
            result = await self.retrieve(query, top_k, **kwargs)
            results.append(result)
        return results

    def _rrf_fusion(
        self,
        vector_results: List[RetrievalResult],
        bm25_results: List[RetrievalResult],
        k: int = 60
    ) -> List[RetrievalResult]:
        """
        Reciprocal Rank Fusion (RRF) 融合算法

        RRF 公式: score(d) = sum(1 / (k + rank_i))
        其中 rank_i 是文档 d 在第 i 个检索器中的排名

        Args:
            vector_results: 向量检索结果
            bm25_results: BM25 检索结果
            k: RRF 参数（默认 60）

        Returns:
            融合后的结果列表（按分数降序排列）
        """
        logger.debug(f"RRF fusion with k={k}")

        # 构建 chunk_id -> RetrievalResult 映射
        result_map: Dict[str, RetrievalResult] = {}

        # 构建 chunk_id -> RRF 分数 映射
        rrf_scores: Dict[str, float] = defaultdict(float)

        # 处理向量检索结果
        for rank, result in enumerate(vector_results, start=1):
            chunk_id = result.chunk_id
            rrf_scores[chunk_id] += 1.0 / (k + rank)
            if chunk_id not in result_map:
                result_map[chunk_id] = result

        # 处理 BM25 检索结果
        for rank, result in enumerate(bm25_results, start=1):
            chunk_id = result.chunk_id
            rrf_scores[chunk_id] += 1.0 / (k + rank)
            if chunk_id not in result_map:
                result_map[chunk_id] = result

        # 构建融合结果
        fused_results = []
        for chunk_id, rrf_score in rrf_scores.items():
            result = result_map[chunk_id]
            # 创建新的 RetrievalResult，使用 RRF 分数
            fused_result = RetrievalResult(
                chunk_id=result.chunk_id,
                parent_id=result.parent_id,
                content=result.content,
                metadata=result.metadata,
                score=rrf_score,  # RRF 分数
                distance=1.0 - rrf_score,  # distance 与 score 相反
                chunk_index=result.chunk_index
            )
            fused_results.append(fused_result)

        # 按 RRF 分数降序排序
        fused_results.sort(key=lambda x: x.score, reverse=True)

        logger.debug(f"RRF fusion produced {len(fused_results)} unique results")
        return fused_results

    def _weighted_fusion(
        self,
        vector_results: List[RetrievalResult],
        bm25_results: List[RetrievalResult],
        vector_weight: float = 0.5,
        bm25_weight: float = 0.5
    ) -> List[RetrievalResult]:
        """
        加权平均融合

        score(d) = alpha * vector_score(d) + beta * bm25_score(d)
        其中 alpha + beta = 1

        Args:
            vector_results: 向量检索结果
            bm25_results: BM25 检索结果
            vector_weight: 向量检索权重
            bm25_weight: BM25 检索权重

        Returns:
            融合后的结果列表（按分数降序排列）
        """
        logger.debug(f"Weighted fusion with vector_weight={vector_weight}, bm25_weight={bm25_weight}")

        # 构建 chunk_id -> (RetrievalResult, vector_score, bm25_score) 映射
        result_map: Dict[str, tuple] = {}

        # 收集向量检索分数
        for result in vector_results:
            chunk_id = result.chunk_id
            result_map[chunk_id] = (result, result.score, 0.0)

        # 收集 BM25 检索分数
        for result in bm25_results:
            chunk_id = result.chunk_id
            if chunk_id in result_map:
                existing_result, vector_score, _ = result_map[chunk_id]
                result_map[chunk_id] = (existing_result, vector_score, result.score)
            else:
                result_map[chunk_id] = (result, 0.0, result.score)

        # 计算加权分数
        fused_results = []
        for chunk_id, (result, vector_score, bm25_score) in result_map.items():
            weighted_score = vector_weight * vector_score + bm25_weight * bm25_score

            fused_result = RetrievalResult(
                chunk_id=result.chunk_id,
                parent_id=result.parent_id,
                content=result.content,
                metadata=result.metadata,
                score=weighted_score,
                distance=1.0 - weighted_score,
                chunk_index=result.chunk_index
            )
            fused_results.append(fused_result)

        # 按加权分数降序排序
        fused_results.sort(key=lambda x: x.score, reverse=True)

        logger.debug(f"Weighted fusion produced {len(fused_results)} unique results")
        return fused_results

    def _linear_fusion(
        self,
        vector_results: List[RetrievalResult],
        bm25_results: List[RetrievalResult],
        vector_weight: float = 0.5,
        bm25_weight: float = 0.5
    ) -> List[RetrievalResult]:
        """
        线性组合融合（与加权平均相同，保留以备后续扩展）

        Args:
            vector_results: 向量检索结果
            bm25_results: BM25 检索结果
            vector_weight: 向量检索权重
            bm25_weight: BM25 检索权重

        Returns:
            融合后的结果列表
        """
        # 目前与加权平均相同
        return self._weighted_fusion(vector_results, bm25_results, vector_weight, bm25_weight)

    def _deduplicate(self, results: List[RetrievalResult]) -> List[RetrievalResult]:
        """
        去重（基于 chunk_id）

        如果同一个 chunk_id 出现多次，保留分数最高的

        Args:
            results: 检索结果列表

        Returns:
            去重后的结果列表
        """
        seen = set()
        deduplicated = []

        for result in results:
            if result.chunk_id not in seen:
                seen.add(result.chunk_id)
                deduplicated.append(result)

        if len(deduplicated) < len(results):
            logger.debug(f"Deduplicated: {len(results)} -> {len(deduplicated)}")

        return deduplicated

    def _normalize_scores(self, results: List[RetrievalResult]) -> List[RetrievalResult]:
        """
        归一化分数到 0-1 区间

        使用 Min-Max 归一化: score_norm = (score - min) / (max - min)

        Args:
            results: 检索结果列表

        Returns:
            归一化后的结果列表
        """
        if not results:
            return results

        scores = [r.score for r in results]
        min_score = min(scores)
        max_score = max(scores)

        # 如果所有分数相同，直接返回
        if max_score == min_score:
            return results

        # Min-Max 归一化
        normalized_results = []
        for result in results:
            normalized_score = (result.score - min_score) / (max_score - min_score)

            normalized_result = RetrievalResult(
                chunk_id=result.chunk_id,
                parent_id=result.parent_id,
                content=result.content,
                metadata=result.metadata,
                score=normalized_score,
                distance=1.0 - normalized_score,
                chunk_index=result.chunk_index
            )
            normalized_results.append(normalized_result)

        logger.debug(f"Scores normalized: [{min_score:.4f}, {max_score:.4f}] -> [0.0, 1.0]")
        return normalized_results

    def get_statistics(self) -> Dict[str, any]:
        """
        获取性能统计信息

        Returns:
            统计信息字典
        """
        stats = self._stats.copy()

        # 计算平均耗时
        if stats["total_queries"] > 0:
            stats["avg_vector_time"] = stats["vector_time_total"] / stats["total_queries"]
            stats["avg_bm25_time"] = stats["bm25_time_total"] / stats["total_queries"]
            stats["avg_fusion_time"] = stats["fusion_time_total"] / stats["total_queries"]
        else:
            stats["avg_vector_time"] = 0.0
            stats["avg_bm25_time"] = 0.0
            stats["avg_fusion_time"] = 0.0

        # 计算缓存命中率
        total_cache_queries = stats["cache_hits"] + stats["cache_misses"]
        if total_cache_queries > 0:
            stats["cache_hit_rate"] = stats["cache_hits"] / total_cache_queries
        else:
            stats["cache_hit_rate"] = 0.0

        # 添加缓存信息
        stats["cache_size"] = len(self._cache)
        stats["cache_max_size"] = self.cache_size
        stats["cache_enabled"] = self.enable_cache

        return stats

    def reset_statistics(self) -> None:
        """重置统计信息"""
        self._stats = {
            "total_queries": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "vector_time_total": 0.0,
            "bm25_time_total": 0.0,
            "fusion_time_total": 0.0,
            "timeout_count": 0
        }
        logger.info("Statistics reset")

    def clear_cache(self) -> None:
        """清空缓存"""
        cache_size_before = len(self._cache)
        self._cache.clear()
        logger.info(f"Cache cleared: {cache_size_before} entries removed")

    def get_cache_info(self) -> Dict[str, any]:
        """
        获取缓存信息

        Returns:
            缓存信息字典
        """
        return {
            "enabled": self.enable_cache,
            "current_size": len(self._cache),
            "max_size": self.cache_size,
            "ttl_seconds": self._cache_ttl,
            "entries": [
                {
                    "key": key,
                    "result_count": len(results),
                    "age_seconds": time.time() - timestamp
                }
                for key, (results, timestamp) in self._cache.items()
            ]
        }


# 全局单例
_hybrid_retriever_instance: Optional[HybridRetriever] = None


def get_hybrid_retriever(
    vector_retriever: VectorRetriever = None,
    bm25_retriever: BM25Retriever = None,
    retrieval_config: RetrievalConfig = None,
    hybrid_config: HybridConfig = None,
    force_new: bool = False
) -> HybridRetriever:
    """
    获取混合检索器单例

    Args:
        vector_retriever: 向量检索器实例
        bm25_retriever: BM25 检索器实例
        retrieval_config: 检索配置
        hybrid_config: 混合检索配置
        force_new: 是否强制创建新实例

    Returns:
        HybridRetriever 实例

    Raises:
        InvalidConfigError: 如果未提供必需的检索器实例
    """
    global _hybrid_retriever_instance

    if force_new or _hybrid_retriever_instance is None:
        if vector_retriever is None or bm25_retriever is None:
            raise InvalidConfigError(
                "vector_retriever and bm25_retriever are required for HybridRetriever"
            )

        _hybrid_retriever_instance = HybridRetriever(
            vector_retriever,
            bm25_retriever,
            retrieval_config,
            hybrid_config
        )

    return _hybrid_retriever_instance
