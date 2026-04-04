"""
性能监控页面 - Gradio UI
Story 5.5: 性能监控面板
"""

import logging
import gradio as gr
from typing import Dict, Any, List, Tuple
import asyncio
from datetime import datetime

from ..utils.api_client import get_api_client

logger = logging.getLogger(__name__)


class MetricsPage:
    """性能监控页面"""

    def __init__(self):
        self.api_client = get_api_client()
        logger.info("MetricsPage initialized")

    def create_ui(self) -> gr.Blocks:
        """创建监控页面 UI"""

        with gr.Blocks(title="KT-BOT - 性能监控") as demo:
            gr.Markdown("# 📊 性能监控面板")

            # 顶部：4 个关键指标卡片
            with gr.Row():
                metrics_cards = gr.HTML(
                    value="<div style='text-align: center; padding: 20px; color: #666;'>加载中...</div>",
                    label="系统概览"
                )

            # 中间：API 性能和数据库状态
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### ⚡ API 性能统计")
                    api_stats_display = gr.HTML(
                        value="<div style='text-align: center; padding: 20px; color: #666;'>加载中...</div>"
                    )

                with gr.Column(scale=1):
                    gr.Markdown("### 💾 数据库连接池")
                    db_stats_display = gr.HTML(
                        value="<div style='text-align: center; padding: 20px; color: #666;'>加载中...</div>"
                    )

            # 底部：最慢端点 Top 10
            with gr.Row():
                gr.Markdown("### 🐌 最慢端点 Top 10")

            with gr.Row():
                slowest_endpoints_display = gr.HTML(
                    value="<div style='text-align: center; padding: 20px; color: #666;'>加载中...</div>"
                )

            # 控制按钮
            with gr.Row():
                refresh_btn = gr.Button("🔄 刷新", variant="primary", size="lg")
                operation_log = gr.Textbox(
                    label="📝 操作日志",
                    lines=2,
                    interactive=False
                )

            # ========================================================================
            # 事件绑定
            # ========================================================================

            # 页面加载时初始化
            demo.load(
                fn=self.load_all_metrics,
                outputs=[
                    metrics_cards,
                    api_stats_display,
                    db_stats_display,
                    slowest_endpoints_display,
                    operation_log
                ]
            )

            # 刷新按钮
            refresh_btn.click(
                fn=self.load_all_metrics,
                outputs=[
                    metrics_cards,
                    api_stats_display,
                    db_stats_display,
                    slowest_endpoints_display,
                    operation_log
                ]
            )

        return demo

    async def load_all_metrics(self) -> Tuple[str, str, str, str, str]:
        """加载所有指标"""
        try:
            # 并发获取所有指标
            system_task = self.api_client.get_system_metrics()
            database_task = self.api_client.get_database_metrics()
            api_task = self.api_client.get_api_metrics()

            system, database, api = await asyncio.gather(
                system_task,
                database_task,
                api_task
            )

            # 检查是否有错误
            if not system or not database or not api:
                error_msg = "<div style='text-align: center; padding: 20px; color: #f44336;'>❌ 加载失败</div>"
                log = f"❌ [{datetime.now().strftime('%H:%M:%S')}] 加载指标失败"
                return error_msg, error_msg, error_msg, error_msg, log

            # 格式化为 HTML
            cards_html = self._format_metric_cards(system, database, api)
            api_html = self._format_api_stats(api)
            db_html = self._format_db_stats(database)
            slowest_html = self._format_slowest_endpoints(api)
            log = f"✅ [{datetime.now().strftime('%H:%M:%S')}] 刷新成功"

            return cards_html, api_html, db_html, slowest_html, log

        except Exception as e:
            logger.error(f"Error loading metrics: {e}", exc_info=True)
            error_msg = f"<div style='text-align: center; padding: 20px; color: #f44336;'>❌ 加载失败: {str(e)}</div>"
            log = f"❌ [{datetime.now().strftime('%H:%M:%S')}] 加载出错: {str(e)}"
            return error_msg, error_msg, error_msg, error_msg, log

    # ========================================================================
    # 格式化函数
    # ========================================================================

    def _format_metric_cards(self, system: Dict, database: Dict, api: Dict) -> str:
        """格式化指标卡片（4 个关键指标）"""

        # CPU 使用率
        cpu_percent = system.get("cpu_percent", 0)
        cpu_color = self._get_color(cpu_percent)

        # 内存使用率
        memory_percent = system.get("memory_percent", 0)
        memory_available = system.get("memory_available_gb", 0)
        memory_total = system.get("memory_total_gb", 0)
        memory_color = self._get_color(memory_percent)

        # 数据库连接池
        pool_checked_out = database.get("pool_checked_out", 0)
        pool_size = database.get("pool_size", 0)
        pool_usage_percent = database.get("pool_usage_percent", 0)
        db_color = self._get_color(pool_usage_percent)

        # API 平均响应时间
        avg_response_time = api.get("avg_response_time_ms", 0)
        # 响应时间颜色判断（< 100ms 绿色，100-500ms 黄色，> 500ms 红色）
        if avg_response_time < 100:
            api_color = "#4caf50"
        elif avg_response_time < 500:
            api_color = "#ff9800"
        else:
            api_color = "#f44336"

        return f"""
        <div style='display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px;'>
            <!-- CPU 卡片 -->
            <div style='border: 1px solid #e0e0e0; border-radius: 8px;
                        padding: 20px; text-align: center; background: white;'>
                <div style='font-size: 14px; color: #666; margin-bottom: 8px;'>CPU 使用率</div>
                <div style='font-size: 32px; font-weight: bold; color: {cpu_color};'>
                    {cpu_percent:.1f}%
                </div>
            </div>

            <!-- 内存卡片 -->
            <div style='border: 1px solid #e0e0e0; border-radius: 8px;
                        padding: 20px; text-align: center; background: white;'>
                <div style='font-size: 14px; color: #666; margin-bottom: 8px;'>内存使用率</div>
                <div style='font-size: 32px; font-weight: bold; color: {memory_color};'>
                    {memory_percent:.1f}%
                </div>
                <div style='font-size: 12px; color: #999; margin-top: 4px;'>
                    {memory_available:.1f}GB / {memory_total:.1f}GB
                </div>
            </div>

            <!-- 数据库连接池卡片 -->
            <div style='border: 1px solid #e0e0e0; border-radius: 8px;
                        padding: 20px; text-align: center; background: white;'>
                <div style='font-size: 14px; color: #666; margin-bottom: 8px;'>数据库连接</div>
                <div style='font-size: 32px; font-weight: bold; color: {db_color};'>
                    {pool_checked_out} / {pool_size}
                </div>
                <div style='font-size: 12px; color: #999; margin-top: 4px;'>
                    使用率: {pool_usage_percent:.1f}%
                </div>
            </div>

            <!-- API 平均响应时间卡片 -->
            <div style='border: 1px solid #e0e0e0; border-radius: 8px;
                        padding: 20px; text-align: center; background: white;'>
                <div style='font-size: 14px; color: #666; margin-bottom: 8px;'>API 响应时间</div>
                <div style='font-size: 32px; font-weight: bold; color: {api_color};'>
                    {avg_response_time:.0f} ms
                </div>
            </div>
        </div>
        """

    def _format_api_stats(self, api: Dict) -> str:
        """格式化 API 性能统计"""

        total_requests = api.get("total_requests", 0)
        avg_response_time = api.get("avg_response_time_ms", 0)
        p50_response_time = api.get("p50_response_time_ms", 0)
        p95_response_time = api.get("p95_response_time_ms", 0)
        p99_response_time = api.get("p99_response_time_ms", 0)
        requests_per_minute = api.get("requests_per_minute", 0)

        if total_requests == 0:
            return "<div style='text-align: center; padding: 20px; color: #666;'>暂无 API 请求数据</div>"

        return f"""
        <div style='border: 1px solid #e0e0e0; border-radius: 8px; padding: 16px; background: white;'>
            <div style='display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px;'>
                <div>
                    <div style='font-size: 12px; color: #666;'>总请求数</div>
                    <div style='font-size: 20px; font-weight: bold; color: #1976d2;'>{total_requests}</div>
                </div>
                <div>
                    <div style='font-size: 12px; color: #666;'>请求速率</div>
                    <div style='font-size: 20px; font-weight: bold; color: #1976d2;'>{requests_per_minute:.1f}/分钟</div>
                </div>
                <div>
                    <div style='font-size: 12px; color: #666;'>平均响应时间</div>
                    <div style='font-size: 20px; font-weight: bold; color: #4caf50;'>{avg_response_time:.0f} ms</div>
                </div>
                <div>
                    <div style='font-size: 12px; color: #666;'>P50 响应时间</div>
                    <div style='font-size: 20px; font-weight: bold; color: #4caf50;'>{p50_response_time:.0f} ms</div>
                </div>
                <div>
                    <div style='font-size: 12px; color: #666;'>P95 响应时间</div>
                    <div style='font-size: 20px; font-weight: bold; color: #ff9800;'>{p95_response_time:.0f} ms</div>
                </div>
                <div>
                    <div style='font-size: 12px; color: #666;'>P99 响应时间</div>
                    <div style='font-size: 20px; font-weight: bold; color: #f44336;'>{p99_response_time:.0f} ms</div>
                </div>
            </div>
        </div>
        """

    def _format_db_stats(self, database: Dict) -> str:
        """格式化数据库连接池统计"""

        pool_size = database.get("pool_size", 0)
        pool_checked_out = database.get("pool_checked_out", 0)
        pool_overflow = database.get("pool_overflow", 0)
        pool_checked_in = database.get("pool_checked_in", 0)
        pool_usage_percent = database.get("pool_usage_percent", 0)

        usage_color = self._get_color(pool_usage_percent)

        return f"""
        <div style='border: 1px solid #e0e0e0; border-radius: 8px; padding: 16px; background: white;'>
            <div style='display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px;'>
                <div>
                    <div style='font-size: 12px; color: #666;'>连接池大小</div>
                    <div style='font-size: 20px; font-weight: bold; color: #1976d2;'>{pool_size}</div>
                </div>
                <div>
                    <div style='font-size: 12px; color: #666;'>使用率</div>
                    <div style='font-size: 20px; font-weight: bold; color: {usage_color};'>{pool_usage_percent:.1f}%</div>
                </div>
                <div>
                    <div style='font-size: 12px; color: #666;'>已签出</div>
                    <div style='font-size: 20px; font-weight: bold; color: #4caf50;'>{pool_checked_out}</div>
                </div>
                <div>
                    <div style='font-size: 12px; color: #666;'>已签入</div>
                    <div style='font-size: 20px; font-weight: bold; color: #666;'>{pool_checked_in}</div>
                </div>
                <div>
                    <div style='font-size: 12px; color: #666;'>溢出连接</div>
                    <div style='font-size: 20px; font-weight: bold; color: #ff9800;'>{pool_overflow}</div>
                </div>
            </div>
        </div>
        """

    def _format_slowest_endpoints(self, api: Dict) -> str:
        """格式化最慢端点 Top 10"""

        slowest_endpoints = api.get("slowest_endpoints", [])

        if not slowest_endpoints:
            return "<div style='text-align: center; padding: 20px; color: #666;'>暂无端点数据</div>"

        # 表格头部
        html = """
        <div style='border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden; background: white;'>
            <table style='width: 100%; border-collapse: collapse;'>
                <thead>
                    <tr style='background: #f5f5f5;'>
                        <th style='padding: 12px; text-align: left; font-weight: bold; border-bottom: 2px solid #e0e0e0;'>端点</th>
                        <th style='padding: 12px; text-align: center; font-weight: bold; border-bottom: 2px solid #e0e0e0;'>调用次数</th>
                        <th style='padding: 12px; text-align: center; font-weight: bold; border-bottom: 2px solid #e0e0e0;'>平均耗时</th>
                        <th style='padding: 12px; text-align: center; font-weight: bold; border-bottom: 2px solid #e0e0e0;'>最大耗时</th>
                    </tr>
                </thead>
                <tbody>
        """

        # 表格行
        for i, endpoint in enumerate(slowest_endpoints):
            endpoint_name = endpoint.get("endpoint", "Unknown")
            count = endpoint.get("count", 0)
            avg_duration = endpoint.get("avg_duration_ms", 0)
            max_duration = endpoint.get("max_duration_ms", 0)

            # 交替行颜色
            bg_color = "#fafafa" if i % 2 == 0 else "white"

            # 耗时颜色编码
            avg_color = "#4caf50" if avg_duration < 100 else ("#ff9800" if avg_duration < 500 else "#f44336")
            max_color = "#4caf50" if max_duration < 200 else ("#ff9800" if max_duration < 1000 else "#f44336")

            html += f"""
                <tr style='background: {bg_color};'>
                    <td style='padding: 12px; border-bottom: 1px solid #e0e0e0;'>
                        <span style='font-family: monospace; font-size: 12px;'>{endpoint_name}</span>
                    </td>
                    <td style='padding: 12px; text-align: center; border-bottom: 1px solid #e0e0e0;'>{count}</td>
                    <td style='padding: 12px; text-align: center; border-bottom: 1px solid #e0e0e0;'>
                        <span style='color: {avg_color}; font-weight: bold;'>{avg_duration:.0f} ms</span>
                    </td>
                    <td style='padding: 12px; text-align: center; border-bottom: 1px solid #e0e0e0;'>
                        <span style='color: {max_color}; font-weight: bold;'>{max_duration:.0f} ms</span>
                    </td>
                </tr>
            """

        html += """
                </tbody>
            </table>
        </div>
        """

        return html

    def _get_color(self, value: float) -> str:
        """
        根据值返回颜色（绿/黄/红）

        Args:
            value: 百分比值（0-100）

        Returns:
            颜色代码
        """
        if value < 70:
            return "#4caf50"  # 绿色
        elif value < 85:
            return "#ff9800"  # 橙色
        else:
            return "#f44336"  # 红色


def create_metrics_page() -> gr.Blocks:
    """创建监控页面（工厂函数）"""
    page = MetricsPage()
    return page.create_ui()
