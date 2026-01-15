"""
Unit Tests for Cross-Encoder Reranker
Cross-Encoder 重排序器单元测试
"""

import pytest
import asyncio
from typing import List

from src.core.rag import (
    RetrievalResult,
    RerankerConfig,
    RerankerResult,
    CrossEncoderReranker,
    get_reranker
)


@pytest.fixture
def sample_documents() -> List[RetrievalResult]:
    """创建测试文档集"""
    return [
        RetrievalResult(
            chunk_id="doc1_chunk_0",
            parent_id="doc1",
            content="Python 是一种广泛使用的高级编程语言，以其简洁的语法和强大的功能著称。",
            metadata={"source": "doc1"},
            score=0.75,
            distance=0.25,
            chunk_index=0
        ),
        RetrievalResult(
            chunk_id="doc2_chunk_0",
            parent_id="doc2",
            content="机器学习是人工智能的一个重要分支，让计算机能够从数据中学习模式。",
            metadata={"source": "doc2"},
            score=0.70,
            distance=0.30,
            chunk_index=0
        ),
        RetrievalResult(
            chunk_id="doc3_chunk_0",
            parent_id="doc3",
            content="深度学习使用多层神经网络来学习数据的层次化表示，在图像识别等领域表现出色。",
            metadata={"source": "doc3"},
            score=0.68,
            distance=0.32,
            chunk_index=0
        ),
        RetrievalResult(
            chunk_id="doc4_chunk_0",
            parent_id="doc4",
            content="自然语言处理技术让计算机能够理解和生成人类语言，应用广泛。",
            metadata={"source": "doc4"},
            score=0.65,
            distance=0.35,
            chunk_index=0
        ),
        RetrievalResult(
            chunk_id="doc5_chunk_0",
            parent_id="doc5",
            content="JavaScript 是一种脚本语言，主要用于网页开发和前端交互。",
            metadata={"source": "doc5"},
            score=0.60,
            distance=0.40,
            chunk_index=0
        ),
    ]


@pytest.fixture
def reranker_config() -> RerankerConfig:
    """创建重排序配置"""
    return RerankerConfig(
        model_name="BAAI/bge-reranker-base",  # 使用更小的模型进行测试
        batch_size=2,
        max_length=256,
        normalize_scores=True,
        use_fp16=False,
        device="cpu"
    )


@pytest.fixture
def reranker(reranker_config: RerankerConfig) -> CrossEncoderReranker:
    """创建重排序器实例"""
    return CrossEncoderReranker(reranker_config)


class TestRerankerConfig:
    """测试重排序配置"""

    def test_default_config(self):
        """测试默认配置"""
        config = RerankerConfig()

        assert config.model_name == "BAAI/bge-reranker-large"
        assert config.batch_size == 4
        assert config.max_length == 512
        assert config.normalize_scores is True
        assert config.use_fp16 is False
        assert config.device is None
        assert config.timeout_seconds == 30.0

    def test_custom_config(self):
        """测试自定义配置"""
        config = RerankerConfig(
            model_name="custom-model",
            batch_size=8,
            max_length=1024,
            normalize_scores=False,
            use_fp16=True,
            device="cuda",
            timeout_seconds=60.0
        )

        assert config.model_name == "custom-model"
        assert config.batch_size == 8
        assert config.max_length == 1024
        assert config.normalize_scores is False
        assert config.use_fp16 is True
        assert config.device == "cuda"
        assert config.timeout_seconds == 60.0


