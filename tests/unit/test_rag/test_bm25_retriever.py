"""
Unit Tests for BM25Retriever
测试 BM25 全文检索器
"""

import pytest
import tempfile
from pathlib import Path
from src.core.rag import (
    BM25Retriever,
    BM25Config,
    RetrievalConfig,
    Chunk,
    RetrievalError,
    InvalidConfigError,
    get_bm25_retriever
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
            metadata={"source": "python_intro", "language": "zh"}
        ),
        Chunk(
            chunk_id="doc2_chunk_0",
            parent_id="doc2",
            content="机器学习是人工智能的一个重要分支，通过算法让计算机从数据中学习。",
            chunk_index=0,
            start_index=0,
            end_index=35,
            metadata={"source": "ml_intro", "language": "zh"}
        ),
        Chunk(
            chunk_id="doc3_chunk_0",
            parent_id="doc3",
            content="自然语言处理技术可以让计算机理解和生成人类语言，应用广泛。",
            chunk_index=0,
            start_index=0,
            end_index=32,
            metadata={"source": "nlp_intro", "language": "zh"}
        ),
        Chunk(
            chunk_id="doc4_chunk_0",
            parent_id="doc4",
            content="深度学习使用神经网络模型，在图像识别、语音识别等领域取得了突破性进展。",
            chunk_index=0,
            start_index=0,
            end_index=38,
            metadata={"source": "dl_intro", "language": "zh"}
        ),
        Chunk(
            chunk_id="doc5_chunk_0",
            parent_id="doc5",
            content="Python 语言在数据科学和机器学习领域非常流行，拥有丰富的库和工具。",
            chunk_index=0,
            start_index=0,
            end_index=36,
            metadata={"source": "python_ml", "language": "zh"}
        )
    ]


@pytest.fixture
def bm25_retriever(sample_documents):
    """初始化的 BM25 检索器"""
    retriever = BM25Retriever(
        retrieval_config=RetrievalConfig(top_k=3),
        bm25_config=BM25Config(k1=1.5, b=0.75, enable_cache=False)
    )
    retriever.index_documents(sample_documents)
    return retriever


class TestBM25RetrieverInit:
    """测试 BM25Retriever 初始化"""

    def test_init_default_config(self):
        """测试默认配置初始化"""
        retriever = BM25Retriever()
        assert retriever.bm25_config.k1 == 1.5
        assert retriever.bm25_config.b == 0.75
        assert retriever.config.top_k == 5

    def test_init_custom_config(self):
        """测试自定义配置初始化"""
        retrieval_config = RetrievalConfig(top_k=10, min_score=0.5)
        bm25_config = BM25Config(k1=2.0, b=0.5)

        retriever = BM25Retriever(retrieval_config, bm25_config)

        assert retriever.config.top_k == 10
        assert retriever.config.min_score == 0.5
        assert retriever.bm25_config.k1 == 2.0
        assert retriever.bm25_config.b == 0.5


class TestBM25Tokenization:
    """测试中文分词功能"""

    def test_tokenize_chinese_text(self):
        """测试中文分词"""
        retriever = BM25Retriever()
        text = "Python 是一种编程语言"
        tokens = retriever._tokenize(text)

        assert len(tokens) > 0
        assert "Python" in tokens or "python" in tokens
        assert "编程" in tokens or "编程语言" in tokens

    def test_tokenize_with_stopwords_removal(self):
        """测试停用词过滤"""
        retriever = BM25Retriever()
        text = "这是一个测试文本"
        tokens = retriever._tokenize(text, remove_stopwords=True)

        # "这", "是", "一个" 应该被过滤
        assert "这" not in tokens
        assert "是" not in tokens
        assert "测试" in tokens or "文本" in tokens

    def test_tokenize_empty_text(self):
        """测试空文本分词"""
        retriever = BM25Retriever()
        assert retriever._tokenize("") == []
        assert retriever._tokenize("   ") == []
        assert retriever._tokenize(None) == []


class TestBM25Indexing:
    """测试 BM25 索引功能"""

    def test_index_documents(self, sample_documents):
        """测试文档索引"""
        retriever = BM25Retriever()
        retriever.index_documents(sample_documents)

        assert retriever.bm25_model is not None
        assert len(retriever.documents) == len(sample_documents)
        assert len(retriever.tokenized_corpus) == len(sample_documents)

    def test_index_empty_documents(self):
        """测试索引空文档列表"""
        retriever = BM25Retriever()

        with pytest.raises(InvalidConfigError):
            retriever.index_documents([])

    def test_update_index(self, sample_documents):
        """测试索引更新"""
        retriever = BM25Retriever()
        retriever.index_documents(sample_documents[:3])

        assert len(retriever.documents) == 3

        # 更新索引
        retriever.update_index(sample_documents[3:])

        assert len(retriever.documents) == 5


