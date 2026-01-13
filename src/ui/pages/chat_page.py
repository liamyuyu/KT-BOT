"""
主对话页面 - Gradio UI
"""
import logging
import gradio as gr
from typing import List, Tuple, Optional
import asyncio

from ..utils.api_client import get_api_client

logger = logging.getLogger(__name__)


class ChatPage:
    """对话页面"""

    def __init__(self):
        self.api_client = get_api_client()
        logger.info("ChatPage initialized")

    def create_ui(self) -> gr.Blocks:
        """创建 Gradio UI"""

        with gr.Blocks(
            title="KT-BOT - 知识库助手",
            theme=gr.themes.Soft(),
            css=self._get_custom_css()
        ) as demo:
            # 页面标题
            gr.Markdown(
                """
                # 🤖 KT-BOT - 企业知识库智能助手

                基于 RAG（检索增强生成）技术，为您提供精准的知识库问答服务
                """
            )

            # 会话状态
            session_id_state = gr.State(value=None)

            with gr.Row():
                # 左侧：对话区域
                with gr.Column(scale=3):
                    # 对话框
                    chatbot = gr.Chatbot(
                        label="对话历史",
                        height=500,
                        show_copy_button=True,
                        avatar_images=(
                            None,  # 用户头像
                            None   # 助手头像
                        )
                    )

                    # 输入区域
                    with gr.Row():
                        with gr.Column(scale=9):
                            user_input = gr.Textbox(
                                label="",
                                placeholder="请输入您的问题...",
                                lines=2,
                                max_lines=5,
                                show_label=False
                            )

                        with gr.Column(scale=1, min_width=100):
                            send_btn = gr.Button(
                                "发送",
                                variant="primary",
                                size="lg"
                            )

                    # 示例问题
                    gr.Examples(
                        examples=[
                            "JIRA 中如何创建新的工作项？",
                            "如何配置项目的权限设置？",
                            "什么是 Sprint 和 Epic？",
                            "如何导出 JIRA 报告？"
                        ],
                        inputs=user_input,
                        label="💡 示例问题（点击快速输入）"
                    )

                # 右侧：配置面板
                with gr.Column(scale=1, min_width=250):
                    gr.Markdown("### ⚙️ 设置")

                    # 模型选择
                    model_selector = gr.Dropdown(
                        choices=["qwen2.5:7b", "qwen2.5:14b", "llama3.1:8b"],
                        value="qwen2.5:7b",
                        label="LLM 模型",
                        info="选择生成模型"
                    )

                    # RAG 开关
                    rag_enabled = gr.Checkbox(
                        value=True,
                        label="启用 RAG 检索",
                        info="自动检索相关文档"
                    )

                    # RAG 参数
                    with gr.Group(visible=True) as rag_params:
                        rag_top_k = gr.Slider(
                            minimum=1,
                            maximum=10,
                            value=3,
                            step=1,
                            label="检索文档数量",
                            info="Top-K 相关文档"
                        )

                    # 生成参数
                    temperature = gr.Slider(
                        minimum=0.0,
                        maximum=2.0,
                        value=0.7,
                        step=0.1,
                        label="生成温度",
                        info="较高值更有创造性"
                    )

                    gr.Markdown("---")

                    # 操作按钮
                    clear_btn = gr.Button(
                        "🗑️ 清空对话",
                        variant="secondary"
                    )

                    # 状态显示
                    status_box = gr.Textbox(
                        label="状态",
                        value="就绪",
                        interactive=False,
                        lines=2
                    )

            # 事件绑定
            # 用户输入事件
            user_input.submit(
                fn=self.user_input_handler,
                inputs=[user_input, chatbot],
                outputs=[user_input, chatbot],
                queue=False
            ).then(
                fn=self.bot_response_handler,
                inputs=[
                    chatbot,
                    session_id_state,
                    model_selector,
                    rag_enabled,
                    rag_top_k,
                    temperature
                ],
                outputs=[chatbot, session_id_state, status_box],
                queue=True
            )

            # 发送按钮事件
            send_btn.click(
                fn=self.user_input_handler,
                inputs=[user_input, chatbot],
                outputs=[user_input, chatbot],
                queue=False
            ).then(
                fn=self.bot_response_handler,
                inputs=[
                    chatbot,
                    session_id_state,
                    model_selector,
                    rag_enabled,
                    rag_top_k,
                    temperature
                ],
                outputs=[chatbot, session_id_state, status_box],
                queue=True
            )

            # 清空对话事件
            clear_btn.click(
                fn=self.clear_history_handler,
                inputs=[session_id_state],
                outputs=[chatbot, session_id_state, status_box],
                queue=False
            )

            # RAG 开关控制参数显示
            rag_enabled.change(
                fn=lambda x: gr.update(visible=x),
                inputs=[rag_enabled],
                outputs=[rag_params],
                queue=False
            )

        return demo

    def user_input_handler(
        self,
        message: str,
        history: List[Tuple[str, str]]
    ) -> Tuple[str, List[Tuple[str, str]]]:
        """
        处理用户输入

        Args:
            message: 用户消息
            history: 对话历史

        Returns:
            (清空的输入框, 更新后的历史)
        """
        if not message or not message.strip():
            return message, history

        # 添加用户消息到历史
        history = history or []
        history.append([message.strip(), None])

        return "", history

    async def bot_response_handler(
        self,
        history: List[Tuple[str, str]],
        session_id: Optional[str],
        model_name: str,
        enable_rag: bool,
        rag_top_k: int,
        temperature: float
    ) -> Tuple[List[Tuple[str, str]], str, str]:
        """
        处理机器人响应（流式）

        Args:
            history: 对话历史
            session_id: 会话 ID
            model_name: 模型名称
            enable_rag: 是否启用 RAG
            rag_top_k: RAG 检索数量
            temperature: 生成温度

        Returns:
            (更新后的历史, 会话ID, 状态信息)
        """
        if not history or history[-1][1] is not None:
            return history, session_id, "无待处理消息"

        user_message = history[-1][0]
        assistant_message = ""
        status = "生成中..."

        try:
            # 流式生成
            async for event in self.api_client.chat_stream(
                message=user_message,
                session_id=session_id,
                model_name=model_name,
                enable_rag=enable_rag,
                rag_top_k=rag_top_k,
                temperature=temperature
            ):
                event_type = event.get("event")
                data = event.get("data", {})

                if event_type == "start":
                    # 更新会话 ID
                    session_id = data.get("session_id", session_id)
                    status = "正在生成..."

                elif event_type == "context":
                    # RAG 检索结果
                    contexts = data.get("contexts", [])
                    status = f"检索到 {len(contexts)} 个相关文档，正在生成..."

                elif event_type == "token":
                    # 追加 token
                    content = data.get("content", "")
                    assistant_message += content
                    history[-1][1] = assistant_message

                    # 实时更新 UI
                    yield history, session_id, status

                elif event_type == "end":
                    # 生成结束
                    model = data.get("model", "unknown")
                    token_count = data.get("token_count", 0)
                    duration_ms = data.get("duration_ms", 0)
                    status = f"✅ 完成 | 模型: {model} | Token: {token_count} | 耗时: {duration_ms}ms"

                elif event_type == "error":
                    # 错误处理
                    error_msg = data.get("message", "未知错误")
                    history[-1][1] = f"❌ 错误: {error_msg}"
                    status = f"错误: {error_msg}"
                    yield history, session_id, status
                    return

        except Exception as e:
            logger.error(f"Bot response error: {e}", exc_info=True)
            history[-1][1] = f"❌ 系统错误: {str(e)}"
            status = f"错误: {str(e)}"

        yield history, session_id, status

    async def clear_history_handler(
        self,
        session_id: Optional[str]
    ) -> Tuple[List, None, str]:
        """
        清空对话历史

        Args:
            session_id: 会话 ID

        Returns:
            (空历史, None会话ID, 状态信息)
        """
        if session_id:
            try:
                success = await self.api_client.clear_history(session_id)
                if success:
                    logger.info(f"History cleared for session {session_id}")
                    return [], None, "✅ 对话已清空"
                else:
                    return [], None, "⚠️  清空失败"
            except Exception as e:
                logger.error(f"Clear history error: {e}")
                return [], None, f"❌ 错误: {str(e)}"
        else:
            return [], None, "✅ 对话已清空"

    @staticmethod
    def _get_custom_css() -> str:
        """自定义 CSS 样式"""
        return """
        /* 全局样式 */
        .gradio-container {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        /* 对话框样式 */
        .message-row {
            margin-bottom: 10px;
        }

        /* 按钮样式 */
        .primary-button {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        }

        /* 状态框样式 */
        .status-box {
            font-size: 0.85em;
            color: #666;
        }
        """


def create_chat_page() -> gr.Blocks:
    """创建对话页面（工厂函数）"""
    page = ChatPage()
    return page.create_ui()
