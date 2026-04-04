"""
Citation Quality Scoring Module
引用质量评分模块 - 综合评估引用质量
"""

from datetime import datetime
from typing import Dict, List, Tuple, Optional
import math


def calculate_citation_quality(
    relevance_score: float,
    query: str,
    highlights: List[Tuple[int, int]],
    metadata: Dict,
    usage_stats: Optional[Dict] = None
) -> Tuple[float, Dict[str, float]]:
    """
    计算引用质量综合评分

    质量分数 = 40% 相关性 + 20% 时效性 + 20% 关键词覆盖度 + 20% 使用频率

    Args:
        relevance_score: 检索相关性分数 (0-1)
        query: 查询文本
        highlights: 高亮位置列表
        metadata: 文档元数据（包含 created_at, updated_at 等）
        usage_stats: 使用统计信息（可选）

    Returns:
        Tuple[float, Dict[str, float]]: (综合质量分数, 评分细分)
    """
    # 1. 相关性分数 (40%)
    relevance = float(relevance_score)

    # 2. 时效性分数 (20%)
    created_at = metadata.get("created_at") or metadata.get("updated_at")
    freshness = calculate_freshness_score(created_at)

    # 3. 关键词覆盖度分数 (20%)
    coverage = calculate_coverage_score(highlights, query)

    # 4. 使用频率分数 (20%)
    if usage_stats:
        usage_count = usage_stats.get("total_references", 0)
        max_usage = usage_stats.get("max_usage", 100)  # 全局最大使用次数
        popularity = calculate_popularity_score(usage_count, max_usage)
    else:
        popularity = 0.5  # 默认中等流行度

    # 加权计算综合质量分数
    quality_score = (
        0.40 * relevance +
        0.20 * freshness +
        0.20 * coverage +
        0.20 * popularity
    )

    # 评分细分（用于透明化展示）
    breakdown = {
        "relevance": round(relevance, 3),
        "freshness": round(freshness, 3),
        "coverage": round(coverage, 3),
        "popularity": round(popularity, 3)
    }

    return round(quality_score, 3), breakdown


def calculate_freshness_score(created_at: Optional[str]) -> float:
    """
    计算文档时效性分数（基于创建时间）

    评分策略：
    - 1周内: 1.0
    - 1月内: 0.9
    - 3月内: 0.8
    - 6月内: 0.7
    - 1年内: 0.6
    - 2年内: 0.5
    - 更早: 0.3 - 0.5 (指数衰减)

    Args:
        created_at: 创建时间（ISO格式字符串或datetime对象）

    Returns:
        float: 时效性分数 (0-1)
    """
    if not created_at:
        return 0.5  # 无时间信息，返回中等分数

    try:
        # 解析时间
        if isinstance(created_at, str):
            # 支持多种格式
            if "T" in created_at:
                created_time = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            else:
                created_time = datetime.strptime(created_at, "%Y-%m-%d")
        elif isinstance(created_at, datetime):
            created_time = created_at
        else:
            return 0.5

        # 计算距今天数
        now = datetime.now(created_time.tzinfo) if created_time.tzinfo else datetime.now()
        days_old = (now - created_time).days

        # 分段评分
        if days_old < 7:
            return 1.0
        elif days_old < 30:
            return 0.9
        elif days_old < 90:
            return 0.8
        elif days_old < 180:
            return 0.7
        elif days_old < 365:
            return 0.6
        elif days_old < 730:
            return 0.5
        else:
            # 2年以上，指数衰减（最低0.3）
            years = days_old / 365.0
            score = 0.5 * math.exp(-0.3 * (years - 2))
            return max(0.3, min(0.5, score))

    except Exception:
        # 解析失败，返回中等分数
        return 0.5


