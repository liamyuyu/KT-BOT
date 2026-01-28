"""
搜索页面 - Gradio UI
Story 4.5 Phase 4: 搜索功能 UI
"""

import logging
import gradio as gr
from typing import List, Tuple, Optional, Dict, Any
import asyncio

from ..utils.api_client import get_api_client

logger = logging.getLogger(__name__)


class SearchPage:
    """搜索页面"""

    def __init__(self):
        self.api_client = get_api_client()
        logger.info("SearchPage initialized")

    def create_ui(self) -> gr.Blocks:
        """创建搜索页面 UI"""

        with gr.Blocks(title="KT-BOT - 搜索") as demo:
            gr.Markdown(
                """
                # 🔍 全局搜索
                搜索文档、Issue 和 Confluence 页面
                """
            )

            with gr.Row():
                # 左侧：搜索面板
                with gr.Column(scale=2):
                    # 搜索输入框
                    with gr.Group():
                        search_query = gr.Textbox(
                            label="",
                            placeholder="输入搜索关键词...",
                            lines=2,
                            max_lines=5,
                            show_label=False
                        )

                        with gr.Row():
                            search_btn = gr.Button(
                                "🔍 搜索",
                                variant="primary",
                                size="lg",
                                scale=3
                            )
                            clear_btn = gr.Button(
                                "清空",
                                variant="secondary",
                                size="lg",
                                scale=1
                            )

                    # 搜索选项
                    with gr.Accordion("🔧 搜索选项", open=False):
                        search_method = gr.Dropdown(
                            choices=["hybrid", "vector", "bm25"],
                            value="hybrid",
                            label="搜索方法",
                            info="hybrid: 混合搜索 | vector: 向量搜索 | bm25: 全文搜索"
                        )

                        top_k = gr.Slider(
                            minimum=5,
                            maximum=50,
                            value=10,
                            step=5,
                            label="结果数量",
                            info="返回的搜索结果数量"
                        )

                        enable_highlight = gr.Checkbox(
                            label="启用关键词高亮",
                            value=True
                        )

                        # 过滤选项
                        gr.Markdown("#### 过滤条件")
                        filter_sources = gr.CheckboxGroup(
                            choices=["jira", "confluence", "local"],
                            label="数据来源"
                        )

                        filter_time_range = gr.Dropdown(
                            choices=["不限", "1d", "7d", "30d", "90d"],
                            value="不限",
                            label="时间范围"
                        )

                # 右侧：搜索结果
                with gr.Column(scale=3):
                    # 搜索统计
                    search_stats = gr.Markdown("准备搜索...")

                    # 搜索结果列表
                    search_results = gr.HTML(
                        value="<div style='text-align: center; padding: 40px; color: #666;'>"
                              "请输入搜索关键词开始搜索</div>"
                    )

                    # 分页控制
                    with gr.Row():
                        prev_page_btn = gr.Button("上一页", size="sm")
                        page_info = gr.Textbox(
                            value="第 1 页",
                            interactive=False,
                            show_label=False,
                            scale=2
                        )
                        next_page_btn = gr.Button("下一页", size="sm")

                    # 隐藏状态
                    current_page = gr.State(value=1)
                    total_pages = gr.State(value=1)
                    last_query = gr.State(value="")

            # ========================================================================
            # 事件绑定
            # ========================================================================

            # 搜索按钮
            search_btn.click(
                fn=self.search_handler,
                inputs=[
                    search_query,
                    search_method,
                    top_k,
                    enable_highlight,
                    filter_sources,
                    filter_time_range,
                    gr.State(value=1)  # 重置到第1页
                ],
                outputs=[search_results, search_stats, current_page, total_pages, page_info, last_query]
            )

            # 回车搜索
            search_query.submit(
                fn=self.search_handler,
                inputs=[
                    search_query,
                    search_method,
                    top_k,
                    enable_highlight,
                    filter_sources,
                    filter_time_range,
                    gr.State(value=1)
                ],
                outputs=[search_results, search_stats, current_page, total_pages, page_info, last_query]
            )

            # 清空按钮
            clear_btn.click(
                fn=lambda: ("", "<div style='text-align: center; padding: 40px; color: #666;'>"
                           "请输入搜索关键词开始搜索</div>", "准备搜索...", 1, 1, "第 1 页", ""),
                inputs=[],
                outputs=[search_query, search_results, search_stats, current_page, total_pages, page_info, last_query]
            )

            # 上一页
            prev_page_btn.click(
                fn=self.prev_page_handler,
                inputs=[
                    last_query,
                    search_method,
                    top_k,
                    enable_highlight,
                    filter_sources,
                    filter_time_range,
                    current_page
                ],
                outputs=[search_results, search_stats, current_page, page_info]
            )

            # 下一页
            next_page_btn.click(
                fn=self.next_page_handler,
                inputs=[
                    last_query,
                    search_method,
                    top_k,
                    enable_highlight,
                    filter_sources,
                    filter_time_range,
                    current_page,
                    total_pages
                ],
                outputs=[search_results, search_stats, current_page, page_info]
            )

        return demo

    async def search_handler(
        self,
        query: str,
        method: str,
        top_k: int,
        enable_highlight: bool,
        sources: List[str],
        time_range: str,
        page: int
    ) -> Tuple[str, str, int, int, str, str]:
        """
        搜索处理器

        Returns:
            (结果HTML, 统计信息, 当前页, 总页数, 页码信息, 查询文本)
        """
        if not query or query.strip() == "":
            return (
                "<div style='text-align: center; padding: 40px; color: #666;'>"
                "请输入搜索关键词</div>",
                "请输入搜索关键词",
                1,
                1,
                "第 1 页",
                ""
            )

        try:
            logger.info(f"Searching: query='{query}', method={method}, page={page}")

            # 处理过滤参数
            api_sources = sources if sources and len(sources) > 0 else None
            api_time_range = None if time_range == "不限" else time_range

            # 调用搜索 API
            response = await self.api_client.search_documents(
                query=query.strip(),
                method=method,
                top_k=top_k,
                page=page,
                page_size=10,
                sources=api_sources,
                time_range=api_time_range,
                enable_highlight=enable_highlight
            )

            if not response:
                return (
                    "<div style='text-align: center; padding: 40px; color: #f44336;'>"
                    "❌ 搜索失败，请稍后重试</div>",
                    "搜索失败",
                    1,
                    1,
                    "第 1 页",
                    query
                )

            # 解析响应
            data = response.get("data", {})
            results = data.get("results", [])
            total = data.get("total", 0)
            search_time_ms = data.get("search_time_ms", 0)
            current_page = data.get("page", 1)
            total_pages = data.get("total_pages", 1)

            # 生成统计信息
            stats = f"找到 **{total}** 个结果 | 耗时 {search_time_ms}ms | 方法: {method}"

            # 生成结果 HTML
            if total == 0:
                results_html = (
                    "<div style='text-align: center; padding: 40px; color: #666;'>"
                    f"😔 未找到匹配 \"{query}\" 的结果</div>"
                )
            else:
                results_html = self._format_results(results, query)

            page_info = f"第 {current_page} / {total_pages} 页"

            logger.info(f"Search completed: total={total}, page={current_page}/{total_pages}")

            return (
                results_html,
                stats,
                current_page,
                total_pages,
                page_info,
                query
            )

        except Exception as e:
            logger.error(f"Search error: {e}", exc_info=True)
            return (
                f"<div style='text-align: center; padding: 40px; color: #f44336;'>"
                f"❌ 搜索出错: {str(e)}</div>",
                "搜索出错",
                1,
                1,
                "第 1 页",
                query
            )

    async def prev_page_handler(
        self,
        query: str,
        method: str,
        top_k: int,
        enable_highlight: bool,
        sources: List[str],
        time_range: str,
        current_page: int
    ) -> Tuple[str, str, int, str]:
        """上一页处理器"""
        if current_page <= 1:
            return gr.update(), gr.update(), current_page, f"第 {current_page} 页"

        new_page = current_page - 1
        results_html, stats, page, total_pages, page_info, _ = await self.search_handler(
            query, method, top_k, enable_highlight, sources, time_range, new_page
        )

        return results_html, stats, page, page_info

    async def next_page_handler(
        self,
        query: str,
        method: str,
        top_k: int,
        enable_highlight: bool,
        sources: List[str],
        time_range: str,
        current_page: int,
        total_pages: int
    ) -> Tuple[str, str, int, str]:
        """下一页处理器"""
        if current_page >= total_pages:
            return gr.update(), gr.update(), current_page, f"第 {current_page} 页"

        new_page = current_page + 1
        results_html, stats, page, total_pages, page_info, _ = await self.search_handler(
            query, method, top_k, enable_highlight, sources, time_range, new_page
        )

        return results_html, stats, page, page_info

    def _format_results(self, results: List[Dict[str, Any]], query: str) -> str:
        """格式化搜索结果为 HTML"""
        html_parts = []

        for i, result in enumerate(results, 1):
            title = result.get("title", "未命名文档")
            content = result.get("content", "")
            source = result.get("source", "unknown")
            doc_type = result.get("doc_type", "unknown")
            score = result.get("score", 0.0)
            doc_id = result.get("doc_id", "")
            parent_id = result.get("parent_id", "")

            # 来源图标
            source_icon = {
                "jira": "🔶",
                "confluence": "📘",
                "local": "📄"
            }.get(source, "📄")

            # 分数百分比
            score_percent = int(score * 100)

            # 生成结果卡片
            card_html = f"""
            <div style='border: 1px solid #e0e0e0; border-radius: 8px; padding: 16px; margin-bottom: 12px; background: white;'>
                <div style='display: flex; align-items: center; margin-bottom: 8px;'>
                    <span style='font-size: 24px; margin-right: 8px;'>{source_icon}</span>
                    <div style='flex: 1;'>
                        <h3 style='margin: 0; color: #1976d2; font-size: 18px;'>{title}</h3>
                        <div style='font-size: 12px; color: #666; margin-top: 4px;'>
                            {source} • {doc_type} • ID: {parent_id} • 相关度: {score_percent}%
                        </div>
                    </div>
                </div>
                <div style='color: #424242; line-height: 1.6;'>
                    {content}
                </div>
            </div>
            """

            html_parts.append(card_html)

        return "\n".join(html_parts)


def create_search_page() -> gr.Blocks:
    """创建搜索页面（工厂函数）"""
    page = SearchPage()
    return page.create_ui()
