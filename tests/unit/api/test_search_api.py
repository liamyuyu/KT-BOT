"""
搜索 API 测试
Story 4.5: 搜索功能
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient

from src.api.main import app
from src.services.search.models import SearchResponse, SearchResult, SearchMethod


# ========================================================================
# Fixtures
# ========================================================================

@pytest.fixture
def mock_search_engine():
    """模拟搜索引擎"""
    engine = Mock()

    # 模拟搜索响应
    sample_result = SearchResult(
        doc_id="test-doc-1",
        parent_id="TEST-123",
        title="Test Document",
        content="This is a test document about Python programming.",
        source="jira",
        doc_type="issue",
        score=0.9,
        metadata={"issue_key": "TEST-123"},
        highlights=None
    )

    sample_response = SearchResponse(
        query="Python",
        total=1,
        results=[sample_result],
        page=1,
        page_size=10,
        total_pages=1,
        search_time_ms=120,
        method="hybrid"
    )

    engine.search = AsyncMock(return_value=sample_response)
    return engine


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


# ========================================================================
# 搜索 API 测试
# ========================================================================

class TestSearchAPI:
    """测试搜索 API 端点"""

    @pytest.mark.asyncio
    async def test_search_documents_success(self, client, mock_search_engine):
        """测试成功搜索文档"""
        with patch("src.api.routes.search.get_search_engine", return_value=mock_search_engine):
            response = client.post(
                "/api/v1/search/documents",
                json={
                    "query": "Python",
                    "method": "hybrid",
                    "top_k": 10,
                    "page": 1,
                    "page_size": 10
                }
            )

            assert response.status_code == 200
            data = response.json()

            # 验证响应格式
            assert "data" in data
            search_data = data["data"]
            assert "query" in search_data
            assert "total" in search_data
            assert "results" in search_data
            assert search_data["query"] == "Python"
            assert len(search_data["results"]) == 1

            # 验证搜索引擎被调用
            mock_search_engine.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_documents_with_filters(self, client, mock_search_engine):
        """测试带过滤条件的搜索"""
        with patch("src.api.routes.search.get_search_engine", return_value=mock_search_engine):
            response = client.post(
                "/api/v1/search/documents",
                json={
                    "query": "bug",
                    "method": "vector",
                    "sources": ["jira"],
                    "doc_types": ["issue"],
                    "time_range": "7d",
                    "enable_highlight": True
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert "data" in data

    @pytest.mark.asyncio
    async def test_search_documents_pagination(self, client, mock_search_engine):
        """测试分页搜索"""
        with patch("src.api.routes.search.get_search_engine", return_value=mock_search_engine):
            response = client.post(
                "/api/v1/search/documents",
                json={
                    "query": "test",
                    "page": 2,
                    "page_size": 5
                }
            )

            assert response.status_code == 200
            data = response.json()
            search_data = data["data"]
            assert search_data["page"] == 1  # mock 返回第1页
            assert search_data["page_size"] == 10  # mock 返回每页10条

    @pytest.mark.asyncio
    async def test_search_documents_empty_query(self, client, mock_search_engine):
        """测试空查询"""
        with patch("src.api.routes.search.get_search_engine", return_value=mock_search_engine):
            response = client.post(
                "/api/v1/search/documents",
                json={
                    "query": "",
                    "method": "hybrid"
                }
            )

            # 空查询可能返回 400 或者返回空结果，取决于实现
            assert response.status_code in [200, 400]

    @pytest.mark.asyncio
    async def test_search_documents_engine_error(self, client, mock_search_engine):
        """测试搜索引擎错误"""
        mock_search_engine.search = AsyncMock(side_effect=Exception("Search engine error"))

        with patch("src.api.routes.search.get_search_engine", return_value=mock_search_engine):
            response = client.post(
                "/api/v1/search/documents",
                json={"query": "test"}
            )

            assert response.status_code == 500

    def test_get_search_methods_success(self, client):
        """测试获取搜索方法列表"""
        response = client.get("/api/v1/search/methods")

        assert response.status_code == 200
        data = response.json()

        assert "data" in data
        methods_data = data["data"]
        assert "methods" in methods_data
        assert "default" in methods_data

        # 验证方法列表
        methods = methods_data["methods"]
        assert len(methods) >= 3
        method_values = [m["value"] for m in methods]
        assert "hybrid" in method_values
        assert "vector" in method_values
        assert "bm25" in method_values

    def test_get_search_stats_success(self, client):
        """测试获取搜索统计"""
        response = client.get("/api/v1/search/stats")

        assert response.status_code == 200
        data = response.json()

        assert "data" in data
        stats_data = data["data"]
        assert "total_searches" in stats_data
        assert "popular_queries" in stats_data
        assert "avg_search_time_ms" in stats_data


# ========================================================================
# 搜索方法测试
# ========================================================================

class TestSearchMethods:
    """测试不同的搜索方法"""

    @pytest.mark.asyncio
    async def test_vector_search(self, client, mock_search_engine):
        """测试向量搜索"""
        with patch("src.api.routes.search.get_search_engine", return_value=mock_search_engine):
            response = client.post(
                "/api/v1/search/documents",
                json={"query": "test", "method": "vector"}
            )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_bm25_search(self, client, mock_search_engine):
        """测试 BM25 搜索"""
        with patch("src.api.routes.search.get_search_engine", return_value=mock_search_engine):
            response = client.post(
                "/api/v1/search/documents",
                json={"query": "test", "method": "bm25"}
            )

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_hybrid_search(self, client, mock_search_engine):
        """测试混合搜索"""
        with patch("src.api.routes.search.get_search_engine", return_value=mock_search_engine):
            response = client.post(
                "/api/v1/search/documents",
                json={"query": "test", "method": "hybrid"}
            )

            assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
