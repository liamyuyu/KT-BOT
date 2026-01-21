"""
Citation Display Components
引用展示组件，用于在 UI 中显示来源引用和高亮关键词
"""

from typing import Dict, List, Tuple, Any


def create_citation_badge(citation: Dict[str, Any]) -> str:
    """
    创建引用标签 HTML

    Args:
        citation: 引用信息字典，包含 source_id、source_type、source_url、relevance_score

    Returns:
        str: HTML 字符串
    """
    source_id = citation.get("source_id", "Unknown")
    source_type = citation.get("source_type", "").upper()
    source_url = citation.get("source_url")
    score = citation.get("relevance_score", 0)

    # 不同来源类型的颜色
    type_colors = {
        "JIRA": "#0052CC",
        "CONFLUENCE": "#0052CC",
        "LOCAL": "#00875A",
        "UNKNOWN": "#6B778C"
    }
    color = type_colors.get(source_type, "#6B778C")

    html = f"""
    <div style="display: inline-flex; align-items: center; gap: 8px;
                padding: 4px 12px; border-radius: 4px; margin: 4px 0;
                background: {color}15; border: 1px solid {color}40;">
        <span style="font-weight: 600; color: {color}; font-size: 0.85em;">{source_type}</span>
        <span style="color: #172B4D; font-size: 0.9em;">{source_id}</span>
        <span style="color: #6B778C; font-size: 0.85em;">
            相关度: {score:.1%}
        </span>
    """

    if source_url:
        html += f"""
        <a href="{source_url}" target="_blank"
           style="color: {color}; text-decoration: none; font-size: 0.85em;">
            📎 查看原文
        </a>
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
