"""
Unit tests for RAG filters
"""

import pytest
from datetime import datetime, timedelta

from src.core.rag.models import RetrievalResult, TimeRange, FilterConfig
from src.core.rag.filters import (
    SourceFilter,
    TimeRangeFilter,
    MetadataFilter,
    CompositeFilter,
)
from src.core.rag.filters.composite_filter import create_filter_from_config


# ========================================================================
# Fixtures
# ========================================================================

@pytest.fixture
def sample_results():
    """创建示例检索结果"""
    # 使用相对于 now 的时间，确保测试稳定
    now = datetime.now()

    return [
        RetrievalResult(
            chunk_id="PROJ-123_chunk_0",
            parent_id="PROJ-123",
            content="High priority bug",
            metadata={
                "source": "jira",
                "doc_type": "issue",
                "priority": "High",
                "status": "Open",
                "created_at": (now - timedelta(hours=12)).isoformat()  # 12小时前
            },
            score=0.9,
            distance=0.1,
            chunk_index=0
        ),
        RetrievalResult(
            chunk_id="CONF-456_chunk_0",
            parent_id="CONF-456",
            content="Confluence documentation",
            metadata={
                "source": "confluence",
                "doc_type": "page",
                "created_at": (now - timedelta(days=5)).isoformat()  # 5天前
            },
            score=0.8,
            distance=0.2,
            chunk_index=0
        ),
        RetrievalResult(
            chunk_id="PROJ-789_chunk_0",
            parent_id="PROJ-789",
            content="Medium priority task",
            metadata={
                "source": "jira",
                "doc_type": "issue",
                "priority": "Medium",
                "status": "In Progress",
                "created_at": (now - timedelta(days=30)).isoformat()  # 30天前
            },
            score=0.7,
            distance=0.3,
            chunk_index=0
        ),
    ]


# ========================================================================
# SourceFilter Tests
# ========================================================================

class TestSourceFilter:
    """SourceFilter 测试"""

    def test_single_source(self, sample_results):
        """测试单个来源过滤"""
        filter_obj = SourceFilter(["jira"])
        results = filter_obj.apply(sample_results)

        assert len(results) == 2
        assert all(r.metadata["source"] == "jira" for r in results)

    def test_multiple_sources(self, sample_results):
        """测试多个来源过滤"""
        filter_obj = SourceFilter(["jira", "confluence"])
        results = filter_obj.apply(sample_results)

        assert len(results) == 3

    def test_no_source(self, sample_results):
        """测试空来源过滤"""
        filter_obj = SourceFilter([])
        results = filter_obj.apply(sample_results)

        assert len(results) == 3  # 不过滤

    def test_to_chroma_where_single(self):
        """测试转换为 ChromaDB where 子句（单个来源）"""
        filter_obj = SourceFilter(["jira"])
        where = filter_obj.to_chroma_where()

        assert where == {"source": "jira"}

    def test_to_chroma_where_multiple(self):
        """测试转换为 ChromaDB where 子句（多个来源）"""
        filter_obj = SourceFilter(["jira", "confluence"])
        where = filter_obj.to_chroma_where()

        assert where == {"source": {"$in": ["jira", "confluence"]}}

    def test_is_empty(self):
        """测试是否为空"""
        assert SourceFilter([]).is_empty()
        assert not SourceFilter(["jira"]).is_empty()

    def test_add_remove_source(self):
        """测试添加和移除来源"""
        filter_obj = SourceFilter([])
        assert filter_obj.is_empty()

        filter_obj.add_source("jira")
        assert not filter_obj.is_empty()
        assert "jira" in filter_obj.sources

        filter_obj.remove_source("jira")
        assert filter_obj.is_empty()


# ========================================================================
# TimeRangeFilter Tests
# ========================================================================

