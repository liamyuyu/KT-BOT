"""
Citation Display Components
引用展示组件，用于在 UI 中显示来源引用和高亮关键词
"""

from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime


def create_citation_badge(citation: Dict[str, Any], rank: Optional[int] = None) -> str:
    """
    创建引用标签 HTML

    Args:
        citation: 引用信息字典，包含 source_id、source_type、source_url、relevance_score
        rank: 排名位置（可选），用于显示排名徽章

    Returns:
        str: HTML 字符串
    """
    source_id = citation.get("source_id", "Unknown")
    source_type = citation.get("source_type", "").upper()
    source_url = citation.get("source_url")
    score = citation.get("relevance_score", 0)
    quality_score = citation.get("quality_score")

    # 不同来源类型的颜色
    type_colors = {
        "JIRA": "#0052CC",
        "CONFLUENCE": "#0052CC",
        "LOCAL": "#00875A",
        "UNKNOWN": "#6B778C"
    }
    color = type_colors.get(source_type, "#6B778C")

    # URL 验证
    is_valid_url = False
    url_warning = ""
    if source_url:
        is_valid_url = source_url.startswith(("http://", "https://"))
        if not is_valid_url:
            url_warning = "⚠️ 无效链接"

    html = f"""
    <div style="display: inline-flex; align-items: center; gap: 8px;
                padding: 4px 12px; border-radius: 4px; margin: 4px 0;
                background: {color}15; border: 1px solid {color}40;">
    """

    # 添加排名徽章
    if rank is not None:
        rank_color = "#FF5630" if rank == 1 else "#0052CC" if rank <= 3 else "#6B778C"
        html += f"""
        <span style="background: {rank_color}; color: white; padding: 2px 6px;
                     border-radius: 10px; font-size: 0.75em; font-weight: 600;">
            #{rank}
        </span>
        """

    html += f"""
        <span style="font-weight: 600; color: {color}; font-size: 0.85em;">{source_type}</span>
        <span style="color: #172B4D; font-size: 0.9em;">{source_id}</span>
        <span style="color: #6B778C; font-size: 0.85em;">
            相关度: {score:.1%}
        </span>
    """

    # 显示质量分数（如果有）
    if quality_score is not None:
        quality_color = "#00875A" if quality_score >= 0.8 else "#FF991F" if quality_score >= 0.6 else "#6B778C"
        html += f"""
        <span style="color: {quality_color}; font-size: 0.85em; font-weight: 600;">
            质量: {quality_score:.0%}
        </span>
        """

    if source_url:
        if is_valid_url:
            # 有效链接 - 带 hover 效果和图标
            html += f"""
            <a href="{source_url}" target="_blank" rel="noopener noreferrer"
               title="{source_url}"
               style="padding: 6px 12px; background: {color}; color: white;
                      text-decoration: none; font-size: 0.85em; border-radius: 4px;
                      transition: all 0.2s; display: inline-block;"
               onmouseover="this.style.transform='translateY(-1px)'; this.style.boxShadow='0 2px 6px rgba(0,0,0,0.2)';"
               onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none';"
               onclick="showToast('正在打开原文...', 'info')">
                📄 打开原文 ↗
            </a>
            """
        else:
            # 无效链接 - 显示警告
            html += f"""
            <span style="color: #DE350B; font-size: 0.85em; cursor: not-allowed;"
                  title="链接格式无效: {source_url}">
                {url_warning}
            </span>
            """

    html += "</div>"
    return html


def highlight_content(content: str, highlights: List[Tuple[int, int]]) -> str:
    """
    高亮显示内容中的关键词

    Args:
        content: 文本内容
        highlights: 高亮位置列表 [(start, end), ...]

    Returns:
        str: 带高亮标记的 HTML 字符串
    """
    if not highlights:
        return content

    # 去重并排序
    highlights = sorted(set(highlights), key=lambda x: x[0])
    result = []
    last_end = 0

    for start, end in highlights:
        # 避免重叠
        if start < last_end:
            continue

        # 添加普通文本
        result.append(content[last_end:start])

        # 添加高亮文本
        highlighted_text = content[start:end]
        result.append(
            f'<mark style="background-color: #FFF59D; padding: 2px 4px; '
            f'border-radius: 2px; font-weight: 500;">{highlighted_text}</mark>'
        )

        last_end = end

    # 添加剩余文本
    result.append(content[last_end:])

    return "".join(result)


