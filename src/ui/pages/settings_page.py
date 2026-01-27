"""
设置页面 - Gradio UI
Story 4.6: 模型切换 UI
"""
import logging
import gradio as gr
from typing import Optional, Tuple, List
import asyncio

from ..utils.api_client import get_api_client

logger = logging.getLogger(__name__)


class SettingsPage:
    """设置页面"""

    def __init__(self):
        self.api_client = get_api_client()
        logger.info("SettingsPage initialized")

    def create_ui(self) -> gr.Blocks:
        """创建设置页面 UI"""

        with gr.Blocks(title="KT-BOT - 设置") as demo:
            gr.Markdown(
                """
                # ⚙️ 系统设置
                管理模型、配置和系统参数
                """
            )

            with gr.Tabs():
                # Tab 1: 模型管理
                with gr.Tab("🤖 模型管理"):
                    with gr.Row():
                        # 左侧：模型选择
                        with gr.Column(scale=2):
                            gr.Markdown("### 模型选择")

                            # LLM 模型选择
                            with gr.Group():
                                gr.Markdown("#### 💬 对话模型 (LLM)")
                                llm_model_selector = gr.Dropdown(
                                    choices=[],
                                    label="选择对话模型",
                                    info="用于生成回复的大语言模型"
                                )
                                current_llm_label = gr.Textbox(
                                    label="当前模型",
                                    value="加载中...",
                                    interactive=False
                                )
                                llm_health_status = gr.Textbox(
                                    label="模型状态",
                                    value="未检查",
                                    interactive=False
                                )
                                with gr.Row():
                                    switch_llm_btn = gr.Button(
                                        "切换 LLM 模型",
                                        variant="primary",
                                        size="sm"
                                    )
                                    check_llm_health_btn = gr.Button(
                                        "健康检查",
                                        variant="secondary",
                                        size="sm"
                                    )

                            gr.Markdown("---")

                            # Embedding 模型选择
                            with gr.Group():
                                gr.Markdown("#### 🔢 Embedding 模型")
                                embedding_model_selector = gr.Dropdown(
                                    choices=[],
                                    label="选择 Embedding 模型",
                                    info="用于文档向量化的模型"
                                )
                                current_embedding_label = gr.Textbox(
                                    label="当前模型",
                                    value="加载中...",
                                    interactive=False
                                )
                                embedding_health_status = gr.Textbox(
                                    label="模型状态",
                                    value="未检查",
                                    interactive=False
                                )
                                gr.Markdown(
                                    """
                                    ⚠️ **重要提示**：切换 Embedding 模型需要重建向量索引，
                                    否则检索结果可能不准确！
                                    """
                                )
                                with gr.Row():
                                    switch_embedding_btn = gr.Button(
                                        "切换 Embedding 模型",
                                        variant="primary",
                                        size="sm"
                                    )
                                    check_embedding_health_btn = gr.Button(
                                        "健康检查",
                                        variant="secondary",
                                        size="sm"
                                    )

                        # 右侧：模型信息和操作日志
                        with gr.Column(scale=1):
                            gr.Markdown("### 📊 模型信息")

                            refresh_btn = gr.Button(
                                "🔄 刷新模型列表",
                                variant="secondary"
                            )

                            model_info_display = gr.JSON(
                                label="模型详细信息",
                                value={}
                            )

                            gr.Markdown("### 📝 操作日志")
                            operation_log = gr.Textbox(
                                label="",
                                value="",
                                lines=10,
                                max_lines=20,
                                show_label=False,
                                interactive=False,
                                placeholder="操作日志将显示在这里..."
                            )

            # ========================================================================
            # 事件绑定
            # ========================================================================

            # 页面加载时初始化
            demo.load(
                fn=self.load_models_handler,
                outputs=[
                    llm_model_selector,
                    embedding_model_selector,
                    current_llm_label,
                    current_embedding_label,
                    operation_log
                ]
            )

            # 刷新模型列表
            refresh_btn.click(
                fn=self.load_models_handler,
                outputs=[
                    llm_model_selector,
                    embedding_model_selector,
                    current_llm_label,
                    current_embedding_label,
                    operation_log
                ]
            )

            # 切换 LLM 模型
            switch_llm_btn.click(
                fn=self.switch_llm_handler,
                inputs=[llm_model_selector],
                outputs=[current_llm_label, llm_health_status, operation_log]
            )

            # 切换 Embedding 模型
            switch_embedding_btn.click(
                fn=self.switch_embedding_handler,
                inputs=[embedding_model_selector],
                outputs=[current_embedding_label, embedding_health_status, operation_log]
            )

            # LLM 健康检查
            check_llm_health_btn.click(
                fn=self.check_llm_health_handler,
                inputs=[current_llm_label],
                outputs=[llm_health_status, operation_log]
            )

            # Embedding 健康检查
            check_embedding_health_btn.click(
                fn=self.check_embedding_health_handler,
                inputs=[current_embedding_label],
                outputs=[embedding_health_status, operation_log]
            )

        return demo

    async def load_models_handler(self) -> Tuple[gr.Dropdown, gr.Dropdown, str, str, str]:
        """
        加载模型列表和当前模型

        Returns:
            (LLM选择器, Embedding选择器, 当前LLM, 当前Embedding, 日志)
        """
        try:
            logger.info("Loading models...")

            # 获取模型列表
            models_data = await self.api_client.get_models()

            llm_models = models_data.get("models", {}).get("llm", [])
            embedding_models = models_data.get("models", {}).get("embedding", [])

            current_llm = models_data.get("current", {}).get("llm") or "未设置"
            current_embedding = models_data.get("current", {}).get("embedding") or "未设置"

            log_message = f"✅ 模型列表加载成功\n" \
                         f"- LLM 模型: {len(llm_models)} 个\n" \
                         f"- Embedding 模型: {len(embedding_models)} 个\n" \
                         f"- 当前 LLM: {current_llm}\n" \
                         f"- 当前 Embedding: {current_embedding}"

            logger.info(log_message)

            return (
                gr.Dropdown(choices=llm_models, value=current_llm),
                gr.Dropdown(choices=embedding_models, value=current_embedding),
                current_llm,
                current_embedding,
                log_message
            )

        except Exception as e:
            error_msg = f"❌ 加载模型失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return (
                gr.Dropdown(choices=[]),
                gr.Dropdown(choices=[]),
                "加载失败",
                "加载失败",
                error_msg
            )

    async def switch_llm_handler(self, model_name: str) -> Tuple[str, str, str]:
        """
        切换 LLM 模型

        Args:
            model_name: 目标模型名称

        Returns:
            (当前模型, 健康状态, 日志)
        """
        if not model_name:
            return "未选择模型", "未检查", "❌ 请选择一个模型"

        try:
            logger.info(f"Switching LLM model to {model_name}")

            result = await self.api_client.switch_llm_model(model_name)

            if result:
                status = result.get("data", {}).get("status", "unknown")
                message = result.get("message", "")

                health_text = "✅ 健康" if status == "healthy" else "⚠️ 不健康"
                log_message = f"✅ LLM 模型切换成功\n" \
                             f"- 新模型: {model_name}\n" \
                             f"- 状态: {health_text}\n" \
                             f"- 消息: {message}"

                logger.info(log_message)
                return model_name, health_text, log_message
            else:
                error_msg = f"❌ 切换 LLM 模型失败: 无响应"
                logger.error(error_msg)
                return "切换失败", "❌ 失败", error_msg

        except Exception as e:
            error_msg = f"❌ 切换 LLM 模型失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return "切换失败", "❌ 错误", error_msg

    async def switch_embedding_handler(self, model_name: str) -> Tuple[str, str, str]:
        """
        切换 Embedding 模型

        Args:
            model_name: 目标模型名称

        Returns:
            (当前模型, 健康状态, 日志)
        """
        if not model_name:
            return "未选择模型", "未检查", "❌ 请选择一个模型"

        try:
            logger.info(f"Switching Embedding model to {model_name}")

            result = await self.api_client.switch_embedding_model(model_name)

            if result:
                status = result.get("data", {}).get("status", "unknown")
                message = result.get("message", "")
                warning = result.get("data", {}).get("warning", "")

                health_text = "✅ 健康" if status == "healthy" else "⚠️ 不健康"
                log_message = f"✅ Embedding 模型切换成功\n" \
                             f"- 新模型: {model_name}\n" \
                             f"- 状态: {health_text}\n" \
                             f"- 消息: {message}\n\n" \
                             f"⚠️ 警告:\n{warning}"

                logger.info(log_message)
                return model_name, health_text, log_message
            else:
                error_msg = f"❌ 切换 Embedding 模型失败: 无响应"
                logger.error(error_msg)
                return "切换失败", "❌ 失败", error_msg

        except Exception as e:
            error_msg = f"❌ 切换 Embedding 模型失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return "切换失败", "❌ 错误", error_msg

    async def check_llm_health_handler(self, current_model: str) -> Tuple[str, str]:
        """
        检查 LLM 模型健康状态

        Args:
            current_model: 当前模型名称

        Returns:
            (健康状态, 日志)
        """
        if not current_model or current_model == "未设置":
            return "未检查", "❌ 没有活动的 LLM 模型"

        try:
            logger.info(f"Checking LLM model health: {current_model}")

            status_data = await self.api_client.get_model_status()

            if status_data:
                health = status_data.get("health", {})
                llm_healthy = health.get("llm", False)

                health_text = "✅ 健康" if llm_healthy else "❌ 不健康"
                log_message = f"健康检查完成\n" \
                             f"- 模型: {current_model}\n" \
                             f"- 状态: {health_text}"

                logger.info(log_message)
                return health_text, log_message
            else:
                error_msg = "❌ 无法获取健康状态"
                return "❌ 错误", error_msg

        except Exception as e:
            error_msg = f"❌ 健康检查失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return "❌ 错误", error_msg

    async def check_embedding_health_handler(self, current_model: str) -> Tuple[str, str]:
        """
        检查 Embedding 模型健康状态

        Args:
            current_model: 当前模型名称

        Returns:
            (健康状态, 日志)
        """
        if not current_model or current_model == "未设置":
            return "未检查", "❌ 没有活动的 Embedding 模型"

        try:
            logger.info(f"Checking Embedding model health: {current_model}")

            status_data = await self.api_client.get_model_status()

            if status_data:
                health = status_data.get("health", {})
                embedding_healthy = health.get("embedding", False)

                health_text = "✅ 健康" if embedding_healthy else "❌ 不健康"
                log_message = f"健康检查完成\n" \
                             f"- 模型: {current_model}\n" \
                             f"- 状态: {health_text}"

                logger.info(log_message)
                return health_text, log_message
            else:
                error_msg = "❌ 无法获取健康状态"
                return "❌ 错误", error_msg

        except Exception as e:
            error_msg = f"❌ 健康检查失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return "❌ 错误", error_msg


def create_settings_page() -> gr.Blocks:
    """创建设置页面（工厂函数）"""
    page = SettingsPage()
    return page.create_ui()