class TestTimeRangeFilter:
    """TimeRangeFilter 测试"""

    def test_preset_7d(self, sample_results):
        """测试预设 7 天过滤"""
        time_range = TimeRange(preset="7d")
        filter_obj = TimeRangeFilter(time_range)
        results = filter_obj.apply(sample_results)

        # 应该包含最近 7 天的结果（前两个）
        assert len(results) == 2
        assert results[0].chunk_id == "PROJ-123_chunk_0"
        assert results[1].chunk_id == "CONF-456_chunk_0"

    def test_preset_1d(self, sample_results):
        """测试预设 1 天过滤"""
        time_range = TimeRange(preset="1d")
        filter_obj = TimeRangeFilter(time_range)
        results = filter_obj.apply(sample_results)

        # 应该只包含最近 1 天的结果
        assert len(results) == 1
        assert results[0].chunk_id == "PROJ-123_chunk_0"

    def test_custom_range(self, sample_results):
        """测试自定义时间范围"""
        now = datetime.now()
        start = now - timedelta(days=10)  # 10天前
        end = now  # 现在
        time_range = TimeRange(start=start, end=end)
        filter_obj = TimeRangeFilter(time_range)
        results = filter_obj.apply(sample_results)

        # 应该包含 12小时前和5天前的结果
        assert len(results) == 2

    def test_to_chroma_where_preset(self):
        """测试转换为 ChromaDB where 子句（预设）"""
        time_range = TimeRange(preset="7d")
        filter_obj = TimeRangeFilter(time_range)
        where = filter_obj.to_chroma_where()

        assert "created_at" in where
        assert "$gte" in where["created_at"]

    def test_is_empty(self):
        """测试是否为空"""
        assert TimeRangeFilter(None).is_empty()
        assert not TimeRangeFilter(TimeRange(preset="7d")).is_empty()

    def test_set_preset(self):
        """测试设置预设"""
        filter_obj = TimeRangeFilter(None)
        assert filter_obj.is_empty()

        filter_obj.set_preset("7d")
        assert not filter_obj.is_empty()
        assert filter_obj.time_range.preset == "7d"


# ========================================================================
# MetadataFilter Tests
# ========================================================================

class TestMetadataFilter:
    """MetadataFilter 测试"""

    def test_single_condition(self, sample_results):
        """测试单个条件过滤"""
        filter_obj = MetadataFilter({"priority": "High"})
        results = filter_obj.apply(sample_results)

        assert len(results) == 1
        assert results[0].metadata["priority"] == "High"

    def test_multiple_conditions(self, sample_results):
        """测试多个条件过滤（AND 逻辑）"""
        filter_obj = MetadataFilter({"source": "jira", "priority": "High"})
        results = filter_obj.apply(sample_results)

        assert len(results) == 1
        assert results[0].chunk_id == "PROJ-123_chunk_0"

    def test_list_value(self, sample_results):
        """测试列表值过滤（IN 操作）"""
        filter_obj = MetadataFilter({"priority": ["High", "Medium"]})
        results = filter_obj.apply(sample_results)

        assert len(results) == 2

    def test_to_chroma_where(self):
        """测试转换为 ChromaDB where 子句"""
        filter_obj = MetadataFilter({"priority": "High", "status": "Open"})
        where = filter_obj.to_chroma_where()

        assert "$and" in where
        assert len(where["$and"]) == 2

    def test_is_empty(self):
        """测试是否为空"""
        assert MetadataFilter({}).is_empty()
        assert MetadataFilter(None).is_empty()
        assert not MetadataFilter({"priority": "High"}).is_empty()

    def test_add_remove_condition(self):
        """测试添加和移除条件"""
        filter_obj = MetadataFilter({})
        assert filter_obj.is_empty()

        filter_obj.add_condition("priority", "High")
        assert not filter_obj.is_empty()
        assert filter_obj.get_condition("priority") == "High"

        filter_obj.remove_condition("priority")
        assert filter_obj.is_empty()


# ========================================================================
# CompositeFilter Tests
# ========================================================================

