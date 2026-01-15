"""
Integration Tests for Hybrid Retrieval API Integration
混合检索 API 集成测试
"""

import pytest
import asyncio
from typing import List

from src.api.services.chat_service import ChatService
from src.api.schemas.chat import ChatRequest, ChatResponse
from src.core.rag import (
    Chunk,
    VectorRetriever,
    BM25Retriever,
    HybridRetriever,
    RetrievalConfig,
    BM25Config,
    HybridConfig
)


@pytest.fixture
def sample_documents():
    """测试文档集"""
    return [
        Chunk(
            chunk_id="doc1_chunk_0",
            parent_id="doc1",
            content="Python 是一种广泛使用的编程语言，具有简洁的语法和强大的功能。",
            chunk_index=0,
            start_index=0,
            end_index=35,
            metadata={"issue_key": "DOC-001", "project_key": "DOC", "issue_type": "Story"}
        ),
        Chunk(
            chunk_id="doc2_chunk_0",
            parent_id="doc2",
            content="机器学习是人工智能的一个重要分支，通过算法让计算机从数据中学习。",
            chunk_index=0,
            start_index=0,
            end_index=35,
            metadata={"issue_key": "DOC-002", "project_key": "DOC", "issue_type": "Story"}
        ),
        Chunk(
            chunk_id="doc3_chunk_0",
            parent_id="doc3",
            content="自然语言处理技术可以让计算机理解和生成人类语言，应用广泛。",
            chunk_index=0,
            start_index=0,
            end_index=32,
            metadata={"issue_key": "DOC-003", "project_key": "DOC", "issue_type": "Task"}
        ),
    ]


@pytest.fixture
def chat_service_with_retrievers(sample_documents):
    """初始化带检索器的 ChatService"""
    # 创建检索器
    vector_retriever = BM25Retriever(  # 用 BM25 模拟向量检索
        retrieval_config=RetrievalConfig(top_k=10),
        bm25_config=BM25Config(k1=1.2, b=0.5)
    )
    vector_retriever.index_documents(sample_documents)

    bm25_retriever = BM25Retriever(
        retrieval_config=RetrievalConfig(top_k=10),
        bm25_config=BM25Config(k1=1.5, b=0.75)
    )
    bm25_retriever.index_documents(sample_documents)

    hybrid_retriever = HybridRetriever(
        vector_retriever=vector_retriever,
        bm25_retriever=bm25_retriever,
        retrieval_config=RetrievalConfig(top_k=10),
        hybrid_config=HybridConfig(fusion_method="rrf"),
        enable_cache=True
    )

    # 创建 ChatService（不使用真实 LLM）
    service = ChatService(
        vector_retriever=vector_retriever,
        bm25_retriever=bm25_retriever,
        hybrid_retriever=hybrid_retriever
    )

    return service


