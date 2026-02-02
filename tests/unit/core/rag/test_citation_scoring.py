"""
Unit tests for citation scoring module
"""

import pytest
from datetime import datetime, timedelta
from src.core.rag.citation_scoring import (
    calculate_citation_quality,
    calculate_freshness_score,
    calculate_coverage_score,
    calculate_popularity_score,
    batch_calculate_quality_scores,
    sort_by_quality
)


class TestCalculateFreshnessScore:
    """测试时效性评分函数"""

    def test_recent_document_high_score(self):
        """测试最近的文档得分高"""
        # 3天前
        recent = (datetime.now() - timedelta(days=3)).isoformat()
        score = calculate_freshness_score(recent)
        assert score == 1.0, "3天内的文档应该得满分"

    def test_one_month_document(self):
        """测试一个月前的文档"""
        one_month_ago = (datetime.now() - timedelta(days=25)).isoformat()
        score = calculate_freshness_score(one_month_ago)
        assert 0.85 <= score <= 0.95, "1个月内的文档应该得0.9左右"

    def test_one_year_document(self):
        """测试一年前的文档"""
        one_year_ago = (datetime.now() - timedelta(days=200)).isoformat()
        score = calculate_freshness_score(one_year_ago)
        assert 0.5 <= score <= 0.7, "半年到一年的文档应该得0.6左右"

    def test_old_document_lower_score(self):
        """测试很旧的文档得分低"""
        old = (datetime.now() - timedelta(days=1000)).isoformat()
        score = calculate_freshness_score(old)
        assert score <= 0.5, "超过2年的文档得分应该低于0.5"

    def test_no_timestamp_default_score(self):
        """测试没有时间戳返回默认分数"""
        score = calculate_freshness_score(None)
        assert score == 0.5, "没有时间戳应该返回0.5"

    def test_invalid_timestamp_default_score(self):
        """测试无效时间戳返回默认分数"""
        score = calculate_freshness_score("invalid-timestamp")
        assert score == 0.5, "无效时间戳应该返回0.5"


class TestCalculateCoverageScore:
    """测试关键词覆盖度评分函数"""

    def test_no_highlights_zero_score(self):
        """测试没有高亮返回0分"""
        score = calculate_coverage_score([], "test query")
        assert score == 0.0

    def test_empty_query_zero_score(self):
        """测试空查询返回0分"""
        score = calculate_coverage_score([(0, 4)], "")
        assert score == 0.0

    def test_single_highlight(self):
        """测试单个高亮区域"""
        highlights = [(10, 20)]  # 10个字符
        score = calculate_coverage_score(highlights, "测试查询")
        assert 0.0 < score <= 1.0, "应该返回有效分数"

    def test_multiple_highlights(self):
        """测试多个高亮区域"""
        highlights = [(10, 20), (30, 40), (50, 60)]
        score = calculate_coverage_score(highlights, "测试 查询 关键词")
        assert 0.3 < score <= 1.0, "多个高亮应该得到较高分数"

    def test_large_highlights_high_score(self):
        """测试大面积高亮得高分"""
        highlights = [(0, 100), (110, 200)]  # 大量高亮字符
        score = calculate_coverage_score(highlights, "测试")
        assert score >= 0.8, "大量高亮应该得高分"


class TestCalculatePopularityScore:
    """测试流行度评分函数"""

    def test_zero_usage_zero_score(self):
        """测试0次使用返回0分"""
        score = calculate_popularity_score(0, 100)
        assert score == 0.0

    def test_max_usage_full_score(self):
        """测试最大使用次数接近满分"""
        score = calculate_popularity_score(100, 100)
        assert score == 1.0

    def test_logarithmic_scaling(self):
        """测试对数归一化"""
        score_10 = calculate_popularity_score(10, 100)
        score_50 = calculate_popularity_score(50, 100)
        score_90 = calculate_popularity_score(90, 100)

        # 对数增长，差距应该递减
        assert score_10 < score_50 < score_90
        assert (score_50 - score_10) > (score_90 - score_50)

    def test_negative_usage_returns_zero(self):
        """测试负数使用次数返回0"""
        score = calculate_popularity_score(-5, 100)
        assert score == 0.0