class TestCrossEncoderReranker:
    """测试 Cross-Encoder 重排序器"""

    def test_reranker_initialization(self, reranker: CrossEncoderReranker):
        """测试重排序器初始化"""
        assert reranker.config is not None
        assert reranker.model is None  # 延迟加载
        assert reranker._model_loaded is False

    def test_get_device(self, reranker: CrossEncoderReranker):
        """测试设备检测"""
        device = reranker._get_device()
        assert device in ["cpu", "cuda", "mps"]

    def test_normalize_scores(self, reranker: CrossEncoderReranker):
        """测试分数归一化"""
        raw_scores = [-2.0, -1.0, 0.0, 1.0, 2.0]
        normalized = reranker._normalize_scores(raw_scores)

        # 验证归一化结果在 0-1 区间
        assert all(0.0 <= score <= 1.0 for score in normalized)

        # 验证单调性（原始分数越高，归一化后也越高）
        for i in range(len(normalized) - 1):
            assert normalized[i] < normalized[i + 1]

        # 验证 sigmoid 特性
        # sigmoid(0) = 0.5
        assert abs(normalized[2] - 0.5) < 0.01

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_rerank_basic(
        self,
        reranker: CrossEncoderReranker,
        sample_documents: List[RetrievalResult]
    ):
        """测试基本重排序功能"""
        query = "什么是 Python 编程语言？"

        # 执行重排序
        results = await reranker.rerank(query, sample_documents, top_k=3)

        # 验证结果
        assert len(results) == 3
        assert all(isinstance(r, RerankerResult) for r in results)

        # 验证分数在 0-1 区间
        assert all(0.0 <= r.rerank_score <= 1.0 for r in results)

        # 验证分数单调递减
        for i in range(len(results) - 1):
            assert results[i].rerank_score >= results[i + 1].rerank_score

        # 验证排名字段
        assert results[0].new_rank == 0
        assert results[1].new_rank == 1
        assert results[2].new_rank == 2

        # 验证原始信息保留
        assert all(r.chunk_id in [d.chunk_id for d in sample_documents] for r in results)

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_rerank_relevance(
        self,
        reranker: CrossEncoderReranker,
        sample_documents: List[RetrievalResult]
    ):
        """测试重排序相关性提升"""
        query = "Python 编程语言的特点"

        # 执行重排序
        results = await reranker.rerank(query, sample_documents, top_k=5)

        # 第一个结果应该是关于 Python 的文档
        assert "Python" in results[0].content

        # 验证重排序改变了顺序（Python 文档排名提升）
        python_doc = next(r for r in results if "Python" in r.content)
        assert python_doc.new_rank == 0  # Python 文档应该排第一

    @pytest.mark.asyncio
    async def test_rerank_empty_documents(self, reranker: CrossEncoderReranker):
        """测试空文档列表"""
        query = "测试查询"
        results = await reranker.rerank(query, [])

        assert results == []

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_rerank_top_k(
        self,
        reranker: CrossEncoderReranker,
        sample_documents: List[RetrievalResult]
    ):
        """测试 top_k 参数"""
        query = "机器学习"

        # 不指定 top_k，返回全部
        results_all = await reranker.rerank(query, sample_documents)
        assert len(results_all) == len(sample_documents)

        # 指定 top_k = 2
        results_top2 = await reranker.rerank(query, sample_documents, top_k=2)
        assert len(results_top2) == 2

        # top_k 结果应该是全部结果的前 k 个
        assert results_top2[0].chunk_id == results_all[0].chunk_id
        assert results_top2[1].chunk_id == results_all[1].chunk_id

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_batch_scoring(
        self,
        reranker: CrossEncoderReranker,
        sample_documents: List[RetrievalResult]
    ):
        """测试批量打分"""
        query = "测试批量处理"

        # 确保模型已加载
        if not reranker._model_loaded:
            reranker._load_model()

        # batch_size = 2，5 个文档需要 3 个批次
        scores = await reranker._batch_score(query, sample_documents)

        assert len(scores) == len(sample_documents)
        assert all(isinstance(s, float) for s in scores)

    def test_get_model_info(self, reranker: CrossEncoderReranker):
        """测试获取模型信息"""
        info = reranker.get_model_info()

        assert "model_name" in info
        assert "device" in info
        assert "batch_size" in info
        assert "max_length" in info
        assert "loaded" in info

        assert info["model_name"] == reranker.config.model_name
        assert info["loaded"] is False  # 尚未加载


class TestRerankerSingleton:
    """测试重排序器单例"""

    def test_get_reranker_singleton(self):
        """测试单例模式"""
        config = RerankerConfig(model_name="test-model")

        reranker1 = get_reranker(config)
        reranker2 = get_reranker(config)

        # 应该返回同一个实例
        assert reranker1 is reranker2


class TestRerankerResult:
    """测试重排序结果模型"""

    def test_reranker_result_creation(self):
        """测试重排序结果创建"""
        result = RerankerResult(
            chunk_id="doc1_chunk_0",
            parent_id="doc1",
            content="测试内容",
            metadata={"source": "test"},
            original_score=0.75,
            rerank_score=0.92,
            original_rank=3,
            new_rank=0,
            chunk_index=0
        )

        assert result.chunk_id == "doc1_chunk_0"
        assert result.original_score == 0.75
        assert result.rerank_score == 0.92
        assert result.original_rank == 3
        assert result.new_rank == 0

    def test_reranker_result_comparison(self):
        """测试重排序结果比较"""
        result1 = RerankerResult(
            chunk_id="doc1",
            parent_id="doc1",
            content="content1",
            metadata={},
            original_score=0.7,
            rerank_score=0.9,
            original_rank=1,
            new_rank=0,
            chunk_index=0
        )

        result2 = RerankerResult(
            chunk_id="doc2",
            parent_id="doc2",
            content="content2",
            metadata={},
            original_score=0.8,
            rerank_score=0.85,
            original_rank=0,
            new_rank=1,
            chunk_index=0
        )

        # 验证重排序改变了顺序
        assert result1.rerank_score > result2.rerank_score
        assert result1.original_score < result2.original_score


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
