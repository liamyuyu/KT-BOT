"""
性能对比测试：开启/关闭重排序的性能差异
"""
import asyncio
import logging
import time
from pathlib import Path
import sys
from typing import List

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.api.services.chat_service import ChatService
from src.api.schemas.chat import ChatRequest, RetrievedContext

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PerformanceStats:
    """性能统计"""

    def __init__(self, name: str):
        self.name = name
        self.times: List[float] = []
        self.result_counts: List[int] = []

    def add(self, elapsed_time: float, result_count: int):
        self.times.append(elapsed_time)
        self.result_counts.append(result_count)

    @property
    def avg_time(self) -> float:
        return sum(self.times) / len(self.times) if self.times else 0

    @property
    def min_time(self) -> float:
        return min(self.times) if self.times else 0

    @property
    def max_time(self) -> float:
        return max(self.times) if self.times else 0

    @property
    def avg_results(self) -> float:
        return sum(self.result_counts) / len(self.result_counts) if self.result_counts else 0

    def summary(self) -> str:
        return (
            f"{self.name}:\n"
            f"  平均耗时: {self.avg_time * 1000:.1f}ms\n"
            f"  最小耗时: {self.min_time * 1000:.1f}ms\n"
            f"  最大耗时: {self.max_time * 1000:.1f}ms\n"
            f"  平均结果数: {self.avg_results:.1f}"
        )


async def benchmark_retrieval(
    chat_service: ChatService,
    query: str,
    top_k: int,
    retrieval_method: str,
    enable_reranking: bool,
    rerank_top_k: int,
    runs: int = 3
) -> PerformanceStats:
    """
    基准测试：多次运行检索并统计性能

    Args:
        chat_service: ChatService 实例
        query: 查询文本
        top_k: 返回结果数量
        retrieval_method: 检索方法
        enable_reranking: 是否启用重排序
        rerank_top_k: 重排序候选数量
        runs: 运行次数

    Returns:
        性能统计
    """
    stats = PerformanceStats(
        f"{retrieval_method} + {'Rerank' if enable_reranking else 'No Rerank'}"
    )

    for i in range(runs):
        start_time = time.time()

        contexts = await chat_service._retrieve_contexts(
            query=query,
            top_k=top_k,
            retrieval_method=retrieval_method,
            enable_reranking=enable_reranking,
            rerank_top_k=rerank_top_k if enable_reranking else top_k
        )

        elapsed_time = time.time() - start_time
        result_count = len(contexts) if contexts else 0

        stats.add(elapsed_time, result_count)

        logger.debug(
            f"  Run {i+1}/{runs}: {elapsed_time * 1000:.1f}ms, {result_count} results"
        )

    return stats


async def test_reranking_performance():
    """测试重排序性能影响"""
    logger.info("=" * 80)
    logger.info("重排序性能对比测试")
    logger.info("=" * 80)

    # 初始化 ChatService
    logger.info("\n初始化 ChatService...")
    chat_service = ChatService()
    logger.info("✓ ChatService 初始化完成")

    # 测试配置
    test_queries = [
        "如何配置 Jira API Token？",
        "RAG 检索系统的实现原理是什么？",
        "ChromaDB 向量数据库如何使用？",
        "如何实现混合检索？",
        "Cross-Encoder 重排序的作用是什么？"
    ]

    top_k = 5
    rerank_top_k = 20  # 重排序前召回更多候选
    runs_per_query = 3  # 每个查询运行3次取平均

    # 测试场景
    scenarios = [
        ("vector", False),   # 向量检索，不重排序
        ("vector", True),    # 向量检索，重排序
        ("bm25", False),     # BM25 检索，不重排序
        ("bm25", True),      # BM25 检索，重排序
        ("hybrid", False),   # 混合检索，不重排序
        ("hybrid", True),    # 混合检索，重排序
    ]

    # 收集所有场景的统计
    all_stats = {}

    for retrieval_method, enable_reranking in scenarios:
        scenario_name = f"{retrieval_method} + {'Rerank' if enable_reranking else 'No Rerank'}"
        logger.info(f"\n{'=' * 80}")
        logger.info(f"测试场景: {scenario_name}")
        logger.info(f"{'=' * 80}")

        scenario_stats = PerformanceStats(scenario_name)

        for i, query in enumerate(test_queries, 1):
            logger.info(f"\n查询 {i}/{len(test_queries)}: {query}")

            stats = await benchmark_retrieval(
                chat_service=chat_service,
                query=query,
                top_k=top_k,
                retrieval_method=retrieval_method,
                enable_reranking=enable_reranking,
                rerank_top_k=rerank_top_k,
                runs=runs_per_query
            )

            # 合并到场景统计
            scenario_stats.times.extend(stats.times)
            scenario_stats.result_counts.extend(stats.result_counts)

            logger.info(f"  平均: {stats.avg_time * 1000:.1f}ms")

        all_stats[scenario_name] = scenario_stats

    # 输出对比结果
    logger.info(f"\n{'=' * 80}")
    logger.info("性能对比总结")
    logger.info(f"{'=' * 80}")

    for scenario_name, stats in all_stats.items():
        logger.info(f"\n{stats.summary()}")

    # 计算重排序的性能开销
    logger.info(f"\n{'=' * 80}")
    logger.info("重排序性能开销分析")
    logger.info(f"{'=' * 80}")

    for method in ["vector", "bm25", "hybrid"]:
        no_rerank_key = f"{method} + No Rerank"
        rerank_key = f"{method} + Rerank"

        if no_rerank_key in all_stats and rerank_key in all_stats:
            no_rerank_time = all_stats[no_rerank_key].avg_time
            rerank_time = all_stats[rerank_key].avg_time
            overhead = rerank_time - no_rerank_time
            overhead_pct = (overhead / no_rerank_time * 100) if no_rerank_time > 0 else 0

            logger.info(f"\n{method.upper()}:")
            logger.info(f"  不重排序: {no_rerank_time * 1000:.1f}ms")
            logger.info(f"  重排序:   {rerank_time * 1000:.1f}ms")
            logger.info(f"  开销:     +{overhead * 1000:.1f}ms (+{overhead_pct:.1f}%)")

    # 推荐配置
    logger.info(f"\n{'=' * 80}")
    logger.info("推荐配置")
    logger.info(f"{'=' * 80}")

    # 找到最快的配置
    fastest = min(all_stats.items(), key=lambda x: x[1].avg_time)
    logger.info(f"\n最快配置: {fastest[0]}")
    logger.info(f"平均耗时: {fastest[1].avg_time * 1000:.1f}ms")

    # 找到最准确的配置（假设重排序更准确）
    most_accurate = [(k, v) for k, v in all_stats.items() if "Rerank" in k]
    if most_accurate:
        best_accurate = min(most_accurate, key=lambda x: x[1].avg_time)
        logger.info(f"\n最佳平衡配置（准确性 + 性能）: {best_accurate[0]}")
        logger.info(f"平均耗时: {best_accurate[1].avg_time * 1000:.1f}ms")

    logger.info(f"\n建议:")
    logger.info(f"  - 低延迟场景（<100ms）: 使用 vector + 不重排序")
    logger.info(f"  - 平衡场景（100-300ms）: 使用 hybrid + 重排序（候选数10-20）")
    logger.info(f"  - 高准确性场景（>300ms）: 使用 hybrid + 重排序（候选数20-50）")

    logger.info(f"\n{'=' * 80}")
    logger.info("测试完成")
    logger.info(f"{'=' * 80}")


if __name__ == "__main__":
    asyncio.run(test_reranking_performance())
