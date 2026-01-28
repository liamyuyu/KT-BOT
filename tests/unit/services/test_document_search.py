"""
文档搜索引擎测试
Story 4.5 Phase 1
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from src.services.search.document_search import DocumentSearchEngine
from src.services.search.models import SearchQuery, SearchMethod
from src.core.rag.models import RetrievalResult


# ========================================================================
# Fixtures
# ========================================================================

@pytest.fixture
def mock_vector_retriever():
    """模拟向量检索器"""
    retriever = AsyncMock()

    # 模拟检索结果
    sample_result = RetrievalResult(
        chunk_id="test_chunk_0",
        parent_id="TEST-123",
        content="This is a test document about Python programming. "
                "It covers basic concepts and advanced techniques.",
        metadata={
            "source": "jira",
            "issue_key": "TEST-123",
            "title": "Python Programming Guide",
            "doc_type": "issue",
            "priority": "High",
            "created_at": datetime.now().isoformat()
        },
        score=0.9,
        distance=0.1,
        chunk_index=0
    )

    retriever.retrieve = AsyncMock(return_value=[sample_result])
    return retriever


@pytest.fixture
def search_engine(mock_vector_retriever):
    """创建搜索引擎实例"""
    return DocumentSearchEngine(
        vector_retriever=mock_vector_retriever,
        bm25_retriever=None,
        hybrid_retriever=None
    )


# ========================================================================
# DocumentSearchEngine Tests
# ========================================================================

class TestDocumentSearchEngine:
    """文档搜索引擎测试"""

    @pytest.mark.asyncio
    async def test_vector_search(self, search_engine, mock_vector_retriever):
        """测试向量搜索"""
        query = SearchQuery(
            query="Python programming",
            method=SearchMethod.VECTOR,
            top_k=10,
            page=1,
            page_size=10
        )

        response = await search_engine.search(query)

        # 验证响应
        assert response.query == "Python programming"
        assert response.total == 1
        assert len(response.results) == 1
        assert response.method == "vector"

        # 验证结果
        result = response.results[0]
        assert result.doc_id == "test_chunk_0"
        assert result.parent_id == "TEST-123"
        assert result.title == "Python Programming Guide"
        assert result.source == "jira"
        assert result.score == 0.9

        # 验证检索器被调用
        mock_vector_retriever.retrieve.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_with_highlight(self, search_engine):
        """测试关键词高亮"""
        query = SearchQuery(
            query="Python programming",
            method=SearchMethod.VECTOR,
            top_k=10,
            enable_highlight=True
        )

        response = await search_engine.search(query)

        # 验证高亮
        result = response.results[0]
        assert result.highlights is not None
        assert len(result.highlights) > 0

    @pytest.mark.asyncio
    async def test_search_with_pagination(self, search_engine, mock_vector_retriever):
        """测试分页功能"""
        # 模拟多个结果
        results = [
            RetrievalResult(
                chunk_id=f"chunk_{i}",
                parent_id=f"DOC-{i}",
                content=f"Document {i} content",
                metadata={
                    "source": "jira",
                    "title": f"Document {i}",
                    "doc_type": "issue"
                },
                score=0.9 - i * 0.1,
                distance=0.1 + i * 0.1,
                chunk_index=0
            )
            for i in range(25)
        ]
        mock_vector_retriever.retrieve = AsyncMock(return_value=results)

        # 请求第2页，每页10条
        query = SearchQuery(
            query="test",
            method=SearchMethod.VECTOR,
            page=2,
            page_size=10
        )

        response = await search_engine.search(query)

        # 验证分页
        assert response.total == 25
        assert response.page == 2
        assert response.page_size == 10
        assert response.total_pages == 3
        assert len(response.results) == 10

        # 验证返回的是第2页的结果（索引10-19）
        assert response.results[0].doc_id == "chunk_10"

    @pytest.mark.asyncio
    async def test_search_with_filters(self, search_engine, mock_vector_retriever):
        """测试带过滤条件的搜索"""
        query = SearchQuery(
            query="test",
            method=SearchMethod.VECTOR,
            sources=["jira"],
            doc_types=["issue"],
            time_range="7d"
        )

        response = await search_engine.search(query)

        # 验证检索器被调用时传入了过滤条件
        mock_vector_retriever.retrieve.assert_called_once()
        call_kwargs = mock_vector_retriever.retrieve.call_args.kwargs
        assert "filters" in call_kwargs
        assert call_kwargs["filters"] is not None

    @pytest.mark.asyncio
    async def test_search_without_highlight(self, search_engine):
        """测试禁用高亮"""
        query = SearchQuery(
            query="Python",
            method=SearchMethod.VECTOR,
            enable_highlight=False
        )

        response = await search_engine.search(query)

        # 验证没有高亮
        result = response.results[0]
        assert result.highlights is None

    @pytest.mark.asyncio
    async def test_bm25_fallback_to_vector(self, search_engine):
        """测试 BM25 搜索回退到向量搜索"""
        query = SearchQuery(
            query="test",
            method=SearchMethod.BM25
        )

        response = await search_engine.search(query)

        # 应该成功执行（回退到向量搜索）
        assert response.total >= 0
        assert response.method == "bm25"

    @pytest.mark.asyncio
    async def test_hybrid_fallback_to_vector(self, search_engine):
        """测试混合搜索回退到向量搜索"""
        query = SearchQuery(
            query="test",
            method=SearchMethod.HYBRID
        )

        response = await search_engine.search(query)

        # 应该成功执行（回退到向量搜索）
        assert response.total >= 0
        assert response.method == "hybrid"


# ========================================================================
# Highlight Tests
# ========================================================================

class TestHighlightFeature:
    """关键词高亮测试"""

    def test_find_keyword_matches(self, search_engine):
        """测试关键词匹配查找"""
        text = "Python is a great programming language for beginners and experts."
        keyword = "Python"

        matches = search_engine._find_keyword_matches(text, keyword)

        assert len(matches) > 0
        assert matches[0].text.lower().find(keyword.lower()) >= 0

    def test_case_insensitive_match(self, search_engine):
        """测试不区分大小写匹配"""
        text = "Python and python are the same"
        keyword = "PYTHON"

        matches = search_engine._find_keyword_matches(text, keyword)

        # 应该找到两个匹配
        assert len(matches) == 2

    def test_generate_highlights(self, search_engine):
        """测试生成高亮"""
        content = "Python is great. Python programming is fun."
        title = "Python Tutorial"
        query_text = "Python programming"

        highlights = search_engine._generate_highlights(
            content=content,
            title=title,
            query_text=query_text,
            highlight_fields=["title", "content"]
        )

        assert len(highlights) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
