"""
Unit tests for citation components
测试引用组件的过滤、排序和显示功能
"""
import pytest
from datetime import datetime, timedelta
from src.ui.components.citation import (
    filter_citations_by_type,
    sort_citations,
    create_citation_badge,
    render_citation_stats,
    render_quality_score
)


class TestFilterCitationsByType:
    """测试引用过滤功能"""

    def test_filter_by_single_source(self):
        """测试按单个来源类型过滤"""
        citations = [
            {"source_type": "jira", "source_id": "PROJ-1"},
            {"source_type": "confluence", "source_id": "page-1"},
            {"source_type": "local", "source_id": "doc-1"}
        ]
        result = filter_citations_by_type(citations, ["jira"])
        assert len(result) == 1
        assert result[0]["source_type"] == "jira"

    def test_filter_by_multiple_sources(self):
        """测试按多个来源类型过滤"""
        citations = [
            {"source_type": "jira", "source_id": "PROJ-1"},
            {"source_type": "confluence", "source_id": "page-1"},
            {"source_type": "local", "source_id": "doc-1"}
        ]
        result = filter_citations_by_type(citations, ["jira", "confluence"])
        assert len(result) == 2
        assert all(c["source_type"] in ["jira", "confluence"] for c in result)

    def test_filter_case_insensitive(self):
        """测试大小写不敏感过滤"""
        citations = [
            {"source_type": "JIRA", "source_id": "PROJ-1"},
            {"source_type": "Confluence", "source_id": "page-1"}
        ]
        result = filter_citations_by_type(citations, ["jira", "confluence"])
        assert len(result) == 2

    def test_filter_empty_list(self):
        """测试空来源列表返回全部"""
        citations = [
            {"source_type": "jira", "source_id": "PROJ-1"},
            {"source_type": "confluence", "source_id": "page-1"}
        ]
        result = filter_citations_by_type(citations, None)
        assert len(result) == 2

        result = filter_citations_by_type(citations, [])
        assert len(result) == 2

    def test_filter_no_matches(self):
        """测试没有匹配结果"""
        citations = [
            {"source_type": "jira", "source_id": "PROJ-1"}
        ]
        result = filter_citations_by_type(citations, ["confluence"])
        assert len(result) == 0


class TestSortCitations:
    """测试引用排序功能"""

    def test_sort_by_quality(self):
        """测试按质量分数排序"""
        citations = [
            {"quality_score": 0.5, "source_id": "doc-1"},
            {"quality_score": 0.9, "source_id": "doc-2"},
            {"quality_score": 0.7, "source_id": "doc-3"}
        ]
        result = sort_citations(citations, "quality")
        assert result[0]["source_id"] == "doc-2"
        assert result[1]["source_id"] == "doc-3"
        assert result[2]["source_id"] == "doc-1"

    def test_sort_by_relevance(self):
        """测试按相关度排序"""
        citations = [
            {"relevance_score": 0.6, "source_id": "doc-1"},
            {"relevance_score": 0.8, "source_id": "doc-2"},
            {"relevance_score": 0.4, "source_id": "doc-3"}
        ]
        result = sort_citations(citations, "relevance")
        assert result[0]["source_id"] == "doc-2"
        assert result[1]["source_id"] == "doc-1"
        assert result[2]["source_id"] == "doc-3"

    def test_sort_by_usage(self):
        """测试按使用次数排序"""
        citations = [
            {"usage_count": 10, "source_id": "doc-1"},
            {"usage_count": 50, "source_id": "doc-2"},
            {"usage_count": 25, "source_id": "doc-3"}
        ]
        result = sort_citations(citations, "usage")
        assert result[0]["source_id"] == "doc-2"
        assert result[1]["source_id"] == "doc-3"
        assert result[2]["source_id"] == "doc-1"

    def test_sort_by_freshness(self):
        """测试按时效性排序"""
        citations = [
            {"document_created_at": "2024-01-01", "source_id": "doc-1"},
            {"document_created_at": "2024-03-01", "source_id": "doc-2"},
            {"document_created_at": "2024-02-01", "source_id": "doc-3"}
        ]
        result = sort_citations(citations, "freshness")
        assert result[0]["source_id"] == "doc-2"
        assert result[1]["source_id"] == "doc-3"
        assert result[2]["source_id"] == "doc-1"

    def test_sort_default_to_quality(self):
        """测试默认排序方式为质量"""
        citations = [
            {"quality_score": 0.5, "source_id": "doc-1"},
            {"quality_score": 0.9, "source_id": "doc-2"}
        ]
        result = sort_citations(citations)
        assert result[0]["source_id"] == "doc-2"

    def test_sort_invalid_method(self):
        """测试无效排序方法返回原列表"""
        citations = [
            {"quality_score": 0.5, "source_id": "doc-1"},
            {"quality_score": 0.9, "source_id": "doc-2"}
        ]
        result = sort_citations(citations, "invalid_method")
        # Should return original list when sort method is invalid
        assert len(result) == 2

    def test_sort_missing_field(self):
        """测试缺失字段时的处理"""
        citations = [
            {"source_id": "doc-1"},  # Missing quality_score
            {"quality_score": 0.9, "source_id": "doc-2"}
        ]
        result = sort_citations(citations, "quality")
        # Should handle missing fields gracefully
        assert len(result) == 2


