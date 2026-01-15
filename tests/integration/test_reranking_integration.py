"""
Integration Tests for Complete Retrieval Flow with Reranking
完整检索流程集成测试（包含重排序）
"""

import pytest
import asyncio
from typing import List

from src.core.rag import (
    TextChunker,
    RetrievalResult,
    RetrievalConfig,
    HybridConfig,
    RerankerConfig,
    CrossEncoderReranker,
    get_reranker
)
from src.core.rag.retriever.vector import VectorRetriever
from src.core.rag.retriever.bm25 import BM25Retriever
from src.core.rag.retriever.hybrid import HybridRetriever
from src.core.vectordb import ChromaDBClient, get_chroma_client, Document
from src.core.llm import get_llm_manager


@pytest.fixture
async def setup_documents():
    """创建测试文档集"""
    documents = [
        Document(
            id="doc1",
            content="Python 是一种广泛使用的高级编程语言，以其简洁的语法和强大的功能著称。Python 支持多种编程范式，包括面向对象、命令式、函数式和过程式编程。",
            metadata={
                "issue_key": "TECH-001",
                "project_key": "TECH",
                "issue_type": "技术文档",
                "title": "Python 编程语言介绍"
            }
        ),
        Document(
            id="doc2",
            content="JavaScript 是一种脚本语言，主要用于网页开发和前端交互。它是 Web 开发的核心技术之一，与 HTML 和 CSS 共同构成现代网页的基础。",
            metadata={
                "issue_key": "TECH-002",
                "project_key": "TECH",
                "issue_type": "技术文档",
                "title": "JavaScript 基础"
            }
        ),
        Document(
            id="doc3",
            content="机器学习是人工智能的一个重要分支，让计算机能够从数据中学习模式。常见的机器学习算法包括决策树、神经网络、支持向量机等。",
            metadata={
                "issue_key": "AI-001",
                "project_key": "AI",
                "issue_type": "技术文档",
                "title": "机器学习入门"
            }
        ),
        Document(
            id="doc4",
            content="深度学习使用多层神经网络来学习数据的层次化表示，在图像识别、自然语言处理等领域表现出色。深度学习模型通常需要大量数据和计算资源。",
            metadata={
                "issue_key": "AI-002",
                "project_key": "AI",
                "issue_type": "技术文档",
                "title": "深度学习概述"
            }
        ),
        Document(
            id="doc5",
            content="自然语言处理技术让计算机能够理解和生成人类语言，应用广泛。NLP 技术包括分词、词性标注、命名实体识别、情感分析等。",
            metadata={
                "issue_key": "AI-003",
                "project_key": "AI",
                "issue_type": "技术文档",
                "title": "自然语言处理技术"
            }
        ),
    ]

    return documents


@pytest.fixture
async def chroma_client():
    """创建 ChromaDB 测试客户端"""
    client = get_chroma_client(
        persist_directory="./data/test_chroma_reranking",
        collection_name="test_reranking_collection"
    )

    # 清空现有数据
    try:
        client.delete_collection()
    except Exception:
        pass

    yield client

    # 清理
    try:
        client.delete_collection()
    except Exception:
        pass


@pytest.fixture
async def indexed_retrievers(setup_documents, chroma_client):
    """创建并索引检索器"""
    documents = setup_documents

    # 1. 分块
    chunker = TextChunker(chunk_size=200, overlap=50)
    all_chunks = []
    for doc in documents:
        chunks = chunker.chunk_document(doc)
        all_chunks.extend(chunks)

    # 2. 生成 embeddings 并索引到 ChromaDB
    llm_manager = get_llm_manager()
    embedding = llm_manager.create_embedding()

    texts = [chunk.content for chunk in all_chunks]
    responses = await embedding.embed_batch(texts)
    embeddings = [resp.embedding for resp in responses]

    # 添加到 ChromaDB
    for chunk, emb in zip(all_chunks, embeddings):
        chroma_client.add_document(
            document_id=chunk.chunk_id,
            content=chunk.content,
            metadata=chunk.metadata,
            embedding=emb
        )

    # 3. 创建检索器
    vector_retriever = VectorRetriever(
        chroma_client=chroma_client,
        embedding_model=embedding,
        config=RetrievalConfig(top_k=10)
    )

    bm25_retriever = BM25Retriever(
        chroma_client=chroma_client,
        config=RetrievalConfig(top_k=10)
    )

    hybrid_retriever = HybridRetriever(
        vector_retriever=vector_retriever,
        bm25_retriever=bm25_retriever,
        retrieval_config=RetrievalConfig(top_k=10),
        hybrid_config=HybridConfig(fusion_method="rrf"),
        enable_cache=True
    )

    return {
        "vector": vector_retriever,
        "bm25": bm25_retriever,
        "hybrid": hybrid_retriever
    }