class TestCalculateCitationQuality:
    """测试综合质量评分函数"""

    def test_quality_score_range(self):
        """测试质量分数在0-1范围内"""
        score, breakdown = calculate_citation_quality(
            relevance_score=0.8,
            query="测试查询",
            highlights=[(10, 20)],
            metadata={"created_at": datetime.now().isoformat()},
            usage_stats={"total_references": 50, "max_usage": 100}
        )
        assert 0.0 <= score <= 1.0, "质量分数应该在0-1范围内"

    def test_breakdown_contains_all_components(self):
        """测试评分细分包含所有组件"""
        score, breakdown = calculate_citation_quality(
            relevance_score=0.8,
            query="测试",
            highlights=[(0, 5)],
            metadata={"created_at": datetime.now().isoformat()},
            usage_stats={"total_references": 10, "max_usage": 100}
        )

        assert "relevance" in breakdown
        assert "freshness" in breakdown
        assert "coverage" in breakdown
        assert "popularity" in breakdown

    def test_high_quality_citation(self):
        """测试高质量引用"""
        recent = (datetime.now() - timedelta(days=1)).isoformat()
        score, breakdown = calculate_citation_quality(
            relevance_score=0.95,  # 高相关性
            query="重要关键词",
            highlights=[(0, 50), (60, 100)],  # 大量高亮
            metadata={"created_at": recent},  # 最新文档
            usage_stats={"total_references": 100, "max_usage": 100}  # 热门
        )

        assert score >= 0.85, "高质量引用应该得高分"
        assert breakdown["relevance"] >= 0.9
        assert breakdown["freshness"] >= 0.9
        assert breakdown["popularity"] >= 0.9

    def test_low_quality_citation(self):
        """测试低质量引用"""
        old = (datetime.now() - timedelta(days=1000)).isoformat()
        score, breakdown = calculate_citation_quality(
            relevance_score=0.3,  # 低相关性
            query="测试",
            highlights=[],  # 无高亮
            metadata={"created_at": old},  # 旧文档
            usage_stats={"total_references": 1, "max_usage": 100}  # 不热门
        )

        assert score <= 0.5, "低质量引用应该得低分"

    def test_no_usage_stats_default_popularity(self):
        """测试没有使用统计时使用默认流行度"""
        score, breakdown = calculate_citation_quality(
            relevance_score=0.8,
            query="测试",
            highlights=[(0, 5)],
            metadata={"created_at": datetime.now().isoformat()},
            usage_stats=None
        )

        assert breakdown["popularity"] == 0.5, "没有统计信息应该使用默认流行度0.5"


class TestBatchCalculateQualityScores:
    """测试批量质量评分函数"""

    def test_empty_list(self):
        """测试空列表"""
        result = batch_calculate_quality_scores([])
        assert result == []

    def test_batch_processing(self):
        """测试批量处理"""
        citations = [
            {
                "relevance_score": 0.8,
                "query": "测试1",
                "highlights": [(0, 5)],
                "metadata": {"created_at": datetime.now().isoformat()},
                "source_id": "TEST-1"
            },
            {
                "relevance_score": 0.7,
                "query": "测试2",
                "highlights": [(0, 10)],
                "metadata": {"created_at": datetime.now().isoformat()},
                "source_id": "TEST-2"
            }
        ]

        result = batch_calculate_quality_scores(citations)

        assert len(result) == 2
        assert all("quality_score" in c for c in result)
        assert all("quality_breakdown" in c for c in result)

    def test_batch_with_usage_stats(self):
        """测试带使用统计的批量处理"""
        citations = [
            {
                "relevance_score": 0.8,
                "query": "测试",
                "highlights": [(0, 5)],
                "metadata": {"created_at": datetime.now().isoformat()},
                "source_id": "TEST-1"
            }
        ]

        usage_stats_map = {
            "TEST-1": {
                "total_references": 50,
                "unique_queries": 10,
                "avg_relevance": 0.8
            }
        }

        result = batch_calculate_quality_scores(citations, usage_stats_map)

        assert result[0]["quality_score"] > 0
        assert result[0]["quality_breakdown"]["popularity"] > 0

    def test_failed_citation_gets_default_score(self):
        """测试失败的引用获得默认分数"""
        # 故意提供不完整的数据
        citations = [{"source_id": "TEST-1"}]

        result = batch_calculate_quality_scores(citations)

        assert len(result) == 1
        # 不完整数据会被计算，但由于缺失字段默认为0，所以分数较低
        assert 0.0 <= result[0]["quality_score"] <= 0.5
        assert "quality_breakdown" in result[0]


class TestSortByQuality:
    """测试按质量排序函数"""

    def test_sort_descending(self):
        """测试降序排序"""
        citations = [
            {"quality_score": 0.5, "source_id": "C"},
            {"quality_score": 0.9, "source_id": "A"},
            {"quality_score": 0.7, "source_id": "B"}
        ]

        sorted_citations = sort_by_quality(citations, descending=True)

        scores = [c["quality_score"] for c in sorted_citations]
        assert scores == [0.9, 0.7, 0.5]

    def test_sort_ascending(self):
        """测试升序排序"""
        citations = [
            {"quality_score": 0.5, "source_id": "C"},
            {"quality_score": 0.9, "source_id": "A"},
            {"quality_score": 0.7, "source_id": "B"}
        ]

        sorted_citations = sort_by_quality(citations, descending=False)

        scores = [c["quality_score"] for c in sorted_citations]
        assert scores == [0.5, 0.7, 0.9]

    def test_missing_quality_score_defaults_to_zero(self):
        """测试缺失质量分数的引用默认为0"""
        citations = [
            {"quality_score": 0.5},
            {},  # 缺失 quality_score
            {"quality_score": 0.9}
        ]

        sorted_citations = sort_by_quality(citations, descending=True)

        # 缺失分数的应该排在最后
        assert sorted_citations[-1] == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