class TestCreateCitationBadge:
    """测试引用徽章创建"""

    def test_badge_with_valid_url(self):
        """测试有效URL的徽章"""
        citation = {
            "source_id": "PROJ-1",
            "source_type": "jira",
            "source_url": "https://jira.example.com/browse/PROJ-1",
            "relevance_score": 0.85
        }
        html = create_citation_badge(citation)
        assert "PROJ-1" in html
        assert "JIRA" in html
        assert "https://jira.example.com" in html
        assert "打开原文" in html
        assert "↗" in html

    def test_badge_with_invalid_url(self):
        """测试无效URL的徽章"""
        citation = {
            "source_id": "PROJ-1",
            "source_type": "jira",
            "source_url": "invalid-url",
            "relevance_score": 0.85
        }
        html = create_citation_badge(citation)
        assert "⚠️" in html
        assert "无效链接" in html

    def test_badge_with_rank(self):
        """测试带排名的徽章"""
        citation = {
            "source_id": "PROJ-1",
            "source_type": "jira",
            "relevance_score": 0.85
        }
        html = create_citation_badge(citation, rank=1)
        assert "#1" in html

    def test_badge_with_quality_score(self):
        """测试带质量分数的徽章"""
        citation = {
            "source_id": "PROJ-1",
            "source_type": "jira",
            "relevance_score": 0.85,
            "quality_score": 0.92
        }
        html = create_citation_badge(citation)
        assert "质量" in html
        assert "92%" in html


class TestRenderCitationStats:
    """测试引用统计渲染"""

    def test_stats_with_high_usage(self):
        """测试高使用次数的统计（热门）"""
        stats = {
            "usage_count": 60,
            "unique_queries": 30,
            "last_used_at": datetime.now().isoformat(),
            "avg_relevance": 0.85
        }
        html = render_citation_stats(stats)
        assert "🔥" in html
        assert "热门" in html
        assert "60" in html

    def test_stats_with_medium_usage(self):
        """测试中等使用次数的统计（常用）"""
        stats = {
            "usage_count": 30,
            "unique_queries": 15,
            "last_used_at": datetime.now().isoformat(),
            "avg_relevance": 0.75
        }
        html = render_citation_stats(stats)
        assert "⭐" in html
        assert "常用" in html

    def test_stats_with_low_usage(self):
        """测试低使用次数的统计（普通）"""
        stats = {
            "usage_count": 5,
            "unique_queries": 3,
            "last_used_at": datetime.now().isoformat(),
            "avg_relevance": 0.65
        }
        html = render_citation_stats(stats)
        assert "📌" in html
        assert "普通" in html

    def test_stats_time_display_today(self):
        """测试时间显示 - 今天"""
        stats = {
            "usage_count": 10,
            "unique_queries": 5,
            "last_used_at": datetime.now().isoformat(),
            "avg_relevance": 0.75
        }
        html = render_citation_stats(stats)
        assert "今天" in html

    def test_stats_time_display_days_ago(self):
        """测试时间显示 - 几天前"""
        last_used = datetime.now() - timedelta(days=3)
        stats = {
            "usage_count": 10,
            "unique_queries": 5,
            "last_used_at": last_used.isoformat(),
            "avg_relevance": 0.75
        }
        html = render_citation_stats(stats)
        assert "天前" in html


class TestRenderQualityScore:
    """测试质量分数渲染"""

    def test_excellent_quality(self):
        """测试优秀质量（>= 0.8）"""
        html = render_quality_score(0.85)
        assert "⭐" in html
        assert "85%" in html
        assert "优秀" in html

    def test_good_quality(self):
        """测试良好质量（0.6-0.8）"""
        html = render_quality_score(0.7)
        assert "70%" in html
        assert "良好" in html

    def test_average_quality(self):
        """测试一般质量（< 0.6）"""
        html = render_quality_score(0.5)
        assert "50%" in html
        assert "一般" in html

    def test_quality_with_breakdown(self):
        """测试带详细评分的质量"""
        breakdown = {
            "relevance": 0.9,
            "freshness": 0.7,
            "coverage": 0.8,
            "popularity": 0.6
        }
        html = render_quality_score(0.75, breakdown)
        assert "相关度" in html
        assert "时效性" in html
        assert "覆盖度" in html
        assert "热度" in html


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