class TestBM25Retrieval:
    """测试 BM25 检索功能"""

    @pytest.mark.asyncio
    async def test_retrieve_basic(self, bm25_retriever):
        """测试基本检索"""
        results = await bm25_retriever.retrieve("Python 编程语言", top_k=2)

        assert len(results) <= 2
        assert all(isinstance(r.score, float) for r in results)
        assert all(0 <= r.score <= 1 for r in results)
        # 结果应该按分数降序排列
        if len(results) > 1:
            assert results[0].score >= results[1].score

    @pytest.mark.asyncio
    async def test_retrieve_chinese_query(self, bm25_retriever):
        """测试中文查询"""
        results = await bm25_retriever.retrieve("机器学习", top_k=3)

        assert len(results) > 0
        # 应该能检索到包含 "机器学习" 的文档
        assert any("机器学习" in r.content for r in results)

    @pytest.mark.asyncio
    async def test_retrieve_with_min_score(self, sample_documents):
        """测试最小分数过滤"""
        retriever = BM25Retriever(
            retrieval_config=RetrievalConfig(top_k=10, min_score=0.7)
        )
        retriever.index_documents(sample_documents)

        results = await retriever.retrieve("Python", top_k=10)

        # 所有结果的分数应该 >= 0.7
        assert all(r.score >= 0.7 for r in results)

    @pytest.mark.asyncio
    async def test_retrieve_empty_query(self, bm25_retriever):
        """测试空查询"""
        with pytest.raises(InvalidConfigError):
            await bm25_retriever.retrieve("")

    @pytest.mark.asyncio
    async def test_retrieve_without_index(self):
        """测试未索引时检索"""
        retriever = BM25Retriever()

        with pytest.raises(RetrievalError):
            await retriever.retrieve("test query")

    @pytest.mark.asyncio
    async def test_batch_retrieve(self, bm25_retriever):
        """测试批量检索"""
        queries = ["Python", "机器学习", "深度学习"]
        results = await bm25_retriever.batch_retrieve(queries, top_k=2)

        assert len(results) == len(queries)
        assert all(len(r) <= 2 for r in results)


class TestBM25Persistence:
    """测试 BM25 索引持久化"""

    def test_save_and_load_index(self, bm25_retriever):
        """测试保存和加载索引"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test_index.pkl"

            # 保存索引
            bm25_retriever.save_index(str(filepath))
            assert filepath.exists()

            # 创建新的检索器并加载
            new_retriever = BM25Retriever()
            new_retriever.load_index(str(filepath))

            assert len(new_retriever.documents) == len(bm25_retriever.documents)
            assert new_retriever.bm25_model is not None

    def test_load_nonexistent_index(self):
        """测试加载不存在的索引"""
        retriever = BM25Retriever()

        with pytest.raises(RetrievalError):
            retriever.load_index("/nonexistent/path.pkl")

    def test_save_without_model(self):
        """测试未索引时保存"""
        retriever = BM25Retriever()

        with pytest.raises(RetrievalError):
            retriever.save_index("test.pkl")


class TestBM25Statistics:
    """测试 BM25 统计功能"""

    def test_get_statistics_with_index(self, bm25_retriever):
        """测试获取索引统计"""
        stats = bm25_retriever.get_statistics()

        assert stats["indexed"] is True
        assert stats["document_count"] == 5
        assert "config" in stats
        assert stats["config"]["k1"] == 1.5
        assert stats["config"]["b"] == 0.75

    def test_get_statistics_without_index(self):
        """测试未索引时的统计"""
        retriever = BM25Retriever()
        stats = retriever.get_statistics()

        assert stats["indexed"] is False
        assert stats["document_count"] == 0


class TestBM25Singleton:
    """测试 BM25Retriever 单例模式"""

    def test_get_singleton_instance(self):
        """测试获取单例实例"""
        retriever1 = get_bm25_retriever()
        retriever2 = get_bm25_retriever()

        # 应该返回同一个实例
        assert retriever1 is retriever2

    def test_force_new_instance(self):
        """测试强制创建新实例"""
        retriever1 = get_bm25_retriever()
        retriever2 = get_bm25_retriever(force_new=True)

        # 应该返回不同的实例
        assert retriever1 is not retriever2


class TestBM25EdgeCases:
    """测试边界情况"""

    @pytest.mark.asyncio
    async def test_retrieve_with_no_tokens(self, bm25_retriever):
        """测试查询分词后为空的情况"""
        # 只包含停用词的查询
        results = await bm25_retriever.retrieve("的了是在", top_k=3)

        # 应该返回空列表
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_retrieve_very_long_query(self, bm25_retriever):
        """测试非常长的查询"""
        long_query = "Python " * 100 + "编程语言"
        results = await bm25_retriever.retrieve(long_query, top_k=3)

        # 应该能正常处理
        assert len(results) > 0

    def test_index_documents_with_empty_content(self):
        """测试包含空内容的文档"""
        docs = [
            Chunk(
                chunk_id="empty_chunk",
                parent_id="empty",
                content="",
                chunk_index=0,
                start_index=0,
                end_index=0
            )
        ]

        retriever = BM25Retriever()
        # 应该能处理，空文档会被赋予占位符 token
        retriever.index_documents(docs)
        assert len(retriever.tokenized_corpus) == 1
        assert retriever.tokenized_corpus[0] == ["<empty>"]