def format_sources(contexts: List[Dict[str, Any]], max_sources: int = 5) -> str:
    """
    格式化来源列表为 HTML

    Args:
        contexts: 检索上下文列表，每个包含 content、citation 等字段
        max_sources: 最多显示的来源数量

    Returns:
        str: 格式化的 HTML 字符串
    """
    if not contexts:
        return ""

    html = [
        "<div style='margin-top: 16px; padding: 12px; background: #F4F5F7; "
        "border-radius: 8px; border: 1px solid #DFE1E6;'>"
    ]
    html.append("<h4 style='margin-top: 0; color: #172B4D; font-size: 1em;'>📚 参考来源</h4>")

    # 限制显示数量
    displayed_contexts = contexts[:max_sources]

    for i, ctx in enumerate(displayed_contexts, 1):
        citation = ctx.get("citation", {})
        content = ctx.get("content", "")
        highlights = citation.get("highlights", [])

        # 创建引用标签
        badge = create_citation_badge(citation)

        # 高亮内容（限制长度）
        max_content_length = 300
        truncated_content = content[:max_content_length]
        if len(content) > max_content_length:
            truncated_content += "..."

        highlighted = highlight_content(truncated_content, highlights)

        html.append(f"""
        <div style="margin-bottom: 12px; padding: 12px; background: white;
                    border-left: 3px solid #0052CC; border-radius: 4px;
                    box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
            <div style="margin-bottom: 8px;">
                {badge}
            </div>
            <p style="margin: 0; color: #172B4D; font-size: 0.9em; line-height: 1.5;">
                {highlighted}
            </p>
        </div>
        """)

    # 如果有更多来源
    if len(contexts) > max_sources:
        remaining = len(contexts) - max_sources
        html.append(
            f"<p style='margin: 8px 0 0 0; color: #6B778C; font-size: 0.85em;'>"
            f"...还有 {remaining} 个相关来源</p>"
        )

    html.append("</div>")
    return "".join(html)


def create_citation_footer(num_sources: int) -> str:
    """
    创建引用页脚（简洁版）

    Args:
        num_sources: 来源数量

    Returns:
        str: HTML 字符串
    """
    if num_sources == 0:
        return ""

    return f"""
    <div style="margin-top: 8px; padding: 8px; background: #F4F5F7;
                border-radius: 4px; font-size: 0.85em; color: #6B778C;">
        💡 本回答基于 {num_sources} 个知识库文档生成
    </div>
    """


def render_quality_score(score: float, breakdown: Optional[Dict[str, float]] = None) -> str:
    """
    渲染质量分数可视化

    Args:
        score: 质量分数 (0-1)
        breakdown: 评分细分（可选）

    Returns:
        str: HTML 字符串
    """
    # 星级评定（5星制）
    stars = int(score * 5)
    star_display = "⭐" * stars + "☆" * (5 - stars)

    # 颜色编码
    if score >= 0.8:
        color = "#00875A"  # 绿色
        label = "优秀"
    elif score >= 0.6:
        color = "#FF991F"  # 黄色
        label = "良好"
    else:
        color = "#6B778C"  # 灰色
        label = "一般"

    html = f"""
    <div style="display: flex; align-items: center; gap: 8px; margin: 4px 0;">
        <span style="font-size: 0.9em;">{star_display}</span>
        <span style="color: {color}; font-weight: 600; font-size: 0.9em;">{score:.0%}</span>
        <span style="color: #6B778C; font-size: 0.85em;">({label})</span>
    </div>
    """

    # 如果有评分细分，显示详细信息
    if breakdown:
        html += """
        <div style="font-size: 0.8em; color: #6B778C; margin-top: 4px;">
        """
        breakdown_labels = {
            "relevance": "相关度",
            "freshness": "时效性",
            "coverage": "覆盖度",
            "popularity": "热度"
        }
        for key, value in breakdown.items():
            label = breakdown_labels.get(key, key)
            html += f"<span style='margin-right: 8px;'>{label}: {value:.0%}</span>"
        html += "</div>"

    return html