@pytest.fixture
def reranker():
    """创建重排序器"""
    config = RerankerConfig(
        model_name="BAAI/bge-reranker-base",  # 使用更小的模型进行测试
        batch_size=2,
        normalize_scores=True,
        device="cpu"
    )
    return get_reranker(config)


class TestCompleteRetrievalFlow:
    """测试完整检索流程（检索 + 重排序）"""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_hybrid_retrieval_with_reranking(
        self,
        indexed_retrievers,
        reranker
    ):
        """测试混合检索 + 重排序流程"""
        hybrid_retriever = indexed_retrievers["hybrid"]
        query = "Python 编程语言的特点和用途"

        # 1. 混合检索（获取更多候选）
        candidates = await hybrid_retriever.retrieve(query, top_k=10)
        assert len(candidates) > 0
        assert len(candidates) <= 10

        print(f"\n混合检索结果（{len(candidates)} 个）:")
        for i, result in enumerate(candidates[:5], 1):
            print(f"{i}. {result.chunk_id}: {result.content[:50]}... (score={result.score:.4f})")

        # 2. 应用重排序
        reranked_results = await reranker.rerank(
            query=query,
            documents=candidates,
            top_k=3
        )

        assert len(reranked_results) == 3
        assert all(hasattr(r, "rerank_score") for r in reranked_results)
        assert all(hasattr(r, "original_rank") for r in reranked_results)
        assert all(hasattr(r, "new_rank") for r in reranked_results)

        print(f"\n重排序结果（Top 3）:")
        for i, result in enumerate(reranked_results, 1):
            print(f"{i}. {result.chunk_id}: {result.content[:50]}... ")
            print(f"   原始排名={result.original_rank}, 原始分数={result.original_score:.4f}")
            print(f"   重排序排名={result.new_rank}, 重排序分数={result.rerank_score:.4f}")

        # 3. 验证重排序效果
        # - Python 相关文档应该排在前面
        assert "Python" in reranked_results[0].content

        # - 重排序分数单调递减
        for i in range(len(reranked_results) - 1):
            assert reranked_results[i].rerank_score >= reranked_results[i + 1].rerank_score

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_vector_retrieval_with_reranking(
        self,
        indexed_retrievers,
        reranker
    ):
        """测试向量检索 + 重排序流程"""
        vector_retriever = indexed_retrievers["vector"]
        query = "深度学习和神经网络"

        # 1. 向量检索
        candidates = await vector_retriever.retrieve(query, top_k=10)
        assert len(candidates) > 0

        # 2. 重排序
        reranked_results = await reranker.rerank(query, candidates, top_k=3)

        assert len(reranked_results) == 3

        # 深度学习相关内容应该排在前面
        top_content = " ".join([r.content for r in reranked_results[:2]])
        assert "深度学习" in top_content or "神经网络" in top_content

    @pytest.mark.asyncio
    async def test_reranking_improves_relevance(
        self,
        indexed_retrievers,
        reranker
    ):
        """测试重排序提升相关性"""
        hybrid_retriever = indexed_retrievers["hybrid"]
        query = "机器学习算法有哪些"

        # 1. 混合检索
        candidates = await hybrid_retriever.retrieve(query, top_k=10)

        # 2. 重排序
        reranked_results = await reranker.rerank(query, candidates, top_k=5)

        # 3. 验证：机器学习相关文档应该在重排序后排名靠前
        # 找到包含"机器学习"的文档在原始结果和重排序结果中的位置
        ml_doc_original_rank = None
        ml_doc_new_rank = None

        for i, result in enumerate(candidates):
            if "机器学习" in result.content:
                ml_doc_original_rank = i
                break

        for result in reranked_results:
            if "机器学习" in result.content:
                ml_doc_new_rank = result.new_rank
                break

        if ml_doc_original_rank is not None and ml_doc_new_rank is not None:
            # 重排序应该提升机器学习文档的排名（排名数字变小）
            print(f"\n机器学习文档:")
            print(f"  原始排名: {ml_doc_original_rank}")
            print(f"  重排序后排名: {ml_doc_new_rank}")
            assert ml_doc_new_rank <= ml_doc_original_rank

    @pytest.mark.asyncio
    async def test_reranking_without_candidates(self, reranker):
        """测试空候选列表的重排序"""
        query = "测试查询"
        results = await reranker.rerank(query, [])

        assert results == []

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_reranking_with_different_top_k(
        self,
        indexed_retrievers,
        reranker
    ):
        """测试不同 top_k 参数的重排序"""
        hybrid_retriever = indexed_retrievers["hybrid"]
        query = "编程语言的发展"

        # 检索 10 个候选
        candidates = await hybrid_retriever.retrieve(query, top_k=10)

        # 测试不同的 top_k
        for top_k in [1, 3, 5]:
            results = await reranker.rerank(query, candidates, top_k=top_k)
            assert len(results) == min(top_k, len(candidates))

            # 验证分数单调递减
            for i in range(len(results) - 1):
                assert results[i].rerank_score >= results[i + 1].rerank_score

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_end_to_end_retrieval_pipeline(
        self,
        indexed_retrievers,
        reranker
    ):
        """端到端测试：完整的检索流程"""
        query = "自然语言处理的应用"

        # 步骤 1: 混合检索（召回阶段）
        hybrid_retriever = indexed_retrievers["hybrid"]
        recall_top_k = 10
        candidates = await hybrid_retriever.retrieve(query, top_k=recall_top_k)

        assert len(candidates) > 0
        print(f"\n[召回阶段] 混合检索召回 {len(candidates)} 个候选")

        # 步骤 2: 重排序（精排阶段）
        final_top_k = 3
        final_results = await reranker.rerank(
            query=query,
            documents=candidates,
            top_k=final_top_k
        )

        assert len(final_results) == final_top_k
        print(f"\n[精排阶段] 重排序后返回 Top {final_top_k} 结果:")

        for i, result in enumerate(final_results, 1):
            print(f"\n排名 {i}:")
            print(f"  ID: {result.chunk_id}")
            print(f"  内容: {result.content[:100]}...")
            print(f"  原始分数: {result.original_score:.4f} (排名 {result.original_rank})")
            print(f"  重排序分数: {result.rerank_score:.4f}")
            print(f"  元数据: {result.metadata.get('title', 'N/A')}")

        # 验证：
        # 1. 分数归一化到 0-1
        assert all(0.0 <= r.rerank_score <= 1.0 for r in final_results)

        # 2. 分数单调递减
        for i in range(len(final_results) - 1):
            assert final_results[i].rerank_score >= final_results[i + 1].rerank_score

        # 3. NLP 相关内容应该排在靠前位置
        top_2_content = " ".join([r.content for r in final_results[:2]])
        assert "自然语言处理" in top_2_content or "NLP" in top_2_content


