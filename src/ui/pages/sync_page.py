"""
同步状态页面 - Gradio UI
Story 4.7 Phase 2: 同步状态显示 UI
"""

import logging
import gradio as gr
from typing import Dict, Any, List, Tuple
import asyncio
from datetime import datetime

from ..utils.api_client import get_api_client

logger = logging.getLogger(__name__)


class SyncPage:
    """同步状态页面"""

    def __init__(self):
        self.api_client = get_api_client()
        logger.info("SyncPage initialized")

    def create_ui(self) -> gr.Blocks:
        """创建同步状态页面 UI"""

        with gr.Blocks(title="KT-BOT - 同步状态") as demo:
            gr.Markdown(
                """
                # 🔄 数据同步管理
                实时监控同步任务状态，管理同步配置
                """
            )

            with gr.Row():
                # 左侧：同步控制面板
                with gr.Column(scale=1):
                    gr.Markdown("### 🎮 同步控制")

                    # 手动触发同步
                    with gr.Group():
                        gr.Markdown("#### 手动触发同步")

                        trigger_source = gr.Dropdown(
                            choices=["jira", "confluence"],
                            value="jira",
                            label="数据源"
                        )

                        trigger_type = gr.Dropdown(
                            choices=["full", "incremental"],
                            value="incremental",
                            label="同步类型",
                            info="full: 全量同步 | incremental: 增量同步"
                        )

                        with gr.Row():
                            trigger_jira_btn = gr.Button(
                                "🔶 同步 Jira",
                                variant="primary",
                                size="lg"
                            )
                            trigger_confluence_btn = gr.Button(
                                "📘 同步 Confluence",
                                variant="primary",
                                size="lg"
                            )

                    # 调度器状态
                    with gr.Group():
                        gr.Markdown("#### 📊 调度器状态")
                        scheduler_status = gr.JSON(
                            label="",
                            show_label=False
                        )
                        refresh_scheduler_btn = gr.Button(
                            "🔄 刷新状态",
                            size="sm"
                        )

                    # 同步配置
                    with gr.Group():
                        gr.Markdown("#### ⚙️ 同步配置")

                        config_source = gr.Dropdown(
                            choices=["jira", "confluence"],
                            value="jira",
                            label="数据源"
                        )

                        config_display = gr.JSON(
                            label="当前配置",
                            show_label=True
                        )

                        with gr.Row():
                            load_config_btn = gr.Button(
                                "📥 加载配置",
                                size="sm"
                            )
                            reload_config_btn = gr.Button(
                                "🔄 重载配置",
                                size="sm"
                            )

                # 右侧：同步状态监控
                with gr.Column(scale=2):
                    gr.Markdown("### 📈 实时同步状态")

                    # 运行中的任务
                    with gr.Group():
                        gr.Markdown("#### 🏃 运行中的任务")

                        running_tasks_display = gr.HTML(
                            value="<div style='text-align: center; padding: 20px; color: #666;'>"
                                  "暂无运行中的任务</div>"
                        )

                        with gr.Row():
                            auto_refresh = gr.Checkbox(
                                label="自动刷新",
                                value=False,
                                info="每2秒自动刷新运行中的任务"
                            )
                            refresh_running_btn = gr.Button(
                                "🔄 刷新",
                                size="sm"
                            )

                    # 最近同步历史
                    with gr.Group():
                        gr.Markdown("#### 📜 最近同步历史")

                        history_source_filter = gr.Dropdown(
                            choices=["全部", "jira", "confluence"],
                            value="全部",
                            label="数据源过滤"
                        )

                        history_display = gr.HTML(
                            value="<div style='text-align: center; padding: 20px; color: #666;'>"
                                  "加载中...</div>"
                        )

                        refresh_history_btn = gr.Button(
                            "🔄 刷新历史",
                            size="sm"
                        )

                    # 同步统计
                    with gr.Group():
                        gr.Markdown("#### 📊 同步统计（最近7天）")

                        stats_source_filter = gr.Dropdown(
                            choices=["全部", "jira", "confluence"],
                            value="全部",
                            label="数据源"
                        )

                        stats_display = gr.JSON(
                            label="",
                            show_label=False
                        )

                        refresh_stats_btn = gr.Button(
                            "🔄 刷新统计",
                            size="sm"
                        )

            # 操作日志
            with gr.Row():
                operation_log = gr.Textbox(
                    label="📝 操作日志",
                    lines=3,
                    max_lines=5,
                    interactive=False
                )

            # ========================================================================
            # 事件绑定
            # ========================================================================

            # 触发 Jira 同步
            trigger_jira_btn.click(
                fn=lambda sync_type: self.trigger_sync_handler("jira", sync_type),
                inputs=[trigger_type],
                outputs=[operation_log]
            )

            # 触发 Confluence 同步
            trigger_confluence_btn.click(
                fn=lambda sync_type: self.trigger_sync_handler("confluence", sync_type),
                inputs=[trigger_type],
                outputs=[operation_log]
            )

            # 刷新调度器状态
            refresh_scheduler_btn.click(
                fn=self.get_scheduler_status_handler,
                inputs=[],
                outputs=[scheduler_status, operation_log]
            )

            # 加载配置
            load_config_btn.click(
                fn=self.load_config_handler,
                inputs=[config_source],
                outputs=[config_display, operation_log]
            )

            # 重载配置
            reload_config_btn.click(
                fn=self.reload_config_handler,
                inputs=[],
                outputs=[operation_log]
            )

            # 刷新运行中的任务
            refresh_running_btn.click(
                fn=self.get_running_tasks_handler,
                inputs=[],
                outputs=[running_tasks_display, operation_log]
            )

            # 刷新历史
            refresh_history_btn.click(
                fn=self.get_history_handler,
                inputs=[history_source_filter],
                outputs=[history_display, operation_log]
            )

            # 刷新统计
            refresh_stats_btn.click(
                fn=self.get_stats_handler,
                inputs=[stats_source_filter],
                outputs=[stats_display, operation_log]
            )

            # 自动刷新运行中的任务
            auto_refresh.change(
                fn=self.auto_refresh_handler,
                inputs=[auto_refresh],
                outputs=[running_tasks_display]
            )

            # 页面加载时初始化数据
            demo.load(
                fn=self.init_page_handler,
                inputs=[],
                outputs=[
                    scheduler_status,
                    running_tasks_display,
                    history_display,
                    stats_display,
                    operation_log
                ]
            )

        return demo

    # ========================================================================
    # 事件处理器
    # ========================================================================

    async def trigger_sync_handler(
        self,
        source: str,
        sync_type: str
    ) -> str:
        """触发同步处理器"""
        try:
            logger.info(f"Triggering sync: source={source}, type={sync_type}")

            response = await self.api_client.trigger_sync(
                source=source,
                sync_type=sync_type
            )

            if response and response.get("success"):
                task_id = response.get("task_id", "")
                message = response.get("message", "")
                log = f"✅ [{datetime.now().strftime('%H:%M:%S')}] {message}"
                logger.info(f"Sync triggered: {task_id}")
                return log
            else:
                log = f"❌ [{datetime.now().strftime('%H:%M:%S')}] 触发同步失败"
                return log

        except Exception as e:
            logger.error(f"Error triggering sync: {e}", exc_info=True)
            return f"❌ [{datetime.now().strftime('%H:%M:%S')}] 触发同步出错: {str(e)}"

    async def get_scheduler_status_handler(self) -> Tuple[Dict, str]:
        """获取调度器状态处理器"""
        try:
            response = await self.api_client.get_scheduler_status()

            if response and "data" in response:
                data = response["data"]
                log = f"✅ [{datetime.now().strftime('%H:%M:%S')}] 调度器状态已刷新"
                return data, log
            else:
                return {}, f"❌ [{datetime.now().strftime('%H:%M:%S')}] 获取调度器状态失败"

        except Exception as e:
            logger.error(f"Error getting scheduler status: {e}", exc_info=True)
            return {}, f"❌ [{datetime.now().strftime('%H:%M:%S')}] 获取状态出错: {str(e)}"

    async def load_config_handler(self, source: str) -> Tuple[Dict, str]:
        """加载配置处理器"""
        try:
            response = await self.api_client.get_sync_config(source)

            if response and "data" in response:
                data = response["data"]
                log = f"✅ [{datetime.now().strftime('%H:%M:%S')}] 已加载 {source} 配置"
                return data, log
            else:
                return {}, f"❌ [{datetime.now().strftime('%H:%M:%S')}] 加载配置失败"

        except Exception as e:
            logger.error(f"Error loading config: {e}", exc_info=True)
            return {}, f"❌ [{datetime.now().strftime('%H:%M:%S')}] 加载配置出错: {str(e)}"

    async def reload_config_handler(self) -> str:
        """重载配置处理器"""
        try:
            response = await self.api_client.reload_sync_config()

            if response and response.get("success"):
                return f"✅ [{datetime.now().strftime('%H:%M:%S')}] 配置已重新加载"
            else:
                return f"❌ [{datetime.now().strftime('%H:%M:%S')}] 重载配置失败"

        except Exception as e:
            logger.error(f"Error reloading config: {e}", exc_info=True)
            return f"❌ [{datetime.now().strftime('%H:%M:%S')}] 重载配置出错: {str(e)}"

    async def get_running_tasks_handler(self) -> Tuple[str, str]:
        """获取运行中的任务处理器"""
        try:
            response = await self.api_client.get_running_tasks()

            if response and "data" in response:
                data = response["data"]
                tasks = data.get("tasks", [])
                count = data.get("count", 0)

                if count == 0:
                    html = ("<div style='text-align: center; padding: 20px; color: #666;'>"
                           "暂无运行中的任务</div>")
                else:
                    html = self._format_running_tasks(tasks)

                log = f"✅ [{datetime.now().strftime('%H:%M:%S')}] 找到 {count} 个运行中的任务"
                return html, log
            else:
                html = ("<div style='text-align: center; padding: 20px; color: #f44336;'>"
                       "❌ 获取运行中任务失败</div>")
                return html, f"❌ [{datetime.now().strftime('%H:%M:%S')}] 获取运行中任务失败"

        except Exception as e:
            logger.error(f"Error getting running tasks: {e}", exc_info=True)
            html = f"<div style='text-align: center; padding: 20px; color: #f44336;'>❌ 出错: {str(e)}</div>"
            return html, f"❌ [{datetime.now().strftime('%H:%M:%S')}] 获取任务出错: {str(e)}"

    async def get_history_handler(self, source_filter: str) -> Tuple[str, str]:
        """获取历史记录处理器"""
        try:
            source = None if source_filter == "全部" else source_filter

            response = await self.api_client.get_sync_history(
                source=source,
                page=1,
                page_size=10
            )

            if response and "data" in response:
                data = response["data"]
                items = data.get("items", [])
                total = data.get("total", 0)

                if total == 0:
                    html = ("<div style='text-align: center; padding: 20px; color: #666;'>"
                           "暂无历史记录</div>")
                else:
                    html = self._format_history(items)

                log = f"✅ [{datetime.now().strftime('%H:%M:%S')}] 找到 {total} 条历史记录"
                return html, log
            else:
                html = ("<div style='text-align: center; padding: 20px; color: #f44336;'>"
                       "❌ 获取历史记录失败</div>")
                return html, f"❌ [{datetime.now().strftime('%H:%M:%S')}] 获取历史记录失败"

        except Exception as e:
            logger.error(f"Error getting history: {e}", exc_info=True)
            html = f"<div style='text-align: center; padding: 20px; color: #f44336;'>❌ 出错: {str(e)}</div>"
            return html, f"❌ [{datetime.now().strftime('%H:%M:%S')}] 获取历史出错: {str(e)}"

    async def get_stats_handler(self, source_filter: str) -> Tuple[Dict, str]:
        """获取统计信息处理器"""
        try:
            source = None if source_filter == "全部" else source_filter

            response = await self.api_client.get_sync_statistics(
                source=source,
                days=7
            )

            if response and "data" in response:
                data = response["data"]
                log = f"✅ [{datetime.now().strftime('%H:%M:%S')}] 统计信息已刷新"
                return data, log
            else:
                return {}, f"❌ [{datetime.now().strftime('%H:%M:%S')}] 获取统计信息失败"

        except Exception as e:
            logger.error(f"Error getting statistics: {e}", exc_info=True)
            return {}, f"❌ [{datetime.now().strftime('%H:%M:%S')}] 获取统计出错: {str(e)}"

    async def auto_refresh_handler(self, enabled: bool) -> str:
        """自动刷新处理器"""
        if not enabled:
            return "<div style='text-align: center; padding: 20px; color: #666;'>自动刷新已停止</div>"

        # TODO: 实现自动刷新逻辑
        # 这里需要使用定时器或者 SSE 来实现实时更新
        return "<div style='text-align: center; padding: 20px; color: #666;'>自动刷新功能开发中...</div>"

    async def init_page_handler(self) -> Tuple[Dict, str, str, Dict, str]:
        """页面初始化处理器"""
        try:
            # 获取调度器状态
            scheduler_response = await self.api_client.get_scheduler_status()
            scheduler_data = scheduler_response.get("data", {}) if scheduler_response else {}

            # 获取运行中的任务
            running_response = await self.api_client.get_running_tasks()
            if running_response and "data" in running_response:
                tasks = running_response["data"].get("tasks", [])
                count = running_response["data"].get("count", 0)
                if count == 0:
                    running_html = ("<div style='text-align: center; padding: 20px; color: #666;'>"
                                   "暂无运行中的任务</div>")
                else:
                    running_html = self._format_running_tasks(tasks)
            else:
                running_html = ("<div style='text-align: center; padding: 20px; color: #666;'>"
                               "暂无运行中的任务</div>")

            # 获取历史记录
            history_response = await self.api_client.get_sync_history(page=1, page_size=10)
            if history_response and "data" in history_response:
                items = history_response["data"].get("items", [])
                if items:
                    history_html = self._format_history(items)
                else:
                    history_html = ("<div style='text-align: center; padding: 20px; color: #666;'>"
                                   "暂无历史记录</div>")
            else:
                history_html = ("<div style='text-align: center; padding: 20px; color: #666;'>"
                               "暂无历史记录</div>")

            # 获取统计信息
            stats_response = await self.api_client.get_sync_statistics(days=7)
            stats_data = stats_response.get("data", {}) if stats_response else {}

            log = f"✅ [{datetime.now().strftime('%H:%M:%S')}] 页面已初始化"

            return scheduler_data, running_html, history_html, stats_data, log

        except Exception as e:
            logger.error(f"Error initializing page: {e}", exc_info=True)
            return (
                {},
                "<div style='text-align: center; padding: 20px; color: #f44336;'>初始化失败</div>",
                "<div style='text-align: center; padding: 20px; color: #f44336;'>初始化失败</div>",
                {},
                f"❌ [{datetime.now().strftime('%H:%M:%S')}] 初始化出错: {str(e)}"
            )

    # ========================================================================
    # 格式化函数
    # ========================================================================

    def _format_running_tasks(self, tasks: List[Dict]) -> str:
        """格式化运行中的任务为 HTML"""
        html_parts = []

        for task in tasks:
            task_id = task.get("task_id", "")
            source = task.get("source", "unknown")
            sync_type = task.get("sync_type", "unknown")
            status = task.get("status", "unknown")
            progress = task.get("progress_percentage", 0)
            synced = task.get("synced_items", 0)
            total = task.get("total_items", 0)
            failed = task.get("failed_items", 0)
            duration = task.get("duration_seconds", 0)

            # 来源图标
            source_icon = {
                "jira": "🔶",
                "confluence": "📘"
            }.get(source, "📄")

            # 状态颜色
            status_color = {
                "running": "#1976d2",
                "pending": "#ff9800",
            }.get(status, "#666")

            # 进度条
            progress_bar = f"""
            <div style='background: #e0e0e0; border-radius: 10px; height: 20px; margin: 8px 0; overflow: hidden;'>
                <div style='background: #4caf50; height: 100%; width: {progress}%; text-align: center;
                            line-height: 20px; color: white; font-size: 12px; font-weight: bold;'>
                    {progress}%
                </div>
            </div>
            """

            card_html = f"""
            <div style='border: 1px solid #e0e0e0; border-radius: 8px; padding: 16px; margin-bottom: 12px; background: white;'>
                <div style='display: flex; align-items: center; margin-bottom: 8px;'>
                    <span style='font-size: 24px; margin-right: 8px;'>{source_icon}</span>
                    <div style='flex: 1;'>
                        <div style='font-weight: bold; font-size: 16px;'>{source} - {sync_type}</div>
                        <div style='font-size: 12px; color: {status_color}; margin-top: 4px;'>
                            状态: {status} • 任务ID: {task_id[:8]}...
                        </div>
                    </div>
                </div>
                {progress_bar}
                <div style='font-size: 13px; color: #666; margin-top: 8px;'>
                    已同步: {synced}/{total} • 失败: {failed} • 耗时: {duration}s
                </div>
            </div>
            """

            html_parts.append(card_html)

        return "\n".join(html_parts)

    def _format_history(self, items: List[Dict]) -> str:
        """格式化历史记录为 HTML"""
        html_parts = []

        for item in items:
            task_id = item.get("task_id", "")
            source = item.get("source", "unknown")
            sync_type = item.get("sync_type", "unknown")
            status = item.get("status", "unknown")
            synced = item.get("synced_items", 0)
            total = item.get("total_items", 0)
            failed = item.get("failed_items", 0)
            duration = item.get("duration_seconds", 0)
            start_time = item.get("start_time", "")
            error_message = item.get("error_message", "")

            # 来源图标
            source_icon = {
                "jira": "🔶",
                "confluence": "📘"
            }.get(source, "📄")

            # 状态图标和颜色
            if status == "completed":
                status_icon = "✅"
                status_color = "#4caf50"
                status_text = "完成"
            elif status == "failed":
                status_icon = "❌"
                status_color = "#f44336"
                status_text = "失败"
            elif status == "cancelled":
                status_icon = "🚫"
                status_color = "#ff9800"
                status_text = "已取消"
            else:
                status_icon = "⏳"
                status_color = "#666"
                status_text = status

            # 错误信息
            error_html = ""
            if error_message:
                error_html = f"""
                <div style='font-size: 12px; color: #f44336; margin-top: 8px; padding: 8px;
                            background: #ffebee; border-radius: 4px;'>
                    错误: {error_message}
                </div>
                """

            card_html = f"""
            <div style='border: 1px solid #e0e0e0; border-radius: 8px; padding: 12px; margin-bottom: 8px; background: white;'>
                <div style='display: flex; align-items: center; margin-bottom: 8px;'>
                    <span style='font-size: 20px; margin-right: 8px;'>{source_icon}</span>
                    <div style='flex: 1;'>
                        <div style='font-weight: bold; font-size: 14px;'>{source} - {sync_type}</div>
                        <div style='font-size: 11px; color: #666; margin-top: 2px;'>
                            {start_time} • ID: {task_id[:8]}...
                        </div>
                    </div>
                    <div style='font-size: 16px; color: {status_color};'>
                        {status_icon} {status_text}
                    </div>
                </div>
                <div style='font-size: 12px; color: #666;'>
                    已同步: {synced}/{total} • 失败: {failed} • 耗时: {duration}s
                </div>
                {error_html}
            </div>
            """

            html_parts.append(card_html)

        return "\n".join(html_parts)


def create_sync_page() -> gr.Blocks:
    """创建同步状态页面（工厂函数）"""
    page = SyncPage()
    return page.create_ui()