def render_citation_stats(stats: Dict[str, Any]) -> str:
    """
    渲染引用统计信息

    Args:
        stats: 统计信息字典，包含 usage_count, unique_queries, last_used_at, avg_relevance

    Returns:
        str: HTML 字符串
    """
    usage_count = stats.get("usage_count", 0)
    unique_queries = stats.get("unique_queries", 0)
    last_used = stats.get("last_used_at")
    avg_relevance = stats.get("avg_relevance", 0)

    # 确定热度等级和徽章
    popularity_badge = ""
    popularity_label = ""
    if usage_count > 50:
        popularity_badge = "🔥"
        popularity_label = "热门"
        badge_color = "#FF5630"
    elif usage_count > 20:
        popularity_badge = "⭐"
        popularity_label = "常用"
        badge_color = "#FF991F"
    elif usage_count > 0:
        popularity_badge = "📌"
        popularity_label = "普通"
        badge_color = "#6B778C"
    else:
        badge_color = "#6B778C"

    # 格式化最后使用时间
    last_used_display = "未知"
    time_color = "#6B778C"
    if last_used:
        try:
            if isinstance(last_used, str):
                last_time = datetime.fromisoformat(last_used.replace("Z", "+00:00"))
            else:
                last_time = last_used

            delta = datetime.now(last_time.tzinfo or None) - last_time
            if delta.days == 0:
                last_used_display = "今天"
                time_color = "#00875A"  # 绿色 - 最近使用
            elif delta.days == 1:
                last_used_display = "昨天"
                time_color = "#00875A"
            elif delta.days < 7:
                last_used_display = f"{delta.days}天前"
                time_color = "#FF991F"  # 黄色 - 本周使用
            elif delta.days < 30:
                last_used_display = f"{delta.days // 7}周前"
                time_color = "#6B778C"  # 灰色 - 本月使用
            else:
                last_used_display = f"{delta.days // 30}月前"
                time_color = "#6B778C"
        except Exception:
            last_used_display = "未知"

    html = f"""
    <div style="margin-top: 8px; padding: 12px; background: #F4F5F7;
                border-radius: 4px; font-size: 0.85em; color: #6B778C;
                border: 1px solid #DFE1E6;">
    """

    # 添加热度徽章
    if popularity_label:
        html += f"""
        <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 8px;">
            <span style="font-size: 1.2em;">{popularity_badge}</span>
            <span style="color: {badge_color}; font-weight: 600; font-size: 0.9em;">
                {popularity_label}文档
            </span>
        </div>
        """

    html += f"""
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
            <div style="display: flex; align-items: center; gap: 4px;">
                <span>📊</span>
                <span>引用次数: <strong style="color: #172B4D;">{usage_count}</strong></span>
            </div>
            <div style="display: flex; align-items: center; gap: 4px;">
                <span>🔍</span>
                <span>查询数: <strong style="color: #172B4D;">{unique_queries}</strong></span>
            </div>
            <div style="display: flex; align-items: center; gap: 4px;">
                <span>🕒</span>
                <span>最后使用: <strong style="color: {time_color};">{last_used_display}</strong></span>
            </div>
            <div style="display: flex; align-items: center; gap: 4px;">
                <span>📈</span>
                <span>平均相关度: <strong style="color: #172B4D;">{avg_relevance:.0%}</strong></span>
            </div>
        </div>
    </div>
    """
    return html


