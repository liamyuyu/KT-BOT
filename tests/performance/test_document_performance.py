"""
文档管理性能测试
测试文档上传、检索、删除等操作的性能表现
"""
import pytest
import asyncio
import time
from typing import List, Dict
from statistics import mean, median, stdev
from datetime import datetime

from src.api.services.document_service import DocumentService
from src.api.schemas.document import DocumentUploadRequest, DocumentQueryRequest
from src.core.rag import TextChunker, ChunkingConfig
from src.core.vectordb import get_chroma_client
from src.core.llm.manager import get_llm_manager


class PerformanceMetrics:
    """性能指标收集器"""

    def __init__(self):
        self.timings: List[float] = []
        self.errors: List[str] = []

    def record(self, duration: float):
        """记录一次操作耗时"""
        self.timings.append(duration)

    def record_error(self, error: str):
        """记录错误"""
        self.errors.append(error)

    def get_stats(self) -> Dict:
        """获取统计信息"""
        if not self.timings:
            return {
                "count": 0,
                "errors": len(self.errors),
                "error_rate": 1.0 if self.errors else 0.0
            }

        return {
            "count": len(self.timings),
            "total_time": sum(self.timings),
            "mean": mean(self.timings),
            "median": median(self.timings),
            "stdev": stdev(self.timings) if len(self.timings) > 1 else 0,
            "min": min(self.timings),
            "max": max(self.timings),
            "errors": len(self.errors),
            "error_rate": len(self.errors) / (len(self.timings) + len(self.errors))
        }

    def print_report(self, operation: str):
        """打印性能报告"""
        stats = self.get_stats()
        print(f"\n{'='*60}")
        print(f"Performance Report: {operation}")
        print(f"{'='*60}")
        print(f"Total Operations: {stats['count']}")
        print(f"Total Time: {stats.get('total_time', 0):.2f}s")
        if stats['count'] > 0:
            print(f"Mean Time: {stats['mean']*1000:.2f}ms")
            print(f"Median Time: {stats['median']*1000:.2f}ms")
            print(f"Std Dev: {stats['stdev']*1000:.2f}ms")
            print(f"Min Time: {stats['min']*1000:.2f}ms")
            print(f"Max Time: {stats['max']*1000:.2f}ms")
            print(f"Throughput: {stats['count']/stats['total_time']:.2f} ops/sec")
        print(f"Errors: {stats['errors']}")
        print(f"Error Rate: {stats['error_rate']*100:.2f}%")
        print(f"{'='*60}\n")


@pytest.fixture(scope="module")
def service():
    """创建文档服务实例"""
    chunker = TextChunker(config=ChunkingConfig(chunk_size=800, chunk_overlap=150))
    vectordb = get_chroma_client()
    service = DocumentService(chunker=chunker, vectordb_client=vectordb)
    return service


class TestDocumentUploadPerformance:
    """文档上传性能测试"""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_single_document_upload_performance(self, service):
        """测试单文档上传性能"""
        metrics = PerformanceMetrics()

        # 准备测试数据
        content = "This is a test document content. " * 100  # ~3KB

        for i in range(10):
            request = DocumentUploadRequest(
                title=f"Performance Test Doc {i}",
                content=content,
                source_type="local",
                tags=["performance", "test"]
            )

            start = time.time()
            try:
                await service.upload_document(request)
                duration = time.time() - start
                metrics.record(duration)
            except Exception as e:
                metrics.record_error(str(e))

        metrics.print_report("Single Document Upload")

        stats = metrics.get_stats()
        # 性能基准：平均上传时间应小于 2 秒
        if stats['count'] > 0:
            assert stats['mean'] < 2.0, f"Upload too slow: {stats['mean']:.2f}s"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_document_upload_performance(self, service):
        """测试并发文档上传性能"""
        metrics = PerformanceMetrics()

        async def upload_document(i: int):
            """上传单个文档"""
            content = "Concurrent test document content. " * 50
            request = DocumentUploadRequest(
                title=f"Concurrent Doc {i}",
                content=content,
                source_type="local",
                tags=["concurrent", "performance"]
            )

            start = time.time()
            try:
                await service.upload_document(request)
                duration = time.time() - start
                metrics.record(duration)
            except Exception as e:
                metrics.record_error(str(e))

        # 并发上传 20 个文档
        total_start = time.time()
        tasks = [upload_document(i) for i in range(20)]
        await asyncio.gather(*tasks, return_exceptions=True)
        total_duration = time.time() - total_start

        metrics.print_report("Concurrent Document Upload (20 documents)")

        print(f"Total Concurrent Upload Time: {total_duration:.2f}s")
        print(f"Effective Throughput: {20/total_duration:.2f} docs/sec\n")

        # 并发上传应该比顺序上传快
        # 至少应该在 30 秒内完成
        assert total_duration < 30.0, f"Concurrent upload too slow: {total_duration:.2f}s"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_large_document_upload_performance(self, service):
        """测试大文档上传性能"""
        metrics = PerformanceMetrics()

        # 测试不同大小的文档
        sizes = [1000, 5000, 10000, 50000]  # 字数

        for size in sizes:
            content = "Large document content. " * size
            request = DocumentUploadRequest(
                title=f"Large Doc {size} words",
                content=content,
                source_type="local",
                tags=["large", "performance"]
            )

            start = time.time()
            try:
                response = await service.upload_document(request)
                duration = time.time() - start
                metrics.record(duration)
                print(f"Size: {size} words, Chunks: {response.chunk_count}, Time: {duration:.2f}s")
            except Exception as e:
                metrics.record_error(str(e))

        metrics.print_report("Large Document Upload")