class TestHybridRetrievalIntegration:
    """测试混合检索集成"""

    @pytest.mark.asyncio
    async def test_retrieval_method_vector(self, chat_service_with_retrievers):
        """测试纯向量检索"""
        service = chat_service_with_retrievers

        # 测试向量检索
        contexts = await service._retrieve_contexts(
            query="Python 编程语言",
            top_k=3,
            retrieval_method="vector"
        )

        assert len(contexts) > 0
        assert all(ctx.retrieval_method == "vector" for ctx in contexts)
        assert all(hasattr(ctx, 'score') for ctx in contexts)
        assert all(hasattr(ctx, 'distance') for ctx in contexts)

    @pytest.mark.asyncio
    async def test_retrieval_method_bm25(self, chat_service_with_retrievers):
        """测试纯 BM25 检索"""
        service = chat_service_with_retrievers

        # 测试 BM25 检索
        contexts = await service._retrieve_contexts(
            query="机器学习算法",
            top_k=3,
            retrieval_method="bm25"
        )

        assert len(contexts) > 0
        assert all(ctx.retrieval_method == "bm25" for ctx in contexts)
        assert all(hasattr(ctx, 'score') for ctx in contexts)

    @pytest.mark.asyncio
    async def test_retrieval_method_hybrid_rrf(self, chat_service_with_retrievers):
        """测试混合检索 - RRF 融合"""
        service = chat_service_with_retrievers

        # 测试混合检索（RRF）
        contexts = await service._retrieve_contexts(
            query="Python 编程",
            top_k=3,
            retrieval_method="hybrid",
            fusion_method="rrf"
        )

        assert len(contexts) > 0
        assert all(ctx.retrieval_method == "hybrid" for ctx in contexts)
        assert all(hasattr(ctx, 'score') for ctx in contexts)

    @pytest.mark.asyncio
    async def test_retrieval_method_hybrid_weighted(self, chat_service_with_retrievers):
        """测试混合检索 - 加权融合"""
        service = chat_service_with_retrievers

        # 测试混合检索（加权）
        contexts = await service._retrieve_contexts(
            query="机器学习",
            top_k=3,
            retrieval_method="hybrid",
            fusion_method="weighted",
            vector_weight=0.7,
            bm25_weight=0.3
        )

        assert len(contexts) > 0
        assert all(ctx.retrieval_method == "hybrid" for ctx in contexts)
        # 验证权重已应用
        assert service.hybrid_retriever.hybrid_config.fusion_method == "weighted"
        assert service.hybrid_retriever.hybrid_config.vector_weight == 0.7
        assert service.hybrid_retriever.hybrid_config.bm25_weight == 0.3

    @pytest.mark.asyncio
    async def test_retrieval_weight_adjustment(self, chat_service_with_retrievers):
        """测试检索权重动态调整"""
        service = chat_service_with_retrievers

        # 第一次查询：权重 0.8/0.2
        contexts1 = await service._retrieve_contexts(
            query="测试",
            top_k=2,
            retrieval_method="hybrid",
            fusion_method="weighted",
            vector_weight=0.8,
            bm25_weight=0.2
        )

        assert service.hybrid_retriever.hybrid_config.vector_weight == 0.8

        # 第二次查询：权重 0.3/0.7
        contexts2 = await service._retrieve_contexts(
            query="测试",
            top_k=2,
            retrieval_method="hybrid",
            fusion_method="weighted",
            vector_weight=0.3,
            bm25_weight=0.7
        )

        assert service.hybrid_retriever.hybrid_config.vector_weight == 0.3

    @pytest.mark.asyncio
    async def test_different_fusion_methods(self, chat_service_with_retrievers):
        """测试不同融合方法"""
        service = chat_service_with_retrievers
        query = "Python 机器学习"

        # 测试 RRF
        contexts_rrf = await service._retrieve_contexts(
            query=query,
            top_k=3,
            retrieval_method="hybrid",
            fusion_method="rrf"
        )

        # 测试 weighted
        contexts_weighted = await service._retrieve_contexts(
            query=query,
            top_k=3,
            retrieval_method="hybrid",
            fusion_method="weighted",
            vector_weight=0.5,
            bm25_weight=0.5
        )

        # 测试 linear
        contexts_linear = await service._retrieve_contexts(
            query=query,
            top_k=3,
            retrieval_method="hybrid",
            fusion_method="linear",
            vector_weight=0.5,
            bm25_weight=0.5
        )

        # 所有方法都应该返回结果
        assert len(contexts_rrf) > 0
        assert len(contexts_weighted) > 0
        assert len(contexts_linear) > 0

    @pytest.mark.asyncio
    async def test_retrieved_context_format(self, chat_service_with_retrievers):
        """测试检索上下文格式"""
        service = chat_service_with_retrievers

        contexts = await service._retrieve_contexts(
            query="Python",
            top_k=2,
            retrieval_method="hybrid"
        )

        assert len(contexts) > 0

        # 验证上下文格式
        for ctx in contexts:
            assert hasattr(ctx, 'chunk_id')
            assert hasattr(ctx, 'content')
            assert hasattr(ctx, 'score')
            assert hasattr(ctx, 'source')
            assert hasattr(ctx, 'retrieval_method')
            assert hasattr(ctx, 'distance')

            # 验证 source 字段
            assert 'issue_key' in ctx.source
            assert 'project_key' in ctx.source
            assert 'issue_type' in ctx.source

            # 验证检索方法
            assert ctx.retrieval_method == "hybrid"

    @pytest.mark.asyncio
    async def test_empty_query_handling(self, chat_service_with_retrievers):
        """测试空查询处理"""
        service = chat_service_with_retrievers

        # 空查询应该返回空列表
        contexts = await service._retrieve_contexts(
            query="",
            top_k=3,
            retrieval_method="hybrid"
        )

        # 应该捕获异常并返回空列表
        assert contexts == []

    @pytest.mark.asyncio
    async def test_invalid_retrieval_method(self, chat_service_with_retrievers):
        """测试无效的检索方法"""
        service = chat_service_with_retrievers

        # 无效的检索方法应该回退到 vector
        contexts = await service._retrieve_contexts(
            query="测试",
            top_k=2,
            retrieval_method="invalid_method"
        )

        # 应该返回结果（使用默认的 vector 方法）
        assert len(contexts) > 0


class TestChatRequestValidation:
    """测试 ChatRequest 模型验证"""

    def test_chat_request_default_values(self):
        """测试默认值"""
        request = ChatRequest(message="测试消息")

        assert request.message == "测试消息"
        assert request.enable_rag is True
        assert request.rag_top_k == 3
        assert request.retrieval_method == "hybrid"
        assert request.vector_weight == 0.5
        assert request.bm25_weight == 0.5
        assert request.fusion_method == "rrf"

    def test_chat_request_custom_values(self):
        """测试自定义值"""
        request = ChatRequest(
            message="测试消息",
            enable_rag=True,
            rag_top_k=5,
            retrieval_method="bm25",
            vector_weight=0.7,
            bm25_weight=0.3,
            fusion_method="weighted"
        )

        assert request.retrieval_method == "bm25"
        assert request.vector_weight == 0.7
        assert request.bm25_weight == 0.3
        assert request.fusion_method == "weighted"

    def test_weight_validation(self):
        """测试权重验证"""
        # 权重应该在 0.0-1.0 之间
        request = ChatRequest(
            message="测试",
            vector_weight=0.0,
            bm25_weight=1.0
        )

        assert request.vector_weight == 0.0
        assert request.bm25_weight == 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
