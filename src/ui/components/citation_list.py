"""
Citation List Component
引用列表组件 - 支持过滤、排序、分组显示
"""

from typing import List, Dict, Any, Optional
from .citation import create_enhanced_citation_card, get_citation_scripts


def filter_citations(
    citations: List[Dict[str, Any]],
    source_types: Optional[List[str]] = None,
    min_quality: float = 0.0
) -> List[Dict[str, Any]]:
    """
    过滤引用列表

    Args:
        citations: 引用列表
        source_types: 来源类型过滤（如 ['jira', 'confluence']）
        min_quality: 最低质量分数

    Returns:
        过滤后的引用列表
    """
    filtered = citations

    # 按来源类型过滤
    if source_types:
        source_types_lower = [st.lower() for st in source_types]
        filtered = [
            c for c in filtered
            if c.get("source_type", "").lower() in source_types_lower
        ]

    # 按质量分数过滤
    if min_quality > 0:
        filtered = [
            c for c in filtered
            if c.get("quality_score", 0) >= min_quality
        ]

    return filtered


def sort_citations(
    citations: List[Dict[str, Any]],
    sort_by: str = "quality"
) -> List[Dict[str, Any]]:
    """
    排序引用列表

    Args:
        citations: 引用列表
        sort_by: 排序方式（quality, relevance, usage, freshness）

    Returns:
        排序后的引用列表
    """
    if sort_by == "quality":
        # 按质量分数降序
        return sorted(
            citations,
            key=lambda x: x.get("quality_score", 0),
            reverse=True
        )
    elif sort_by == "relevance":
        # 按相关度降序
        return sorted(
            citations,
            key=lambda x: x.get("relevance_score", 0),
            reverse=True
        )
    elif sort_by == "usage":
        # 按使用次数降序
        return sorted(
            citations,
            key=lambda x: x.get("usage_count", 0),
            reverse=True
        )
    elif sort_by == "freshness":
        # 按文档时间降序（最新的在前）
        def get_timestamp(citation):
            created_at = citation.get("document_created_at")
            if not created_at:
                return ""
            return str(created_at)

        return sorted(
            citations,
            key=get_timestamp,
            reverse=True
        )
    else:
        # 默认保持原顺序
        return citations