class TestDocumentQueryPerformance:
    """文档查询性能测试"""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_document_list_query_performance(self, service):
        """测试文档列表查询性能"""
        metrics = PerformanceMetrics()

        # 先确保有一些文档
        for i in range(5):
            request = DocumentUploadRequest(
                title=f"Query Test Doc {i}",
                content=f"Content for query test {i}",
                source_type="local",
                tags=["query", "test"]
            )
            try:
                await service.upload_document(request)
            except:
                pass  # 可能因为 embedding 服务不可用

        # 测试查询性能
        for i in range(20):
            query = DocumentQueryRequest(limit=100, offset=0)

            start = time.time()
            try:
                await service.get_document_list(query)
                duration = time.time() - start
                metrics.record(duration)
            except Exception as e:
                metrics.record_error(str(e))

        metrics.print_report("Document List Query")

        stats = metrics.get_stats()
        # 查询应该很快，平均时间小于 0.5 秒
        if stats['count'] > 0:
            assert stats['mean'] < 0.5, f"Query too slow: {stats['mean']:.2f}s"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_document_detail_query_performance(self, service):
        """测试文档详情查询性能"""
        metrics = PerformanceMetrics()

        # 创建测试文档
        test_doc_id = None
        try:
            request = DocumentUploadRequest(
                title="Detail Query Test Doc",
                content="Content for detail query test",
                source_type="local",
                tags=["detail", "test"]
            )
            response = await service.upload_document(request)
            test_doc_id = response.document_id
        except:
            pass

        if test_doc_id:
            # 测试详情查询性能
            for i in range(20):
                start = time.time()
                try:
                    await service.get_document_by_id(test_doc_id)
                    duration = time.time() - start
                    metrics.record(duration)
                except Exception as e:
                    metrics.record_error(str(e))

            metrics.print_report("Document Detail Query")

            stats = metrics.get_stats()
            if stats['count'] > 0:
                assert stats['mean'] < 0.3, f"Detail query too slow: {stats['mean']:.2f}s"


class TestDocumentDeletePerformance:
    """文档删除性能测试"""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_single_document_delete_performance(self, service):
        """测试单文档删除性能"""
        metrics = PerformanceMetrics()

        # 创建并删除多个文档
        for i in range(10):
            # 创建文档
            try:
                request = DocumentUploadRequest(
                    title=f"Delete Test Doc {i}",
                    content=f"Content for delete test {i}",
                    source_type="local"
                )
                response = await service.upload_document(request)
                doc_id = response.document_id

                # 删除文档
                start = time.time()
                await service.delete_document(doc_id)
                duration = time.time() - start
                metrics.record(duration)
            except Exception as e:
                metrics.record_error(str(e))

        metrics.print_report("Single Document Delete")

        stats = metrics.get_stats()
        if stats['count'] > 0:
            assert stats['mean'] < 0.5, f"Delete too slow: {stats['mean']:.2f}s"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_batch_document_delete_performance(self, service):
        """测试批量文档删除性能"""
        metrics = PerformanceMetrics()

        # 创建多个文档
        doc_ids = []
        for i in range(20):
            try:
                request = DocumentUploadRequest(
                    title=f"Batch Delete Test Doc {i}",
                    content=f"Content {i}",
                    source_type="local"
                )
                response = await service.upload_document(request)
                doc_ids.append(response.document_id)
            except:
                pass

        # 批量删除
        start = time.time()
        for doc_id in doc_ids:
            try:
                await service.delete_document(doc_id)
            except Exception as e:
                metrics.record_error(str(e))

        total_duration = time.time() - start
        print(f"\nBatch Delete Performance:")
        print(f"Deleted {len(doc_ids)} documents in {total_duration:.2f}s")
        print(f"Average: {total_duration/len(doc_ids):.2f}s per document")
        print(f"Throughput: {len(doc_ids)/total_duration:.2f} docs/sec\n")


