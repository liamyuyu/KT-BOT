"""
Integration tests for filters with retrievers
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from src.core.rag.models import RetrievalResult, FilterConfig, TimeRange, RetrievalConfig
from src.core.rag.filters import SourceFilter, TimeRangeFilter, MetadataFilter, CompositeFilter
from src.core.rag.retriever.vector import VectorRetriever
from src.core.vectordb.models import SearchResult, SearchResults


# ========================================================================
# Fixtures
# ========================================================================

@pytest.fixture
def mock_chroma_client():
    """创建模拟的 ChromaDB 客户端"""
    client = Mock()

    # 模拟搜索结果
    def mock_search(**kwargs):
        """模拟搜索方法"""
        now = datetime.now()
        results = [
            SearchResult(
                id="PROJ-123_chunk_0",
                content="High priority bug",
                distance=0.1,
                metadata={
                    "source": "jira",
                    "parent_id": "PROJ-123",
                    "doc_type": "issue",
                    "priority": "High",
                    "status": "Open",
                    "created_at": (now - timedelta(hours=12)).isoformat(),
                    "chunk_index": 0
                }
            ),
            SearchResult(
                id="CONF-456_chunk_0",
                content="Confluence documentation",
                distance=0.2,
                metadata={
                    "source": "confluence",
                    "parent_id": "CONF-456",
                    "doc_type": "page",
                    "created_at": (now - timedelta(days=5)).isoformat(),
                    "chunk_index": 0
                }
            ),
            SearchResult(
                id="PROJ-789_chunk_0",
                content="Medium priority task",
                distance=0.3,
                metadata={
                    "source": "jira",
                    "parent_id": "PROJ-789",
                    "doc_type": "issue",
                    "priority": "Medium",
                    "status": "In Progress",
                    "created_at": (now - timedelta(days=30)).isoformat(),
                    "chunk_index": 0
                }
            ),
        ]

        # 应用 where 过滤（简化版）
        where = kwargs.get("where")
        if where:
            filtered_results = []
            for result in results:
                if _match_where_clause(result.metadata, where):
                    filtered_results.append(result)
            results = filtered_results

        n_results = kwargs.get("n_results", 5)
        limited_results = results[:n_results]

        return SearchResults(
            results=limited_results,
            total=len(limited_results),
            query="test_query",  # 模拟查询文本
            limit=n_results
        )

    client.search = Mock(side_effect=mock_search)
    return client


@pytest.fixture
def mock_llm_manager():
    """创建模拟的 LLM 管理器"""
    manager = Mock()
    embedding_model = AsyncMock()
    embedding_response = Mock()
    embedding_response.embedding = [0.1] * 768
    embedding_model.embed = AsyncMock(return_value=embedding_response)
    manager.create_embedding = Mock(return_value=embedding_model)
    return manager


@pytest.fixture
def vector_retriever(mock_chroma_client, mock_llm_manager):
    """创建 VectorRetriever 实例"""
    return VectorRetriever(
        chroma_client=mock_chroma_client,
        llm_manager=mock_llm_manager,
        collection_name="test_collection",
        config=RetrievalConfig(top_k=10)
    )


# ========================================================================
# Helper Functions
# ========================================================================

def _match_where_clause(metadata: dict, where: dict) -> bool:
    """简化版 where 子句匹配（用于测试）"""
    if not where:
        return True

    # 处理 $and
    if "$and" in where:
        return all(_match_where_clause(metadata, cond) for cond in where["$and"])

    # 处理 $or
    if "$or" in where:
        return any(_match_where_clause(metadata, cond) for cond in where["$or"])

    # 处理普通字段
    for key, value in where.items():
        if key.startswith("$"):
            continue

        if key not in metadata:
            return False

        # 处理操作符
        if isinstance(value, dict):
            meta_value = metadata[key]
            if "$in" in value:
                if meta_value not in value["$in"]:
                    return False
            elif "$gte" in value:
                if meta_value < value["$gte"]:
                    return False
            elif "$lte" in value:
                if meta_value > value["$lte"]:
                    return False
        else:
            if metadata[key] != value:
                return False

    return True


# ========================================================================
# VectorRetriever Integration Tests
# ========================================================================

class TestVectorRetrieverIntegration:
    """VectorRetriever 与过滤器集成测试"""

    @pytest.mark.asyncio
    async def test_retrieve_with_dict_filter(self, vector_retriever):
        """测试使用字典过滤"""
        filters = {"source": "jira"}
        results = await vector_retriever.retrieve("test query", filters=filters)

        # 应该只返回 jira 来源的结果
        assert len(results) == 2
        assert all(r.metadata["source"] == "jira" for r in results)

    @pytest.mark.asyncio
    async def test_retrieve_with_filter_config(self, vector_retriever):
        """测试使用 FilterConfig"""
        filter_config = FilterConfig(sources=["jira"], metadata={"priority": "High"})
        results = await vector_retriever.retrieve("test query", filters=filter_config)

        # 应该只返回 jira 来源且高优先级的结果
        assert len(results) == 1
        assert results[0].metadata["source"] == "jira"
        assert results[0].metadata["priority"] == "High"

    @pytest.mark.asyncio
    async def test_retrieve_with_source_filter(self, vector_retriever):
        """测试使用 SourceFilter"""
        source_filter = SourceFilter(["confluence"])
        results = await vector_retriever.retrieve("test query", filters=source_filter)

        # 应该只返回 confluence 来源的结果
        assert len(results) == 1
        assert results[0].metadata["source"] == "confluence"

    @pytest.mark.asyncio
    async def test_retrieve_with_composite_filter(self, vector_retriever):
        """测试使用 CompositeFilter"""
        filters = CompositeFilter([
            SourceFilter(["jira"]),
            MetadataFilter({"priority": "High"})
        ], logic="AND")

        results = await vector_retriever.retrieve("test query", filters=filters)

        # 应该只返回 jira 来源且高优先级的结果
        assert len(results) == 1
        assert results[0].metadata["source"] == "jira"
        assert results[0].metadata["priority"] == "High"

    @pytest.mark.asyncio
    async def test_retrieve_with_time_filter(self, vector_retriever):
        """测试使用 TimeRangeFilter"""
        time_range = TimeRange(preset="7d")
        time_filter = TimeRangeFilter(time_range)

        results = await vector_retriever.retrieve("test query", filters=time_filter)

        # 应该只返回最近 7 天的结果（前两个）
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_retrieve_no_filter(self, vector_retriever):
        """测试无过滤条件"""
        results = await vector_retriever.retrieve("test query")

        # 应该返回所有结果
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_retrieve_empty_filter_config(self, vector_retriever):
        """测试空 FilterConfig"""
        filter_config = FilterConfig()
        results = await vector_retriever.retrieve("test query", filters=filter_config)

        # 空过滤配置应该返回所有结果
        assert len(results) == 3


# ========================================================================
# Filter to ChromaDB Where Clause Tests
# ========================================================================

class TestFilterToWhereClause:
    """测试过滤器转换为 ChromaDB where 子句"""

    def test_source_filter_to_where(self):
        """测试 SourceFilter 转换"""
        filter_obj = SourceFilter(["jira", "confluence"])
        where = filter_obj.to_chroma_where()

        assert where == {"source": {"$in": ["jira", "confluence"]}}

    def test_time_range_filter_to_where(self):
        """测试 TimeRangeFilter 转换"""
        time_range = TimeRange(preset="7d")
        filter_obj = TimeRangeFilter(time_range)
        where = filter_obj.to_chroma_where()

        assert "created_at" in where
        assert "$gte" in where["created_at"]

    def test_metadata_filter_to_where(self):
        """测试 MetadataFilter 转换"""
        filter_obj = MetadataFilter({"priority": "High", "status": "Open"})
        where = filter_obj.to_chroma_where()

        assert "$and" in where
        assert len(where["$and"]) == 2

    def test_composite_filter_to_where_and(self):
        """测试 CompositeFilter AND 逻辑转换"""
        filters = CompositeFilter([
            SourceFilter(["jira"]),
            MetadataFilter({"priority": "High"})
        ], logic="AND")
        where = filters.to_chroma_where()

        assert "$and" in where
        assert len(where["$and"]) == 2

    def test_composite_filter_to_where_or(self):
        """测试 CompositeFilter OR 逻辑转换"""
        filters = CompositeFilter([
            SourceFilter(["jira"]),
            SourceFilter(["confluence"])
        ], logic="OR")
        where = filters.to_chroma_where()

        assert "$or" in where

    def test_filter_config_to_where(self):
        """测试 FilterConfig 转换"""
        config = FilterConfig(
            sources=["jira"],
            metadata={"priority": "High"},
            logic="AND"
        )
        where = config.to_chroma_where()

        assert "$and" in where
        assert len(where["$and"]) == 2


# ========================================================================
# Edge Cases Tests
# ========================================================================

class TestEdgeCases:
    """边界情况测试"""

    @pytest.mark.asyncio
    async def test_retrieve_with_none_filter(self, vector_retriever):
        """测试 None 过滤器"""
        results = await vector_retriever.retrieve("test query", filters=None)
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_retrieve_with_empty_dict_filter(self, vector_retriever):
        """测试空字典过滤器"""
        results = await vector_retriever.retrieve("test query", filters={})
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_retrieve_with_invalid_filter_type(self, vector_retriever):
        """测试无效过滤器类型"""
        # 应该记录警告并忽略过滤器
        results = await vector_retriever.retrieve("test query", filters="invalid")
        assert len(results) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
