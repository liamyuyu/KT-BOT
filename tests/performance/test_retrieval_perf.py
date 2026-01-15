"""
Performance Tests for Retrieval System
检索系统性能测试脚本
"""

import asyncio
import time
import json
import statistics
from typing import List, Dict, Any
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(level=logging.WARNING)

from src.core.rag import (
    Chunk,
    BM25Retriever,
    VectorRetriever,
    HybridRetriever,
    RetrievalConfig,
    BM25Config,
    HybridConfig
)


class PerformanceTestRunner:
    """性能测试运行器"""

    def __init__(self, output_dir: str = "./tests/performance/results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results = []

    def generate_test_documents(self, count: int) -> List[Chunk]:
        """生成测试文档"""
        documents = []
        content_templates = [
            "Python 是一种广泛使用的高级编程语言，具有简洁的语法和强大的功能库。",
            "机器学习是人工智能的一个重要分支，通过算法让计算机从数据中学习模式。",
            "自然语言处理技术可以让计算机理解和生成人类语言，应用非常广泛。",
            "深度学习使用神经网络模型，在图像识别、语音识别等领域取得了突破性进展。",
            "数据科学结合统计学、计算机科学和领域知识，从数据中提取有价值的洞察。",
            "云计算提供按需访问的计算资源，极大地降低了企业的 IT 基础设施成本。",
            "区块链技术提供去中心化的分布式账本，在金融科技领域有广泛应用前景。",
            "人工智能正在改变各行各业，从医疗诊断到自动驾驶都有重要应用。",
            "软件工程强调系统化、规范化的软件开发方法，以提高软件质量和开发效率。",
            "敏捷开发方法论强调快速迭代和持续交付，已成为现代软件开发的主流方式。"
        ]

        for i in range(count):
            content = content_templates[i % len(content_templates)]
            # 添加索引号以保证内容唯一性
            content = f"[Doc {i}] {content} 文档编号：{i}"

            doc = Chunk(
                chunk_id=f"doc{i}_chunk_0",
                parent_id=f"doc{i}",
                content=content,
                chunk_index=0,
                start_index=0,
                end_index=len(content),
                metadata={"source": "perf_test", "doc_num": i}
            )
            documents.append(doc)

        return documents

    async def test_bm25_performance(self, document_counts: List[int]) -> Dict[str, Any]:
        """
        测试 BM25 检索性能

        Args:
            document_counts: 测试的文档数量列表

        Returns:
            性能测试结果
        """
        print("\n=== BM25 Retriever Performance Test ===")
        results = {
            "retriever": "BM25",
            "tests": []
        }

        test_queries = [
            "Python 编程语言",
            "机器学习算法",
            "深度学习神经网络",
            "自然语言处理",
            "数据科学分析"
        ]

        for doc_count in document_counts:
            print(f"\nTesting with {doc_count} documents...")

            # 生成文档
            documents = self.generate_test_documents(doc_count)

            # 初始化检索器
            retriever = BM25Retriever(
                retrieval_config=RetrievalConfig(top_k=20),
                bm25_config=BM25Config(k1=1.5, b=0.75)
            )

            # 测试索引时间
            index_start = time.time()
            retriever.index_documents(documents)
            index_time = time.time() - index_start

            # 测试单次检索延迟
            latencies = []
            for query in test_queries:
                query_start = time.time()
                results_list = await retriever.retrieve(query, top_k=20)
                latency = (time.time() - query_start) * 1000  # 转换为毫秒
                latencies.append(latency)

            # 统计结果
            test_result = {
                "document_count": doc_count,
                "index_time_seconds": round(index_time, 3),
                "latency_ms": {
                    "mean": round(statistics.mean(latencies), 2),
                    "median": round(statistics.median(latencies), 2),
                    "p95": round(statistics.quantiles(latencies, n=20)[18], 2) if len(latencies) >= 20 else round(max(latencies), 2),
                    "min": round(min(latencies), 2),
                    "max": round(max(latencies), 2)
                },
                "queries_tested": len(test_queries)
            }

            results["tests"].append(test_result)

            print(f"  Index time: {test_result['index_time_seconds']:.3f}s")
            print(f"  Mean latency: {test_result['latency_ms']['mean']:.2f}ms")
            print(f"  P95 latency: {test_result['latency_ms']['p95']:.2f}ms")

        return results

    async def test_hybrid_performance(self, document_counts: List[int]) -> Dict[str, Any]:
        """
        测试混合检索性能

        Args:
            document_counts: 测试的文档数量列表

        Returns:
            性能测试结果
        """
        print("\n=== Hybrid Retriever Performance Test ===")
        results = {
            "retriever": "Hybrid",
            "tests": []
        }

        test_queries = [
            "Python 编程语言",
            "机器学习算法",
            "深度学习神经网络",
            "自然语言处理",
            "数据科学分析"
        ]

        for doc_count in document_counts:
            print(f"\nTesting with {doc_count} documents...")

            # 生成文档
            documents = self.generate_test_documents(doc_count)

            # 初始化 BM25 检索器（向量检索器需要实际的向量数据库，此处用 BM25 模拟）
            bm25_retriever = BM25Retriever(
                retrieval_config=RetrievalConfig(top_k=20),
                bm25_config=BM25Config(k1=1.5, b=0.75)
            )
            bm25_retriever.index_documents(documents)

            # 创建一个模拟的向量检索器（使用 BM25 代替）
            vector_retriever = BM25Retriever(
                retrieval_config=RetrievalConfig(top_k=20),
                bm25_config=BM25Config(k1=1.2, b=0.5)
            )
            vector_retriever.index_documents(documents)

            # 初始化混合检索器
            hybrid_retriever = HybridRetriever(
                vector_retriever=vector_retriever,
                bm25_retriever=bm25_retriever,
                retrieval_config=RetrievalConfig(top_k=20),
                hybrid_config=HybridConfig(fusion_method="rrf", rrf_k=60),
                enable_cache=True,
                cache_size=128,
                retrieval_timeout=10.0
            )

            # 测试单次检索延迟（无缓存）
            latencies_no_cache = []
            for query in test_queries:
                hybrid_retriever.clear_cache()  # 清除缓存
                query_start = time.time()
                results_list = await hybrid_retriever.retrieve(query, top_k=20)
                latency = (time.time() - query_start) * 1000
                latencies_no_cache.append(latency)

            # 测试缓存命中性能
            latencies_with_cache = []
            for query in test_queries:
                # 第一次查询（缓存miss）
                await hybrid_retriever.retrieve(query, top_k=20)
                # 第二次查询（缓存hit）
                query_start = time.time()
                results_list = await hybrid_retriever.retrieve(query, top_k=20)
                latency = (time.time() - query_start) * 1000
                latencies_with_cache.append(latency)

            # 获取统计信息
            stats = hybrid_retriever.get_statistics()

            # 统计结果
            test_result = {
                "document_count": doc_count,
                "latency_no_cache_ms": {
                    "mean": round(statistics.mean(latencies_no_cache), 2),
                    "median": round(statistics.median(latencies_no_cache), 2),
                    "p95": round(statistics.quantiles(latencies_no_cache, n=20)[18], 2) if len(latencies_no_cache) >= 20 else round(max(latencies_no_cache), 2),
                    "min": round(min(latencies_no_cache), 2),
                    "max": round(max(latencies_no_cache), 2)
                },
                "latency_with_cache_ms": {
                    "mean": round(statistics.mean(latencies_with_cache), 2),
                    "median": round(statistics.median(latencies_with_cache), 2),
                    "min": round(min(latencies_with_cache), 2),
                    "max": round(max(latencies_with_cache), 2)
                },
                "cache_hit_rate": round(stats["cache_hit_rate"], 3),
                "avg_vector_time_ms": round(stats["avg_vector_time"] * 1000, 2),
                "avg_bm25_time_ms": round(stats["avg_bm25_time"] * 1000, 2),
                "avg_fusion_time_ms": round(stats["avg_fusion_time"] * 1000, 2),
                "queries_tested": len(test_queries)
            }

            results["tests"].append(test_result)

            print(f"  Mean latency (no cache): {test_result['latency_no_cache_ms']['mean']:.2f}ms")
            print(f"  Mean latency (with cache): {test_result['latency_with_cache_ms']['mean']:.2f}ms")
            print(f"  Cache hit rate: {test_result['cache_hit_rate']:.1%}")
            print(f"  Avg vector time: {test_result['avg_vector_time_ms']:.2f}ms")
            print(f"  Avg BM25 time: {test_result['avg_bm25_time_ms']:.2f}ms")
            print(f"  Avg fusion time: {test_result['avg_fusion_time_ms']:.2f}ms")

        return results

    async def test_concurrent_queries(self, document_count: int, concurrent_users: List[int]) -> Dict[str, Any]:
        """
        测试并发查询性能

        Args:
            document_count: 文档数量
            concurrent_users: 并发用户数列表

        Returns:
            性能测试结果
        """
        print("\n=== Concurrent Query Performance Test ===")
        results = {
            "test": "Concurrent Queries",
            "document_count": document_count,
            "tests": []
        }

        # 准备测试数据
        documents = self.generate_test_documents(document_count)

        bm25_retriever = BM25Retriever(
            retrieval_config=RetrievalConfig(top_k=20),
            bm25_config=BM25Config()
        )
        bm25_retriever.index_documents(documents)

        vector_retriever = BM25Retriever(
            retrieval_config=RetrievalConfig(top_k=20),
            bm25_config=BM25Config()
        )
        vector_retriever.index_documents(documents)

        hybrid_retriever = HybridRetriever(
            vector_retriever=vector_retriever,
            bm25_retriever=bm25_retriever,
            retrieval_config=RetrievalConfig(top_k=20),
            hybrid_config=HybridConfig(fusion_method="rrf"),
            enable_cache=True
        )

        test_queries = [
            "Python 编程",
            "机器学习",
            "深度学习",
            "自然语言处理",
            "数据科学",
            "云计算技术",
            "区块链应用",
            "人工智能",
            "软件工程",
            "敏捷开发"
        ]

        for concurrent_count in concurrent_users:
            print(f"\nTesting with {concurrent_count} concurrent users...")

            # 准备并发查询任务
            async def run_query(query_id: int):
                query = test_queries[query_id % len(test_queries)]
                start = time.time()
                await hybrid_retriever.retrieve(query, top_k=20)
                return time.time() - start

            # 执行并发查询
            start_time = time.time()
            latencies = await asyncio.gather(*[run_query(i) for i in range(concurrent_count)])
            total_time = time.time() - start_time

            # 转换为毫秒
            latencies_ms = [l * 1000 for l in latencies]

            # 统计结果
            test_result = {
                "concurrent_users": concurrent_count,
                "total_queries": concurrent_count,
                "total_time_seconds": round(total_time, 3),
                "throughput_qps": round(concurrent_count / total_time, 2),
                "latency_ms": {
                    "mean": round(statistics.mean(latencies_ms), 2),
                    "median": round(statistics.median(latencies_ms), 2),
                    "p95": round(statistics.quantiles(latencies_ms, n=20)[18], 2) if len(latencies_ms) >= 20 else round(max(latencies_ms), 2),
                    "min": round(min(latencies_ms), 2),
                    "max": round(max(latencies_ms), 2)
                }
            }

            results["tests"].append(test_result)

            print(f"  Total time: {test_result['total_time_seconds']:.3f}s")
            print(f"  Throughput: {test_result['throughput_qps']:.2f} queries/second")
            print(f"  Mean latency: {test_result['latency_ms']['mean']:.2f}ms")
            print(f"  P95 latency: {test_result['latency_ms']['p95']:.2f}ms")

        return results

    def save_results(self, all_results: List[Dict[str, Any]], filename: str = "performance_report.json"):
        """保存测试结果到文件"""
        output_file = self.output_dir / filename
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)

        print(f"\n\nResults saved to: {output_file}")

    def generate_markdown_report(self, all_results: List[Dict[str, Any]], filename: str = "performance_report.md"):
        """生成 Markdown 格式的性能报告"""
        output_file = self.output_dir / filename

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Retrieval System Performance Test Report\n\n")
            f.write(f"**Generated**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            for result in all_results:
                if "retriever" in result:
                    # BM25 或 Hybrid 测试
                    f.write(f"## {result['retriever']} Retriever Performance\n\n")
                    f.write("| Document Count | Index Time (s) | Mean Latency (ms) | P95 Latency (ms) | Queries |\n")
                    f.write("|----------------|----------------|-------------------|------------------|----------|\n")

                    for test in result["tests"]:
                        doc_count = test["document_count"]
                        if "index_time_seconds" in test:
                            # BM25 test
                            index_time = test["index_time_seconds"]
                            mean_lat = test["latency_ms"]["mean"]
                            p95_lat = test["latency_ms"]["p95"]
                            queries = test["queries_tested"]
                            f.write(f"| {doc_count:,} | {index_time:.3f} | {mean_lat:.2f} | {p95_lat:.2f} | {queries} |\n")
                        else:
                            # Hybrid test
                            mean_lat = test["latency_no_cache_ms"]["mean"]
                            p95_lat = test["latency_no_cache_ms"]["p95"]
                            queries = test["queries_tested"]
                            f.write(f"| {doc_count:,} | N/A | {mean_lat:.2f} | {p95_lat:.2f} | {queries} |\n")

                    f.write("\n")

                    # 如果是 Hybrid，添加详细信息
                    if result["retriever"] == "Hybrid":
                        f.write("### Hybrid Retriever Breakdown\n\n")
                        f.write("| Document Count | Vector (ms) | BM25 (ms) | Fusion (ms) | Cache Hit Rate |\n")
                        f.write("|----------------|-------------|-----------|-------------|----------------|\n")

                        for test in result["tests"]:
                            doc_count = test["document_count"]
                            vector_time = test["avg_vector_time_ms"]
                            bm25_time = test["avg_bm25_time_ms"]
                            fusion_time = test["avg_fusion_time_ms"]
                            cache_rate = test["cache_hit_rate"]
                            f.write(f"| {doc_count:,} | {vector_time:.2f} | {bm25_time:.2f} | {fusion_time:.2f} | {cache_rate:.1%} |\n")

                        f.write("\n")

                elif result["test"] == "Concurrent Queries":
                    # 并发测试
                    f.write(f"## Concurrent Query Performance\n\n")
                    f.write(f"**Document Count**: {result['document_count']:,}\n\n")
                    f.write("| Concurrent Users | Throughput (QPS) | Mean Latency (ms) | P95 Latency (ms) |\n")
                    f.write("|------------------|------------------|-------------------|------------------|\n")

                    for test in result["tests"]:
                        users = test["concurrent_users"]
                        throughput = test["throughput_qps"]
                        mean_lat = test["latency_ms"]["mean"]
                        p95_lat = test["latency_ms"]["p95"]
                        f.write(f"| {users} | {throughput:.2f} | {mean_lat:.2f} | {p95_lat:.2f} |\n")

                    f.write("\n")

        print(f"Markdown report saved to: {output_file}")


async def main():
    """主测试函数"""
    runner = PerformanceTestRunner()

    # 测试配置
    document_counts = [100, 500, 1000, 5000]  # 文档数量
    concurrent_users = [1, 5, 10, 20]  # 并发用户数

    all_results = []

    # 测试 BM25
    bm25_results = await runner.test_bm25_performance(document_counts)
    all_results.append(bm25_results)

    # 测试 Hybrid
    hybrid_results = await runner.test_hybrid_performance(document_counts)
    all_results.append(hybrid_results)

    # 测试并发
    concurrent_results = await runner.test_concurrent_queries(
        document_count=1000,
        concurrent_users=concurrent_users
    )
    all_results.append(concurrent_results)

    # 保存结果
    runner.save_results(all_results)
    runner.generate_markdown_report(all_results)

    print("\n✅ Performance tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