def create_enhanced_citation_card(
    citation: Dict[str, Any],
    content: str = "",
    collapsed: bool = True,
    show_stats: bool = True
) -> str:
    """
    创建增强的引用卡片

    Args:
        citation: 引用信息字典
        content: 引用内容（可选）
        collapsed: 是否默认折叠
        show_stats: 是否显示统计信息

    Returns:
        str: HTML 字符串
    """
    source_id = citation.get("source_id", "Unknown")
    source_type = citation.get("source_type", "").upper()
    source_url = citation.get("source_url")
    relevance_score = citation.get("relevance_score", 0)
    quality_score = citation.get("quality_score")
    quality_breakdown = citation.get("quality_breakdown")
    usage_count = citation.get("usage_count", 0)
    highlights = citation.get("highlights", [])
    snippet_preview = citation.get("snippet_preview", "")

    # 来源类型颜色
    type_colors = {
        "JIRA": "#0052CC",
        "CONFLUENCE": "#0052CC",
        "LOCAL": "#00875A",
        "UNKNOWN": "#6B778C"
    }
    color = type_colors.get(source_type, "#6B778C")

    # 卡片唯一 ID（用于展开/折叠）
    card_id = f"citation-{source_id.replace('/', '-')}"

    # 折叠状态样式
    detail_display = "none" if collapsed else "block"
    toggle_text = "展开" if collapsed else "折叠"

    html = f"""
    <div id="{card_id}" style="margin-bottom: 12px; padding: 12px; background: white;
                border-left: 3px solid {color}; border-radius: 4px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                transition: box-shadow 0.2s;"
         onmouseover="this.style.boxShadow='0 2px 8px rgba(0,0,0,0.15)'"
         onmouseout="this.style.boxShadow='0 1px 3px rgba(0,0,0,0.1)'">

        <!-- 标题行 -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-weight: 600; color: {color}; font-size: 0.85em;">{source_type}</span>
                <span style="color: #172B4D; font-size: 0.95em; font-weight: 500;">{source_id}</span>
                {f'<span style="background: #FF5630; color: white; padding: 2px 6px; border-radius: 10px; font-size: 0.75em; font-weight: 600;">{usage_count}</span>' if usage_count > 0 else ''}
            </div>
            <div style="display: flex; gap: 8px;">
                <button onclick="toggleCitationDetail('{card_id}')"
                        style="background: none; border: 1px solid #DFE1E6; padding: 4px 8px;
                               border-radius: 4px; cursor: pointer; font-size: 0.85em; color: #42526E;">
                    <span id="{card_id}-toggle">{toggle_text}</span>
                </button>
            </div>
        </div>

        <!-- 摘要信息（始终显示） -->
        <div style="display: flex; gap: 16px; align-items: center; margin-bottom: 8px;">
            <span style="color: #6B778C; font-size: 0.85em;">相关度: {relevance_score:.0%}</span>
    """

    # 显示质量分数（如果有）
    if quality_score is not None:
        html += f"""
            <div style="border-left: 1px solid #DFE1E6; padding-left: 16px;">
                {render_quality_score(quality_score, quality_breakdown)}
            </div>
        """

    html += """
        </div>

        <!-- 详细信息（可展开） -->
        <div id="{card_id}-detail" style="display: {detail_display}; margin-top: 12px;">
    """.format(card_id=card_id, detail_display=detail_display)

    # 显示内容预览
    if content or snippet_preview:
        display_content = content or snippet_preview
        max_length = 300
        truncated = display_content[:max_length]
        if len(display_content) > max_length:
            truncated += "..."

        highlighted = highlight_content(truncated, highlights)
        html += f"""
            <div style="margin-bottom: 12px; padding: 12px; background: #F4F5F7;
                        border-radius: 4px; font-size: 0.9em; line-height: 1.6;">
                {highlighted}
            </div>
        """

    # 显示统计信息
    if show_stats and usage_count > 0:
        stats = {
            "usage_count": usage_count,
            "unique_queries": citation.get("unique_queries", 0),
            "last_used_at": citation.get("last_used_at"),
            "avg_relevance": relevance_score
        }
        html += render_citation_stats(stats)

    # 操作按钮
    html += """
        <div style="margin-top: 12px; display: flex; gap: 8px;">
    """

    if source_url:
        # URL 验证
        is_valid_url = source_url.startswith(("http://", "https://"))
        if is_valid_url:
            html += f"""
            <a href="{source_url}" target="_blank" rel="noopener noreferrer"
               title="{source_url}"
               style="padding: 6px 12px; background: {color}; color: white; text-decoration: none;
                      border-radius: 4px; font-size: 0.85em; font-weight: 500;
                      transition: all 0.2s; display: inline-block;"
               onmouseover="this.style.transform='translateY(-1px)'; this.style.boxShadow='0 2px 6px rgba(0,0,0,0.2)';"
               onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none';"
               onclick="showToast('正在打开原文...', 'info')">
                📄 打开原文 ↗
            </a>
            <button onclick="copyToClipboard('{source_url}')"
                    style="padding: 6px 12px; background: white; color: {color};
                           border: 1px solid {color}; border-radius: 4px;
                           cursor: pointer; font-size: 0.85em; font-weight: 500;
                           transition: all 0.2s;"
                    onmouseover="this.style.background='{color}'; this.style.color='white';"
                    onmouseout="this.style.background='white'; this.style.color='{color}';">
                📋 复制链接
            </button>
            """
        else:
            html += f"""
            <span style="padding: 6px 12px; background: #FFEBE6; color: #DE350B;
                         border-radius: 4px; font-size: 0.85em; font-weight: 500;"
                  title="链接格式无效: {source_url}">
                ⚠️ 无效链接
            </span>
            """

    html += """
        </div>
    </div>
    """

    html += """
    </div>
    """

    return html