def calculate_coverage_score(highlights: List[Tuple[int, int]], query: str) -> float:
    """
    计算关键词覆盖度分数（查询关键词在文档中的匹配程度）

    评分策略：
    - 基于高亮区域的数量和总字符数
    - 高亮越多、覆盖面越广，分数越高

    Args:
        highlights: 高亮位置列表 [(start, end), ...]
        query: 查询文本

    Returns:
        float: 覆盖度分数 (0-1)
    """
    if not query or not highlights:
        return 0.0

    try:
        # 计算查询关键词数量（中文分词）
        try:
            import jieba
            query_tokens = list(jieba.lcut(query))
            query_tokens = [t for t in query_tokens if len(t) >= 2]  # 过滤单字
        except ImportError:
            # jieba 未安装，简单按空格分词
            query_tokens = [t for t in query.split() if len(t) >= 2]

        num_query_tokens = max(len(query_tokens), 1)

        # 计算高亮区域数量和总字符数
        num_highlights = len(highlights)
        total_highlight_chars = sum(end - start for start, end in highlights)

        # 覆盖度分数组成：
        # - 50% 基于高亮区域数量与查询词数量的比例
        # - 50% 基于高亮字符数（归一化）

        # 高亮区域数量分数（最多为查询词数量）
        region_score = min(1.0, num_highlights / num_query_tokens)

        # 高亮字符数分数（归一化到0-1，假设100字符为满分）
        char_score = min(1.0, total_highlight_chars / 100.0)

        # 加权平均
        coverage_score = 0.5 * region_score + 0.5 * char_score

        return min(1.0, coverage_score)

    except Exception:
        return 0.0


def calculate_popularity_score(usage_count: int, max_usage: int = 100) -> float:
    """
    计算使用频率分数（基于引用次数）

    评分策略：
    - 对数归一化（避免热门文档占据过高权重）
    - 使用次数越多，分数越高（但增长放缓）

    Args:
        usage_count: 引用使用次数
        max_usage: 全局最大使用次数（用于归一化）

    Returns:
        float: 流行度分数 (0-1)
    """
    if usage_count <= 0:
        return 0.0

    if max_usage <= 0:
        max_usage = 100  # 默认值

    # 对数归一化（避免线性增长导致的头部效应）
    # score = log(1 + usage_count) / log(1 + max_usage)
    score = math.log(1 + usage_count) / math.log(1 + max_usage)

    return min(1.0, score)


def batch_calculate_quality_scores(
    citations: List[Dict],
    usage_stats_map: Optional[Dict[str, Dict]] = None
) -> List[Dict]:
    """
    批量计算引用质量分数

    Args:
        citations: 引用列表（每个引用包含 relevance_score, highlights, metadata 等字段）
        usage_stats_map: 使用统计映射 {source_id: stats}（可选）

    Returns:
        List[Dict]: 添加了 quality_score 和 quality_breakdown 的引用列表
    """
    if not citations:
        return []

    # 计算全局最大使用次数（用于归一化）
    max_usage = 100
    if usage_stats_map:
        max_usage = max(
            (stats.get("total_references", 0) for stats in usage_stats_map.values()),
            default=100
        )

    enriched_citations = []
    for citation in citations:
        try:
            # 提取必要字段
            relevance_score = citation.get("relevance_score", 0.5)
            query = citation.get("query", "")
            highlights = citation.get("highlights", [])
            metadata = citation.get("metadata", {})
            source_id = citation.get("source_id", "")

            # 获取使用统计
            usage_stats = None
            if usage_stats_map and source_id in usage_stats_map:
                usage_stats = usage_stats_map[source_id].copy()
                usage_stats["max_usage"] = max_usage

            # 计算质量分数
            quality_score, breakdown = calculate_citation_quality(
                relevance_score=relevance_score,
                query=query,
                highlights=highlights,
                metadata=metadata,
                usage_stats=usage_stats
            )

            # 添加质量分数字段
            enriched_citation = citation.copy()
            enriched_citation["quality_score"] = quality_score
            enriched_citation["quality_breakdown"] = breakdown

            enriched_citations.append(enriched_citation)

        except Exception as e:
            # 单个引用计算失败，保留原始数据但添加默认分数
            enriched_citation = citation.copy()
            enriched_citation["quality_score"] = 0.5
            enriched_citation["quality_breakdown"] = {
                "relevance": 0.5,
                "freshness": 0.5,
                "coverage": 0.5,
                "popularity": 0.5
            }
            enriched_citations.append(enriched_citation)

    return enriched_citations


def sort_by_quality(citations: List[Dict], descending: bool = True) -> List[Dict]:
    """
    按质量分数排序引用列表

    Args:
        citations: 引用列表（必须包含 quality_score 字段）
        descending: 是否降序排序（默认 True，分数高的在前）

    Returns:
        List[Dict]: 排序后的引用列表
    """
    return sorted(
        citations,
        key=lambda x: x.get("quality_score", 0.0),
        reverse=descending
    )