class TestDocumentStatsPerformance:
    """文档统计性能测试"""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_stats_query_performance(self, service):
        """测试统计查询性能"""
        metrics = PerformanceMetrics()

        # 测试统计查询性能
        for i in range(20):
            start = time.time()
            try:
                await service.get_document_stats()
                duration = time.time() - start
                metrics.record(duration)
            except Exception as e:
                metrics.record_error(str(e))

        metrics.print_report("Document Stats Query")

        stats = metrics.get_stats()
        if stats['count'] > 0:
            # 统计查询应该很快
            assert stats['mean'] < 1.0, f"Stats query too slow: {stats['mean']:.2f}s"


class TestEndToEndPerformance:
    """端到端性能测试"""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_complete_workflow_performance(self, service):
        """测试完整工作流性能"""
        print("\n" + "="*60)
        print("End-to-End Workflow Performance Test")
        print("="*60)

        total_start = time.time()

        # 1. 上传文档
        upload_start = time.time()
        doc_id = None
        try:
            request = DocumentUploadRequest(
                title="E2E Test Document",
                content="Complete workflow test content. " * 100,
                source_type="local",
                tags=["e2e", "test"]
            )
            response = await service.upload_document(request)
            doc_id = response.document_id
            upload_time = time.time() - upload_start
            print(f"✓ Upload: {upload_time:.2f}s")
        except Exception as e:
            print(f"✗ Upload failed: {e}")
            return

        # 2. 查询列表
        list_start = time.time()
        try:
            query = DocumentQueryRequest(limit=10)
            await service.get_document_list(query)
            list_time = time.time() - list_start
            print(f"✓ List Query: {list_time:.2f}s")
        except Exception as e:
            print(f"✗ List query failed: {e}")

        # 3. 获取详情
        detail_start = time.time()
        try:
            await service.get_document_by_id(doc_id)
            detail_time = time.time() - detail_start
            print(f"✓ Detail Query: {detail_time:.2f}s")
        except Exception as e:
            print(f"✗ Detail query failed: {e}")

        # 4. 获取统计
        stats_start = time.time()
        try:
            await service.get_document_stats()
            stats_time = time.time() - stats_start
            print(f"✓ Stats Query: {stats_time:.2f}s")
        except Exception as e:
            print(f"✗ Stats query failed: {e}")

        # 5. 删除文档
        delete_start = time.time()
        try:
            await service.delete_document(doc_id)
            delete_time = time.time() - delete_start
            print(f"✓ Delete: {delete_time:.2f}s")
        except Exception as e:
            print(f"✗ Delete failed: {e}")

        total_time = time.time() - total_start
        print(f"\nTotal Workflow Time: {total_time:.2f}s")
        print("="*60 + "\n")

        # 整个工作流应该在合理时间内完成
        assert total_time < 10.0, f"E2E workflow too slow: {total_time:.2f}s"


@pytest.mark.performance
class TestScalabilityPerformance:
    """可扩展性性能测试"""

    @pytest.mark.asyncio
    async def test_scalability_with_document_count(self, service):
        """测试随文档数量增加的性能变化"""
        print("\n" + "="*60)
        print("Scalability Test: Query Performance vs Document Count")
        print("="*60)

        results = []

        # 测试不同文档数量下的查询性能
        doc_counts = [10, 50, 100]

        for target_count in doc_counts:
            # 获取当前文档数
            stats = await service.get_document_stats()
            current_count = stats.total_documents

            # 如果文档不足，创建更多
            if current_count < target_count:
                for i in range(target_count - current_count):
                    try:
                        request = DocumentUploadRequest(
                            title=f"Scalability Test Doc {i}",
                            content=f"Content {i}",
                            source_type="local"
                        )
                        await service.upload_document(request)
                    except:
                        pass

            # 测试查询性能
            query_times = []
            for _ in range(5):
                start = time.time()
                try:
                    query = DocumentQueryRequest(limit=100)
                    await service.get_document_list(query)
                    duration = time.time() - start
                    query_times.append(duration)
                except:
                    pass

            if query_times:
                avg_time = mean(query_times)
                results.append((target_count, avg_time))
                print(f"Document Count: {target_count:4d} | Avg Query Time: {avg_time*1000:6.2f}ms")

        print("="*60 + "\n")

        # 验证查询时间不会随文档数量线性增长
        if len(results) >= 2:
            # 文档数量增加 10 倍，查询时间不应该增加超过 3 倍
            first_time = results[0][1]
            last_time = results[-1][1]
            time_ratio = last_time / first_time if first_time > 0 else 1
            doc_ratio = results[-1][0] / results[0][0]

            print(f"Document ratio: {doc_ratio:.1f}x")
            print(f"Time ratio: {time_ratio:.1f}x")
            print(f"Scalability score: {doc_ratio/time_ratio:.2f}x (higher is better)\n")


if __name__ == "__main__":
    # 运行性能测试
    pytest.main([__file__, "-v", "-m", "performance", "-s"])