def filter_citations_by_type(
    citations: List[Dict],
    source_types: Optional[List[str]] = None
) -> List[Dict]:
    """
    Filter citations by source type

    Args:
        citations: List of citation dictionaries
        source_types: List of source types to filter by (e.g., ["jira", "confluence", "local"])
                     If None or empty, returns all citations

    Returns:
        List[Dict]: Filtered citations
    """
    if not source_types:
        return citations

    # Normalize source types to lowercase for comparison
    normalized_types = [st.lower() for st in source_types]

    return [
        c for c in citations
        if c.get("source_type", "").lower() in normalized_types
    ]


def sort_citations(
    citations: List[Dict],
    sort_by: str = "quality"
) -> List[Dict]:
    """
    Sort citations by specified criteria

    Args:
        citations: List of citation dictionaries
        sort_by: Sorting method - "quality", "relevance", "usage", or "freshness"

    Returns:
        List[Dict]: Sorted citations (descending order)
    """
    sort_keys = {
        "quality": lambda c: c.get("quality_score", 0),
        "relevance": lambda c: c.get("relevance_score", 0),
        "usage": lambda c: c.get("usage_count", 0),
        "freshness": lambda c: c.get("document_created_at", "")
    }

    sort_func = sort_keys.get(sort_by, sort_keys["quality"])

    try:
        return sorted(citations, key=sort_func, reverse=True)
    except (TypeError, KeyError):
        # Fallback: return original list if sorting fails
        return citations


def get_citation_scripts() -> str:
    """
    获取引用交互所需的 JavaScript 脚本

    Returns:
        str: JavaScript 代码
    """
    return """
    <script>
    function toggleCitationDetail(cardId) {
        const detail = document.getElementById(cardId + '-detail');
        const toggle = document.getElementById(cardId + '-toggle');

        if (detail.style.display === 'none') {
            detail.style.display = 'block';
            toggle.textContent = '折叠';
        } else {
            detail.style.display = 'none';
            toggle.textContent = '展开';
        }
    }

    function copyToClipboard(text) {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(text).then(() => {
                // 显示复制成功提示
                const msg = document.createElement('div');
                msg.textContent = '✅ 链接已复制';
                msg.style.cssText = 'position: fixed; top: 20px; right: 20px; background: #00875A; color: white; padding: 12px 20px; border-radius: 4px; z-index: 9999; font-size: 0.9em;';
                document.body.appendChild(msg);
                setTimeout(() => msg.remove(), 2000);
            }).catch(err => {
                console.error('Failed to copy:', err);
            });
        } else {
            // 降级方案：使用 execCommand
            const textarea = document.createElement('textarea');
            textarea.value = text;
            textarea.style.position = 'fixed';
            textarea.style.opacity = '0';
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);

            alert('链接已复制到剪贴板');
        }
    }

    function showToast(message, type='info') {
        const colors = {
            success: '#00875A',
            warning: '#FF991F',
            error: '#DE350B',
            info: '#0052CC'
        };
        const toast = document.createElement('div');
        toast.textContent = message;
        toast.style.cssText = `position: fixed; top: 20px; right: 20px;
                               background: ${colors[type]}; color: white;
                               padding: 12px 20px; border-radius: 4px;
                               z-index: 9999; font-size: 0.9em;
                               box-shadow: 0 2px 8px rgba(0,0,0,0.2);`;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }
    </script>
    """