def group_citations_by_type(
    citations: List[Dict[str, Any]]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    按来源类型分组引用

    Args:
        citations: 引用列表

    Returns:
        分组后的字典 {source_type: [citations]}
    """
    groups = {}
    for citation in citations:
        source_type = citation.get("source_type", "unknown").upper()
        if source_type not in groups:
            groups[source_type] = []
        groups[source_type].append(citation)

    return groups


def render_citation_list(
    citations: List[Dict[str, Any]],
    filters: Optional[Dict[str, Any]] = None,
    sort_by: str = "quality",
    show_stats: bool = True,
    group_by_type: bool = False,
    max_display: int = 10
) -> str:
    """
    渲染可过滤、可排序的引用列表

    Args:
        citations: 引用列表
        filters: 过滤条件字典（source_types, min_quality）
        sort_by: 排序方式
        show_stats: 是否显示统计信息
        group_by_type: 是否按来源类型分组
        max_display: 最多显示数量

    Returns:
        HTML 字符串
    """
    if not citations:
        return """
        <div style="padding: 20px; text-align: center; color: #6B778C; font-size: 0.9em;">
            暂无引用信息
        </div>
        """

    # 应用过滤
    if filters:
        citations = filter_citations(
            citations,
            source_types=filters.get("source_types"),
            min_quality=filters.get("min_quality", 0.0)
        )

    # 应用排序
    citations = sort_citations(citations, sort_by)

    # 限制显示数量
    total_count = len(citations)
    displayed_citations = citations[:max_display]

    html = []

    # 标题和统计
    sort_labels = {
        "quality": "质量优先",
        "relevance": "相关度优先",
        "usage": "热门优先",
        "freshness": "时效性优先"
    }
    sort_label = sort_labels.get(sort_by, sort_by)

    html.append(f"""
    <div style="margin-bottom: 16px; padding: 12px; background: #F4F5F7;
                border-radius: 8px; display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h3 style="margin: 0 0 4px 0; color: #172B4D; font-size: 1.1em;">📚 引用来源</h3>
            <p style="margin: 0; color: #6B778C; font-size: 0.85em;">
                共 {total_count} 个来源 · 排序方式: {sort_label}
            </p>
        </div>
    """)

    # 批量操作按钮
    if len(displayed_citations) > 1:
        html.append("""
        <div style="display: flex; gap: 8px;">
            <button onclick="expandAllCitations()"
                    style="padding: 6px 12px; background: white; border: 1px solid #DFE1E6;
                           border-radius: 4px; cursor: pointer; font-size: 0.85em; color: #42526E;">
                全部展开
            </button>
            <button onclick="collapseAllCitations()"
                    style="padding: 6px 12px; background: white; border: 1px solid #DFE1E6;
                           border-radius: 4px; cursor: pointer; font-size: 0.85em; color: #42526E;">
                全部折叠
            </button>
        </div>
        """)

    html.append("</div>")

    # 渲染引用列表
    if group_by_type:
        # 按类型分组显示
        groups = group_citations_by_type(displayed_citations)

        for source_type, group_citations in groups.items():
            html.append(f"""
            <div style="margin-bottom: 20px;">
                <h4 style="margin: 0 0 12px 0; color: #172B4D; font-size: 1em;
                           padding-bottom: 8px; border-bottom: 2px solid #DFE1E6;">
                    {source_type} ({len(group_citations)})
                </h4>
            """)

            for citation in group_citations:
                content = citation.get("content", "")
                card_html = create_enhanced_citation_card(
                    citation=citation,
                    content=content,
                    collapsed=True,
                    show_stats=show_stats
                )
                html.append(card_html)

            html.append("</div>")
    else:
        # 不分组，直接显示
        for citation in displayed_citations:
            content = citation.get("content", "")
            card_html = create_enhanced_citation_card(
                citation=citation,
                content=content,
                collapsed=True,
                show_stats=show_stats
            )
            html.append(card_html)

    # 显示更多提示
    if total_count > max_display:
        remaining = total_count - max_display
        html.append(f"""
        <div style="padding: 12px; text-align: center; color: #6B778C; font-size: 0.85em;
                    background: #F4F5F7; border-radius: 4px;">
            还有 {remaining} 个来源未显示
        </div>
        """)

    # 添加交互脚本
    html.append(get_citation_scripts())
    html.append(get_batch_control_scripts())

    return "".join(html)


def get_batch_control_scripts() -> str:
    """
    获取批量控制的 JavaScript 脚本

    Returns:
        JavaScript 代码
    """
    return """
    <script>
    function expandAllCitations() {
        const details = document.querySelectorAll('[id$="-detail"]');
        const toggles = document.querySelectorAll('[id$="-toggle"]');

        details.forEach(detail => {
            detail.style.display = 'block';
        });

        toggles.forEach(toggle => {
            toggle.textContent = '折叠';
        });
    }

    function collapseAllCitations() {
        const details = document.querySelectorAll('[id$="-detail"]');
        const toggles = document.querySelectorAll('[id$="-toggle"]');

        details.forEach(detail => {
            detail.style.display = 'none';
        });

        toggles.forEach(toggle => {
            toggle.textContent = '展开';
        });
    }
    </script>
    """


def create_filter_summary(
    total_count: int,
    filtered_count: int,
    filters: Dict[str, Any]
) -> str:
    """
    创建过滤结果摘要

    Args:
        total_count: 总数量
        filtered_count: 过滤后数量
        filters: 过滤条件

    Returns:
        HTML 字符串
    """
    if not filters or total_count == filtered_count:
        return ""

    active_filters = []

    source_types = filters.get("source_types")
    if source_types:
        active_filters.append(f"来源: {', '.join(source_types)}")

    min_quality = filters.get("min_quality", 0)
    if min_quality > 0:
        active_filters.append(f"最低质量: {min_quality:.0%}")

    if not active_filters:
        return ""

    filters_text = " · ".join(active_filters)

    return f"""
    <div style="padding: 8px 12px; background: #FFF4E6; border-left: 3px solid #FF991F;
                border-radius: 4px; margin-bottom: 12px; font-size: 0.85em;">
        <strong>筛选中:</strong> {filters_text} · 显示 {filtered_count}/{total_count} 个结果
    </div>
    """
