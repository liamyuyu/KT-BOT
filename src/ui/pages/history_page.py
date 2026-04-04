"""
对话历史页面 - Gradio UI
Story 5.1 Phase 4: 对话历史管理 UI
"""

import logging
import gradio as gr
from typing import List, Tuple, Optional, Dict, Any
import asyncio
from datetime import datetime
import tempfile
import os

from ..utils.api_client import get_api_client

logger = logging.getLogger(__name__)


class HistoryPage:
    """对话历史页面"""

    def __init__(self):
        self.api_client = get_api_client()
        self.default_user_id = "default_user"  # MVP版本使用固定用户ID
        logger.info("HistoryPage initialized")

    def create_ui(self) -> gr.Blocks:
        """创建对话历史页面 UI"""

        with gr.Blocks(title="KT-BOT - 对话历史") as demo:
            gr.Markdown(
                """
                # 📜 对话历史
                管理和查看您的对话记录
                """
            )

            with gr.Row():
                # 左侧：对话列表和搜索
                with gr.Column(scale=2):
                    # 搜索和过滤
                    with gr.Group():
                        search_box = gr.Textbox(
                            label="",
                            placeholder="搜索对话标题...",
                            show_label=False
                        )

                        with gr.Row():
                            search_btn = gr.Button(
                                "🔍 搜索",
                                variant="primary",
                                size="sm",
                                scale=2
                            )
                            refresh_btn = gr.Button(
                                "🔄 刷新",
                                variant="secondary",
                                size="sm",
                                scale=1
                            )

                    # 统计信息
                    stats_display = gr.Markdown("加载统计中...")

                    # 对话列表
                    conversation_list = gr.HTML(
                        value="<div style='text-align: center; padding: 40px; color: #666;'>"
                              "加载对话列表中...</div>"
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

                # 右侧：对话详情
                with gr.Column(scale=3):
                    # 详情标题
                    detail_header = gr.Markdown("### 📝 对话详情")

                    # 对话信息
                    conversation_info = gr.HTML(
                        value="<div style='text-align: center; padding: 40px; color: #666;'>"
                              "请选择一个对话查看详情</div>"
                    )

                    # 消息列表
                    messages_display = gr.HTML(
                        value=""
                    )

                    # 操作按钮
                    with gr.Row():
                        export_md_btn = gr.Button(
                            "📄 导出 Markdown",
                            variant="secondary",
                            size="sm"
                        )
                        export_json_btn = gr.Button(
                            "📋 导出 JSON",
                            variant="secondary",
                            size="sm"
                        )
                        export_pdf_btn = gr.Button(
                            "📕 导出 PDF",
                            variant="secondary",
                            size="sm"
                        )
                        delete_btn = gr.Button(
                            "🗑️ 删除",
                            variant="stop",
                            size="sm"
                        )

                    # 导出文件下载
                    export_file = gr.File(
                        label="导出文件",
                        visible=False
                    )

            # 隐藏状态
            current_page = gr.State(value=1)
            total_pages = gr.State(value=1)
            selected_conversation_id = gr.State(value=None)
            search_keyword = gr.State(value="")

            # ========================================================================
            # 事件绑定
            # ========================================================================

            # 页面加载时获取对话列表和统计
            demo.load(
                fn=self.load_initial_data,
                inputs=[],
                outputs=[conversation_list, stats_display, current_page, total_pages, page_info]
            )

            # 刷新按钮
            refresh_btn.click(
                fn=self.load_conversations,
                inputs=[gr.State(value=1), search_keyword],
                outputs=[conversation_list, current_page, total_pages, page_info]
            ).then(
                fn=self.load_stats,
                inputs=[],
                outputs=[stats_display]
            )

            # 搜索按钮
            search_btn.click(
                fn=self.search_handler,
                inputs=[search_box],
                outputs=[conversation_list, search_keyword, current_page, total_pages, page_info]
            )

            # 搜索框回车
            search_box.submit(
                fn=self.search_handler,
                inputs=[search_box],
                outputs=[conversation_list, search_keyword, current_page, total_pages, page_info]
            )

            # 上一页
            prev_page_btn.click(
                fn=self.prev_page_handler,
                inputs=[current_page, search_keyword],
                outputs=[conversation_list, current_page, page_info]
            )

            # 下一页
            next_page_btn.click(
                fn=self.next_page_handler,
                inputs=[current_page, total_pages, search_keyword],
                outputs=[conversation_list, current_page, page_info]
            )

            # 导出 Markdown
            export_md_btn.click(
                fn=self.export_handler,
                inputs=[selected_conversation_id, gr.State(value="markdown")],
                outputs=[export_file, gr.State()]
            ).then(
                fn=lambda: gr.update(visible=True),
                inputs=[],
                outputs=[export_file]
            )

            # 导出 JSON
            export_json_btn.click(
                fn=self.export_handler,
                inputs=[selected_conversation_id, gr.State(value="json")],
                outputs=[export_file, gr.State()]
            ).then(
                fn=lambda: gr.update(visible=True),
                inputs=[],
                outputs=[export_file]
            )

            # 导出 PDF
            export_pdf_btn.click(
                fn=self.export_handler,
                inputs=[selected_conversation_id, gr.State(value="pdf")],
                outputs=[export_file, gr.State()]
            ).then(
                fn=lambda: gr.update(visible=True),
                inputs=[],
                outputs=[export_file]
            )

            # 删除对话
            delete_btn.click(
                fn=self.delete_handler,
                inputs=[selected_conversation_id],
                outputs=[conversation_info, messages_display, selected_conversation_id]
            ).then(
                fn=self.load_conversations,
                inputs=[current_page, search_keyword],
                outputs=[conversation_list, current_page, total_pages, page_info]
            ).then(
                fn=self.load_stats,
                inputs=[],
                outputs=[stats_display]
            )

        return demo

    async def load_initial_data(self) -> Tuple[str, str, int, int, str]:
        """加载初始数据（对话列表和统计）"""
        try:
            # 并发加载对话列表和统计
            conversations_task = self.api_client.list_conversations(
                user_id=self.default_user_id,
                page=1,
                page_size=20
            )
            stats_task = self.api_client.get_conversation_stats(
                user_id=self.default_user_id
            )

            conversations_response, stats_response = await asyncio.gather(
                conversations_task,
                stats_task
            )

            # 处理对话列表
            if conversations_response:
                data = conversations_response.get("data", {})
                conversations = data.get("conversations", [])
                total = data.get("total", 0)
                page = data.get("page", 1)
                page_size = data.get("page_size", 20)
                total_pages = (total + page_size - 1) // page_size if total > 0 else 1

                list_html = self._format_conversation_list(conversations)
                page_info = f"第 {page} / {total_pages} 页"
            else:
                list_html = "<div style='text-align: center; padding: 40px; color: #f44336;'>加载失败</div>"
                page = 1
                total_pages = 1
                page_info = "第 1 页"

            # 处理统计信息
            if stats_response:
                stats_data = stats_response.get("data", {})
                stats_html = self._format_stats(stats_data)
            else:
                stats_html = "统计加载失败"

            return list_html, stats_html, page, total_pages, page_info

        except Exception as e:
            logger.error(f"Load initial data error: {e}", exc_info=True)
            return (
                "<div style='text-align: center; padding: 40px; color: #f44336;'>加载失败</div>",
                "统计加载失败",
                1,
                1,
                "第 1 页"
            )

    async def load_conversations(
        self,
        page: int,
        keyword: str = ""
    ) -> Tuple[str, int, int, str]:
        """加载对话列表"""
        try:
            if keyword and keyword.strip():
                # 搜索对话
                response = await self.api_client.search_conversations(
                    user_id=self.default_user_id,
                    keyword=keyword.strip(),
                    page=page,
                    page_size=20
                )
            else:
                # 列出所有对话
                response = await self.api_client.list_conversations(
                    user_id=self.default_user_id,
                    page=page,
                    page_size=20
                )

            if not response:
                return (
                    "<div style='text-align: center; padding: 40px; color: #f44336;'>加载失败</div>",
                    1,
                    1,
                    "第 1 页"
                )

            data = response.get("data", {})
            conversations = data.get("conversations", [])
            total = data.get("total", 0)
            current_page = data.get("page", 1)
            page_size = data.get("page_size", 20)
            total_pages = (total + page_size - 1) // page_size if total > 0 else 1

            list_html = self._format_conversation_list(conversations)
            page_info = f"第 {current_page} / {total_pages} 页"

            return list_html, current_page, total_pages, page_info

        except Exception as e:
            logger.error(f"Load conversations error: {e}", exc_info=True)
            return (
                f"<div style='text-align: center; padding: 40px; color: #f44336;'>加载失败: {str(e)}</div>",
                1,
                1,
                "第 1 页"
            )

    async def load_stats(self) -> str:
        """加载统计信息"""
        try:
            response = await self.api_client.get_conversation_stats(
                user_id=self.default_user_id
            )

            if not response:
                return "统计加载失败"

            stats_data = response.get("data", {})
            return self._format_stats(stats_data)

        except Exception as e:
            logger.error(f"Load stats error: {e}", exc_info=True)
            return f"统计加载失败: {str(e)}"

    async def search_handler(
        self,
        keyword: str
    ) -> Tuple[str, str, int, int, str]:
        """搜索处理器"""
        list_html, page, total_pages, page_info = await self.load_conversations(1, keyword)
        return list_html, keyword, page, total_pages, page_info

    async def prev_page_handler(
        self,
        current_page: int,
        keyword: str
    ) -> Tuple[str, int, str]:
        """上一页处理器"""
        if current_page <= 1:
            return gr.update(), current_page, f"第 {current_page} 页"

        new_page = current_page - 1
        list_html, page, total_pages, page_info = await self.load_conversations(new_page, keyword)

        return list_html, page, page_info

    async def next_page_handler(
        self,
        current_page: int,
        total_pages: int,
        keyword: str
    ) -> Tuple[str, int, str]:
        """下一页处理器"""
        if current_page >= total_pages:
            return gr.update(), current_page, f"第 {current_page} 页"

        new_page = current_page + 1
        list_html, page, total_pages, page_info = await self.load_conversations(new_page, keyword)

        return list_html, page, page_info

    async def export_handler(
        self,
        conversation_id: Optional[str],
        format: str
    ) -> Tuple[Optional[str], str]:
        """导出处理器"""
        if not conversation_id:
            return None, "请先选择一个对话"

        try:
            logger.info(f"Exporting conversation: id={conversation_id}, format={format}")

            content = await self.api_client.export_conversation(
                conversation_id=conversation_id,
                format=format
            )

            if not content:
                return None, "导出失败"

            # 保存到临时文件
            extensions = {
                "markdown": "md",
                "json": "json",
                "pdf": "pdf"
            }

            ext = extensions.get(format, "txt")
            temp_file = tempfile.NamedTemporaryFile(
                mode='wb',
                suffix=f'.{ext}',
                delete=False
            )

            temp_file.write(content)
            temp_file.close()

            logger.info(f"Export saved to: {temp_file.name}")

            return temp_file.name, f"导出成功: {format}"

        except Exception as e:
            logger.error(f"Export error: {e}", exc_info=True)
            return None, f"导出失败: {str(e)}"

    async def delete_handler(
        self,
        conversation_id: Optional[str]
    ) -> Tuple[str, str, None]:
        """删除处理器"""
        if not conversation_id:
            return gr.update(), gr.update(), None

        try:
            logger.info(f"Deleting conversation: id={conversation_id}")

            response = await self.api_client.delete_conversation(
                conversation_id=conversation_id,
                soft_delete=True
            )

            if response:
                # 清空详情显示
                info_html = "<div style='text-align: center; padding: 40px; color: #4caf50;'>✅ 对话已删除</div>"
                messages_html = ""
                return info_html, messages_html, None
            else:
                info_html = "<div style='text-align: center; padding: 40px; color: #f44336;'>❌ 删除失败</div>"
                return info_html, gr.update(), conversation_id

        except Exception as e:
            logger.error(f"Delete error: {e}", exc_info=True)
            info_html = f"<div style='text-align: center; padding: 40px; color: #f44336;'>删除失败: {str(e)}</div>"
            return info_html, gr.update(), conversation_id

    def _format_stats(self, stats: Dict[str, Any]) -> str:
        """格式化统计信息"""
        total = stats.get("total", 0)
        today = stats.get("today", 0)
        this_week = stats.get("this_week", 0)
        this_month = stats.get("this_month", 0)

        return f"""
### 📊 对话统计

- **总对话数**: {total}
- **今日新增**: {today}
- **本周**: {this_week}
- **本月**: {this_month}
"""

    def _format_conversation_list(self, conversations: List[Dict[str, Any]]) -> str:
        """格式化对话列表为 HTML"""
        if not conversations:
            return "<div style='text-align: center; padding: 40px; color: #666;'>暂无对话</div>"

        html_parts = []

        for conv in conversations:
            conv_id = conv.get("id", "")
            title = conv.get("title", "未命名对话")
            message_count = conv.get("message_count", 0)
            created_at = conv.get("created_at", "")
            updated_at = conv.get("updated_at", "")

            # 格式化时间
            try:
                created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                created_str = created_time.strftime("%Y-%m-%d %H:%M")
            except:
                created_str = created_at[:16] if created_at else "未知"

            # 卡片 HTML
            card_html = f"""
            <div style='border: 1px solid #e0e0e0; border-radius: 8px; padding: 12px; margin-bottom: 10px;
                        background: white; cursor: pointer; transition: all 0.2s;'
                 onclick='alert("对话ID: {conv_id}\\n标题: {title}\\n消息数: {message_count}")'>
                <div style='font-weight: bold; color: #1976d2; margin-bottom: 4px; font-size: 16px;'>
                    {title}
                </div>
                <div style='font-size: 12px; color: #666;'>
                    💬 {message_count} 条消息 • 📅 {created_str}
                </div>
            </div>
            """

            html_parts.append(card_html)

        return "\n".join(html_parts)


def create_history_page() -> gr.Blocks:
    """创建对话历史页面（工厂函数）"""
    page = HistoryPage()
    return page.create_ui()