class TestCompositeFilter:
    """CompositeFilter 测试"""

    def test_and_logic(self, sample_results):
        """测试 AND 逻辑"""
        filters = [
            SourceFilter(["jira"]),
            MetadataFilter({"priority": "High"})
        ]
        filter_obj = CompositeFilter(filters, logic="AND")
        results = filter_obj.apply(sample_results)

        assert len(results) == 1
        assert results[0].chunk_id == "PROJ-123_chunk_0"

    def test_or_logic(self, sample_results):
        """测试 OR 逻辑"""
        filters = [
            SourceFilter(["confluence"]),
            MetadataFilter({"priority": "High"})
        ]
        filter_obj = CompositeFilter(filters, logic="OR")
        results = filter_obj.apply(sample_results)

        # 应该包含 Confluence 文档或高优先级 Issue
        assert len(results) == 2

    def test_empty_filters(self, sample_results):
        """测试空过滤器列表"""
        filter_obj = CompositeFilter([])
        results = filter_obj.apply(sample_results)

        assert len(results) == 3  # 不过滤

    def test_single_filter(self, sample_results):
        """测试单个过滤器"""
        filters = [SourceFilter(["jira"])]
        filter_obj = CompositeFilter(filters)
        results = filter_obj.apply(sample_results)

        assert len(results) == 2

    def test_to_chroma_where_and(self):
        """测试转换为 ChromaDB where 子句（AND 逻辑）"""
        filters = [
            SourceFilter(["jira"]),
            MetadataFilter({"priority": "High"})
        ]
        filter_obj = CompositeFilter(filters, logic="AND")
        where = filter_obj.to_chroma_where()

        assert "$and" in where
        assert len(where["$and"]) == 2

    def test_to_chroma_where_or(self):
        """测试转换为 ChromaDB where 子句（OR 逻辑）"""
        filters = [
            SourceFilter(["jira"]),
            SourceFilter(["confluence"])
        ]
        filter_obj = CompositeFilter(filters, logic="OR")
        where = filter_obj.to_chroma_where()

        assert "$or" in where

    def test_is_empty(self):
        """测试是否为空"""
        assert CompositeFilter([]).is_empty()
        assert CompositeFilter([SourceFilter([])]).is_empty()
        assert not CompositeFilter([SourceFilter(["jira"])]).is_empty()


# ========================================================================
# FilterConfig Tests
# ========================================================================

class TestFilterConfig:
    """FilterConfig 测试"""

    def test_to_chroma_where_single_condition(self):
        """测试单个条件转换"""
        config = FilterConfig(sources=["jira"])
        where = config.to_chroma_where()

        assert where == {"source": "jira"}

    def test_to_chroma_where_multiple_conditions(self):
        """测试多个条件转换（AND 逻辑）"""
        config = FilterConfig(
            sources=["jira"],
            metadata={"priority": "High"}
        )
        where = config.to_chroma_where()

        assert "$and" in where
        assert len(where["$and"]) == 2

    def test_to_chroma_where_or_logic(self):
        """测试 OR 逻辑"""
        config = FilterConfig(
            sources=["jira", "confluence"],
            logic="OR"
        )
        where = config.to_chroma_where()

        # 只有一个条件，直接返回
        assert "source" in where
        assert "$in" in where["source"]

    def test_to_chroma_where_time_range(self):
        """测试时间范围转换"""
        config = FilterConfig(
            time_range=TimeRange(preset="7d")
        )
        where = config.to_chroma_where()

        assert "created_at" in where

    def test_is_empty(self):
        """测试是否为空"""
        assert FilterConfig().is_empty()
        assert not FilterConfig(sources=["jira"]).is_empty()


# ========================================================================
# Helper Functions Tests
# ========================================================================

class TestCreateFilterFromConfig:
    """create_filter_from_config 测试"""

    def test_create_source_filter(self):
        """测试创建来源过滤器"""
        config = {"sources": ["jira"]}
        filter_obj = create_filter_from_config(config)

        assert isinstance(filter_obj, SourceFilter)

    def test_create_composite_filter(self):
        """测试创建组合过滤器"""
        config = {
            "sources": ["jira"],
            "metadata": {"priority": "High"},
            "logic": "AND"
        }
        filter_obj = create_filter_from_config(config)

        assert isinstance(filter_obj, CompositeFilter)
        assert filter_obj.logic == "AND"
        assert len(filter_obj.filters) == 2

    def test_create_none(self):
        """测试空配置"""
        config = {}
        filter_obj = create_filter_from_config(config)

        assert filter_obj is None

    def test_create_single_filter(self):
        """测试单个过滤器"""
        config = {"sources": ["jira"]}
        filter_obj = create_filter_from_config(config)

        assert isinstance(filter_obj, SourceFilter)
        assert not isinstance(filter_obj, CompositeFilter)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