class TestRetrievalPerformanceComparison:
    """测试检索性能对比（有/无重排序）"""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_performance_with_and_without_reranking(
        self,
        indexed_retrievers,
        reranker
    ):
        """对比有/无重排序的检索性能"""
        import time

        hybrid_retriever = indexed_retrievers["hybrid"]
        query = "Python 和 JavaScript 的区别"

        # 测试 1: 仅混合检索
        start_time = time.time()
        results_no_rerank = await hybrid_retriever.retrieve(query, top_k=3)
        time_no_rerank = time.time() - start_time

        # 测试 2: 混合检索 + 重排序
        start_time = time.time()
        candidates = await hybrid_retriever.retrieve(query, top_k=10)
        results_with_rerank = await reranker.rerank(query, candidates, top_k=3)
        time_with_rerank = time.time() - start_time

        print(f"\n性能对比:")
        print(f"  仅混合检索: {time_no_rerank:.3f}s")
        print(f"  混合检索 + 重排序: {time_with_rerank:.3f}s")
        print(f"  重排序开销: {time_with_rerank - time_no_rerank:.3f}s")

        print(f"\n结果对比:")
        print(f"  无重排序 Top 3:")
        for i, r in enumerate(results_no_rerank[:3], 1):
            print(f"    {i}. {r.chunk_id}: score={r.score:.4f}")

        print(f"\n  有重排序 Top 3:")
        for i, r in enumerate(results_with_rerank[:3], 1):
            print(f"    {i}. {r.chunk_id}: rerank_score={r.rerank_score:.4f} (原始排名={r.original_rank})")

        # 验证：重排序后的结果应该更相关
        # 这里我们验证 Python 和 JavaScript 相关内容是否都出现在结果中
        all_content_with_rerank = " ".join([r.content for r in results_with_rerank])

        # 至少应该包含其中一个语言
        assert "Python" in all_content_with_rerank or "JavaScript" in all_content_with_rerank


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "not slow"])
