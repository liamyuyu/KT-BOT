"""
Unit Tests for HybridRetriever
测试混合检索器（融合向量检索和 BM25 检索）
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import List

from src.core.rag import (
    HybridRetriever,
    HybridConfig,
    RetrievalConfig,
    RetrievalResult,
    VectorRetriever,
    BM25Retriever,
    InvalidConfigError,
    RetrievalError,
    get_hybrid_retriever
)


@pytest.fixture
def mock_vector_results():
    """模拟向量检索结果"""
    return [
        RetrievalResult(
            chunk_id="doc1_chunk_0",
            parent_id="doc1",
            content="Python 是一种编程语言",
            metadata={"source": "python"},
            score=0.9,
            distance=0.1,
            chunk_index=0
        ),
        RetrievalResult(
            chunk_id="doc2_chunk_0",
            parent_id="doc2",
            content="机器学习是人工智能的分支",
            metadata={"source": "ml"},
            score=0.8,
            distance=0.2,
            chunk_index=0
        ),
        RetrievalResult(
            chunk_id="doc3_chunk_0",
            parent_id="doc3",
            content="深度学习使用神经网络",
            metadata={"source": "dl"},
            score=0.7,
            distance=0.3,
            chunk_index=0
        )
    ]


@pytest.fixture
def mock_bm25_results():
    """模拟 BM25 检索结果"""
    return [
        RetrievalResult(
            chunk_id="doc2_chunk_0",  # 与向量检索有重复
            parent_id="doc2",
            content="机器学习是人工智能的分支",
            metadata={"source": "ml"},
            score=0.85,
            distance=0.15,
            chunk_index=0
        ),
        RetrievalResult(
            chunk_id="doc4_chunk_0",
            parent_id="doc4",
            content="自然语言处理技术",
            metadata={"source": "nlp"},
            score=0.75,
            distance=0.25,
            chunk_index=0
        ),
        RetrievalResult(
            chunk_id="doc1_chunk_0",  # 与向量检索有重复
            parent_id="doc1",
            content="Python 是一种编程语言",
            metadata={"source": "python"},
            score=0.65,
            distance=0.35,
            chunk_index=0
        )
    ]


@pytest.fixture
def mock_vector_retriever(mock_vector_results):
    """模拟向量检索器"""
    retriever = Mock(spec=VectorRetriever)
    retriever.retrieve = AsyncMock(return_value=mock_vector_results)
    return retriever


@pytest.fixture
def mock_bm25_retriever(mock_bm25_results):
    """模拟 BM25 检索器"""
    retriever = Mock(spec=BM25Retriever)
    retriever.retrieve = AsyncMock(return_value=mock_bm25_results)
    return retriever


@pytest.fixture
def hybrid_retriever(mock_vector_retriever, mock_bm25_retriever):
    """初始化的混合检索器（使用 RRF 融合）"""
    return HybridRetriever(
        vector_retriever=mock_vector_retriever,
        bm25_retriever=mock_bm25_retriever,
        retrieval_config=RetrievalConfig(top_k=5),
        hybrid_config=HybridConfig(fusion_method="rrf", rrf_k=60)
    )


class TestHybridRetrieverInit:
    """测试 HybridRetriever 初始化"""

    def test_init_default_config(self, mock_vector_retriever, mock_bm25_retriever):
        """测试默认配置初始化"""
        retriever = HybridRetriever(
            vector_retriever=mock_vector_retriever,
            bm25_retriever=mock_bm25_retriever
        )

        assert retriever.vector_retriever is mock_vector_retriever
        assert retriever.bm25_retriever is mock_bm25_retriever
        assert retriever.hybrid_config.fusion_method == "rrf"
        assert retriever.hybrid_config.rrf_k == 60
        assert retriever.config.top_k == 5

    def test_init_custom_config(self, mock_vector_retriever, mock_bm25_retriever):
        """测试自定义配置初始化"""
        retrieval_config = RetrievalConfig(top_k=10, min_score=0.6)
        hybrid_config = HybridConfig(
            fusion_method="weighted",
            vector_weight=0.7,
            bm25_weight=0.3,
            deduplicate=False,
            normalize_scores=False
        )

        retriever = HybridRetriever(
            vector_retriever=mock_vector_retriever,
            bm25_retriever=mock_bm25_retriever,
            retrieval_config=retrieval_config,
            hybrid_config=hybrid_config
        )

        assert retriever.config.top_k == 10
        assert retriever.config.min_score == 0.6
        assert retriever.hybrid_config.fusion_method == "weighted"
        assert retriever.hybrid_config.vector_weight == 0.7
        assert retriever.hybrid_config.bm25_weight == 0.3
        assert retriever.hybrid_config.deduplicate is False
        assert retriever.hybrid_config.normalize_scores is False

    def test_init_invalid_fusion_method(self, mock_vector_retriever, mock_bm25_retriever):
        """测试无效的融合方法"""
        hybrid_config = HybridConfig(fusion_method="invalid_method")

        with pytest.raises(InvalidConfigError) as exc_info:
            HybridRetriever(
                vector_retriever=mock_vector_retriever,
                bm25_retriever=mock_bm25_retriever,
                hybrid_config=hybrid_config
            )

        assert "Invalid fusion_method" in str(exc_info.value)


class TestRRFFusion:
    """测试 RRF 融合算法"""

    @pytest.mark.asyncio
    async def test_rrf_basic(self, hybrid_retriever):
        """测试基本 RRF 融合"""
        results = await hybrid_retriever.retrieve("test query", top_k=5)

        # 应该返回结果
        assert len(results) > 0
        assert len(results) <= 5

        # 验证结果按分数降序排列
        for i in range(len(results) - 1):
            assert results[i].score >= results[i + 1].score

        # 验证调用了两个检索器
        hybrid_retriever.vector_retriever.retrieve.assert_called_once()
        hybrid_retriever.bm25_retriever.retrieve.assert_called_once()

    def test_rrf_score_calculation(self, hybrid_retriever, mock_vector_results, mock_bm25_results):
        """测试 RRF 分数计算的正确性"""
        k = 60

        # 手动计算 RRF 分数
        # doc1_chunk_0: rank 1 in vector (0.9), rank 3 in bm25 (0.65)
        # RRF score = 1/(60+1) + 1/(60+3) = 1/61 + 1/63 ≈ 0.0164 + 0.0159 = 0.0323

        # doc2_chunk_0: rank 2 in vector (0.8), rank 1 in bm25 (0.85)
        # RRF score = 1/(60+2) + 1/(60+1) = 1/62 + 1/61 ≈ 0.0161 + 0.0164 = 0.0325

        fused = hybrid_retriever._rrf_fusion(mock_vector_results, mock_bm25_results, k=k)

        # 找到 doc2_chunk_0 的结果（应该排第一，因为 RRF 分数最高）
        doc2_result = next(r for r in fused if r.chunk_id == "doc2_chunk_0")
        doc1_result = next(r for r in fused if r.chunk_id == "doc1_chunk_0")

        # doc2 应该得分更高（因为在两个检索器中排名都靠前）
        assert doc2_result.score > doc1_result.score

    def test_rrf_with_different_k(self, hybrid_retriever, mock_vector_results, mock_bm25_results):
        """测试不同的 RRF k 参数"""
        # k=1 时，排名的影响更大
        fused_k1 = hybrid_retriever._rrf_fusion(mock_vector_results, mock_bm25_results, k=1)

        # k=1000 时，排名的影响较小
        fused_k1000 = hybrid_retriever._rrf_fusion(mock_vector_results, mock_bm25_results, k=1000)

        # 两种情况应该产生不同的分数分布
        assert len(fused_k1) == len(fused_k1000)
        # k 值不同，分数应该不同
        assert fused_k1[0].score != fused_k1000[0].score


class TestWeightedFusion:
    """测试加权融合算法"""

    @pytest.mark.asyncio
    async def test_weighted_basic(self, mock_vector_retriever, mock_bm25_retriever):
        """测试基本加权融合"""
        hybrid_config = HybridConfig(
            fusion_method="weighted",
            vector_weight=0.6,
            bm25_weight=0.4
        )
        retriever = HybridRetriever(
            vector_retriever=mock_vector_retriever,
            bm25_retriever=mock_bm25_retriever,
            hybrid_config=hybrid_config
        )

        results = await retriever.retrieve("test query", top_k=5)

        assert len(results) > 0
        assert len(results) <= 5

    def test_weighted_score_calculation(self, hybrid_retriever, mock_vector_results, mock_bm25_results):
        """测试加权分数计算的正确性"""
        vector_weight = 0.7
        bm25_weight = 0.3

        fused = hybrid_retriever._weighted_fusion(
            mock_vector_results,
            mock_bm25_results,
            vector_weight=vector_weight,
            bm25_weight=bm25_weight
        )

        # 找到 doc2_chunk_0（在两个结果中都存在）
        doc2_result = next(r for r in fused if r.chunk_id == "doc2_chunk_0")

        # 手动计算期望分数
        # vector score: 0.8, bm25 score: 0.85
        # weighted score = 0.7 * 0.8 + 0.3 * 0.85 = 0.56 + 0.255 = 0.815
        expected_score = vector_weight * 0.8 + bm25_weight * 0.85

        assert abs(doc2_result.score - expected_score) < 0.001

    def test_weighted_equal_weights(self, hybrid_retriever, mock_vector_results, mock_bm25_results):
        """测试相等权重（0.5/0.5）"""
        fused = hybrid_retriever._weighted_fusion(
            mock_vector_results,
            mock_bm25_results,
            vector_weight=0.5,
            bm25_weight=0.5
        )

        # 找到 doc1_chunk_0
        doc1_result = next(r for r in fused if r.chunk_id == "doc1_chunk_0")

        # 手动计算：0.5 * 0.9 + 0.5 * 0.65 = 0.45 + 0.325 = 0.775
        expected_score = 0.5 * 0.9 + 0.5 * 0.65

        assert abs(doc1_result.score - expected_score) < 0.001


class TestLinearFusion:
    """测试线性融合算法"""

    @pytest.mark.asyncio
    async def test_linear_basic(self, mock_vector_retriever, mock_bm25_retriever):
        """测试基本线性融合"""
        hybrid_config = HybridConfig(
            fusion_method="linear",
            vector_weight=0.6,
            bm25_weight=0.4
        )
        retriever = HybridRetriever(
            vector_retriever=mock_vector_retriever,
            bm25_retriever=mock_bm25_retriever,
            hybrid_config=hybrid_config
        )

        results = await retriever.retrieve("test query", top_k=5)

        assert len(results) > 0

    def test_linear_same_as_weighted(self, hybrid_retriever, mock_vector_results, mock_bm25_results):
        """测试线性融合与加权融合产生相同结果"""
        vector_weight = 0.6
        bm25_weight = 0.4

        weighted = hybrid_retriever._weighted_fusion(
            mock_vector_results,
            mock_bm25_results,
            vector_weight=vector_weight,
            bm25_weight=bm25_weight
        )

        linear = hybrid_retriever._linear_fusion(
            mock_vector_results,
            mock_bm25_results,
            vector_weight=vector_weight,
            bm25_weight=bm25_weight
        )

        # 两种方法应该产生相同的结果
        assert len(weighted) == len(linear)
        for w, l in zip(weighted, linear):
            assert w.chunk_id == l.chunk_id
            assert abs(w.score - l.score) < 0.001


class TestDeduplication:
    """测试去重功能"""

    def test_deduplicate_basic(self, hybrid_retriever):
        """测试基本去重"""
        # 创建包含重复的结果列表
        results = [
            RetrievalResult(
                chunk_id="doc1_chunk_0",
                parent_id="doc1",
                content="content 1",
                metadata={},
                score=0.9,
                distance=0.1,
                chunk_index=0
            ),
            RetrievalResult(
                chunk_id="doc2_chunk_0",
                parent_id="doc2",
                content="content 2",
                metadata={},
                score=0.8,
                distance=0.2,
                chunk_index=0
            ),
            RetrievalResult(
                chunk_id="doc1_chunk_0",  # 重复
                parent_id="doc1",
                content="content 1",
                metadata={},
                score=0.7,  # 较低分数
                distance=0.3,
                chunk_index=0
            )
        ]

        deduplicated = hybrid_retriever._deduplicate(results)

        # 应该只保留 2 个唯一结果
        assert len(deduplicated) == 2

        # 应该保留第一次出现的（分数更高的）
        chunk_ids = [r.chunk_id for r in deduplicated]
        assert "doc1_chunk_0" in chunk_ids
        assert "doc2_chunk_0" in chunk_ids

        # 验证保留的是高分版本
        doc1_result = next(r for r in deduplicated if r.chunk_id == "doc1_chunk_0")
        assert doc1_result.score == 0.9

    def test_deduplicate_no_duplicates(self, hybrid_retriever):
        """测试没有重复的情况"""
        results = [
            RetrievalResult(
                chunk_id=f"doc{i}_chunk_0",
                parent_id=f"doc{i}",
                content=f"content {i}",
                metadata={},
                score=0.9 - i * 0.1,
                distance=0.1 + i * 0.1,
                chunk_index=0
            )
            for i in range(5)
        ]

        deduplicated = hybrid_retriever._deduplicate(results)

        # 应该保持相同数量
        assert len(deduplicated) == len(results)

    @pytest.mark.asyncio
    async def test_deduplicate_disabled(self, mock_vector_retriever, mock_bm25_retriever):
        """测试禁用去重"""
        hybrid_config = HybridConfig(
            fusion_method="rrf",
            deduplicate=False  # 禁用去重
        )
        retriever = HybridRetriever(
            vector_retriever=mock_vector_retriever,
            bm25_retriever=mock_bm25_retriever,
            hybrid_config=hybrid_config
        )

        results = await retriever.retrieve("test query", top_k=10)

        # RRF 融合本身就会合并重复的 chunk_id，所以不会有重复
        # 但测试配置生效
        assert len(results) > 0


class TestScoreNormalization:
    """测试分数归一化"""

    def test_normalize_scores_basic(self, hybrid_retriever):
        """测试基本分数归一化"""
        results = [
            RetrievalResult(
                chunk_id=f"doc{i}_chunk_0",
                parent_id=f"doc{i}",
                content=f"content {i}",
                metadata={},
                score=float(i),  # 分数：0, 1, 2, 3, 4
                distance=0.0,
                chunk_index=0
            )
            for i in range(5)
        ]

        normalized = hybrid_retriever._normalize_scores(results)

        # 分数应该在 [0, 1] 区间
        assert all(0.0 <= r.score <= 1.0 for r in normalized)

        # 最小值应该归一化为 0，最大值应该归一化为 1
        assert normalized[0].score == 0.0  # 原始分数 0
        assert normalized[-1].score == 1.0  # 原始分数 4

    def test_normalize_scores_identical(self, hybrid_retriever):
        """测试所有分数相同时的归一化"""
        results = [
            RetrievalResult(
                chunk_id=f"doc{i}_chunk_0",
                parent_id=f"doc{i}",
                content=f"content {i}",
                metadata={},
                score=0.5,  # 所有分数相同
                distance=0.5,
                chunk_index=0
            )
            for i in range(5)
        ]

        normalized = hybrid_retriever._normalize_scores(results)

        # 分数应该保持不变
        assert all(r.score == 0.5 for r in normalized)

    def test_normalize_scores_empty(self, hybrid_retriever):
        """测试空结果列表"""
        normalized = hybrid_retriever._normalize_scores([])
        assert normalized == []

    @pytest.mark.asyncio
    async def test_normalization_disabled(self, mock_vector_retriever, mock_bm25_retriever):
        """测试禁用归一化"""
        hybrid_config = HybridConfig(
            fusion_method="rrf",
            normalize_scores=False  # 禁用归一化
        )
        retriever = HybridRetriever(
            vector_retriever=mock_vector_retriever,
            bm25_retriever=mock_bm25_retriever,
            hybrid_config=hybrid_config
        )

        results = await retriever.retrieve("test query", top_k=5)

        # 应该返回结果（分数未归一化）
        assert len(results) > 0


class TestHybridRetrieval:
    """测试完整的混合检索流程"""

    @pytest.mark.asyncio
    async def test_retrieve_with_top_k(self, hybrid_retriever):
        """测试指定 top_k"""
        results = await hybrid_retriever.retrieve("test query", top_k=2)

        assert len(results) <= 2

    @pytest.mark.asyncio
    async def test_retrieve_with_min_score(self, mock_vector_retriever, mock_bm25_retriever):
        """测试最小分数过滤"""
        retrieval_config = RetrievalConfig(top_k=10, min_score=0.5)
        retriever = HybridRetriever(
            vector_retriever=mock_vector_retriever,
            bm25_retriever=mock_bm25_retriever,
            retrieval_config=retrieval_config
        )

        results = await retriever.retrieve("test query", top_k=10)

        # 所有结果的分数应该 >= 0.5
        assert all(r.score >= 0.5 for r in results)

    @pytest.mark.asyncio
    async def test_retrieve_empty_query(self, hybrid_retriever):
        """测试空查询"""
        with pytest.raises(InvalidConfigError) as exc_info:
            await hybrid_retriever.retrieve("")

        assert "Query cannot be empty" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_retrieve_with_custom_candidate_counts(self, hybrid_retriever):
        """测试自定义候选数量"""
        results = await hybrid_retriever.retrieve(
            "test query",
            top_k=3,
            vector_top_k=5,
            bm25_top_k=5
        )

        # 验证调用了检索器，并传递了正确的 top_k
        hybrid_retriever.vector_retriever.retrieve.assert_called_with("test query", top_k=5)
        hybrid_retriever.bm25_retriever.retrieve.assert_called_with("test query", top_k=5)

        assert len(results) <= 3

    @pytest.mark.asyncio
    async def test_batch_retrieve(self, hybrid_retriever):
        """测试批量检索"""
        queries = ["query 1", "query 2", "query 3"]
        results = await hybrid_retriever.batch_retrieve(queries, top_k=2)

        assert len(results) == len(queries)
        assert all(len(r) <= 2 for r in results)


class TestHybridSingleton:
    """测试混合检索器单例模式"""

    def test_get_singleton_instance(self, mock_vector_retriever, mock_bm25_retriever):
        """测试获取单例实例"""
        retriever1 = get_hybrid_retriever(
            vector_retriever=mock_vector_retriever,
            bm25_retriever=mock_bm25_retriever,
            force_new=True  # 强制创建新实例避免测试干扰
        )
        retriever2 = get_hybrid_retriever()

        # 应该返回同一个实例
        assert retriever1 is retriever2

    def test_force_new_instance(self, mock_vector_retriever, mock_bm25_retriever):
        """测试强制创建新实例"""
        retriever1 = get_hybrid_retriever(
            vector_retriever=mock_vector_retriever,
            bm25_retriever=mock_bm25_retriever,
            force_new=True
        )
        retriever2 = get_hybrid_retriever(
            vector_retriever=mock_vector_retriever,
            bm25_retriever=mock_bm25_retriever,
            force_new=True
        )

        # 应该返回不同的实例
        assert retriever1 is not retriever2

    def test_get_without_retrievers(self):
        """测试未提供检索器时报错"""
        with pytest.raises(InvalidConfigError) as exc_info:
            get_hybrid_retriever(force_new=True)

        assert "vector_retriever and bm25_retriever are required" in str(exc_info.value)


class TestEdgeCases:
    """测试边界情况"""

    @pytest.mark.asyncio
    async def test_retrieve_with_empty_results(self, mock_vector_retriever, mock_bm25_retriever):
        """测试检索器返回空结果"""
        # 模拟两个检索器都返回空列表
        mock_vector_retriever.retrieve = AsyncMock(return_value=[])
        mock_bm25_retriever.retrieve = AsyncMock(return_value=[])

        retriever = HybridRetriever(
            vector_retriever=mock_vector_retriever,
            bm25_retriever=mock_bm25_retriever
        )

        results = await retriever.retrieve("test query", top_k=5)

        # 应该返回空列表
        assert results == []

    @pytest.mark.asyncio
    async def test_retrieve_with_one_empty_result(self, mock_vector_retriever, mock_bm25_retriever, mock_bm25_results):
        """测试一个检索器返回空结果"""
        # 向量检索返回空，BM25 有结果
        mock_vector_retriever.retrieve = AsyncMock(return_value=[])

        retriever = HybridRetriever(
            vector_retriever=mock_vector_retriever,
            bm25_retriever=mock_bm25_retriever
        )

        results = await retriever.retrieve("test query", top_k=5)

        # 应该返回 BM25 的结果
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_retrieve_error_handling(self, mock_vector_retriever, mock_bm25_retriever):
        """测试检索错误处理"""
        # 模拟向量检索器抛出异常
        mock_vector_retriever.retrieve = AsyncMock(side_effect=Exception("Vector retrieval failed"))

        retriever = HybridRetriever(
            vector_retriever=mock_vector_retriever,
            bm25_retriever=mock_bm25_retriever
        )

        with pytest.raises(RetrievalError) as exc_info:
            await retriever.retrieve("test query", top_k=5)

        assert "Hybrid retrieval failed" in str(exc_info.value)

    def test_fusion_with_single_result(self, hybrid_retriever):
        """测试只有一个结果的融合"""
        vector_results = [
            RetrievalResult(
                chunk_id="doc1_chunk_0",
                parent_id="doc1",
                content="content",
                metadata={},
                score=0.9,
                distance=0.1,
                chunk_index=0
            )
        ]
        bm25_results = []

        fused = hybrid_retriever._rrf_fusion(vector_results, bm25_results, k=60)

        assert len(fused) == 1
        assert fused[0].chunk_id == "doc1_chunk_0"
