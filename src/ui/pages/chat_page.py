"""
主对话页面 - Gradio UI
"""
import logging
import gradio as gr
from typing import List, Tuple, Optional
import asyncio

from ..utils.api_client import get_api_client
from ..components.citation import create_citation_badge, highlight_content

logger = logging.getLogger(__name__)


class ChatPage:
    """对话页面"""

    def __init__(self):
        self.api_client = get_api_client()
        logger.info("ChatPage initialized")

    def create_ui(self) -> gr.Blocks:
        """创建 Gradio UI"""

        with gr.Blocks(
            title="KT-BOT - 知识库助手"
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
                # 左侧：配置面板
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
                            info="最终返回的文档数量"
                        )

                        # 重排序开关
                        enable_reranking = gr.Checkbox(
                            value=True,
                            label="启用重排序 (Reranker)",
                            info="使用 Cross-Encoder 模型重新评分，提升相关性"
                        )

                        # 重排序参数（仅在启用时显示）
                        with gr.Group(visible=True) as rerank_params:
                            rerank_top_k = gr.Slider(
                                minimum=5,
                                maximum=50,
                                value=10,
                                step=5,
                                label="重排序候选数量",
                                info="先召回更多候选，重排序后返回 Top-K"
                            )

                        # 检索策略选择
                        retrieval_method = gr.Radio(
                            choices=["hybrid", "vector", "bm25"],
                            value="hybrid",
                            label="检索策略",
                            info="hybrid: 混合检索 | vector: 向量检索 | bm25: 全文检索"
                        )

                        # 混合检索参数（仅在 hybrid 模式下显示）
                        with gr.Group(visible=True) as hybrid_params:
                            fusion_method = gr.Dropdown(
                                choices=["rrf", "weighted", "linear"],
                                value="rrf",
                                label="融合方法",
                                info="rrf: Reciprocal Rank Fusion | weighted: 加权平均 | linear: 线性组合"
                            )

                            vector_weight = gr.Slider(
                                minimum=0.0,
                                maximum=1.0,
                                value=0.5,
                                step=0.1,
                                label="向量检索权重",
                                info="0.0-1.0，仅 weighted/linear 模式使用"
                            )

                            bm25_weight = gr.Slider(
                                minimum=0.0,
                                maximum=1.0,
                                value=0.5,
                                step=0.1,
                                label="BM25 检索权重",
                                info="0.0-1.0，仅 weighted/linear 模式使用"
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

                # 右侧：对话区域
                with gr.Column(scale=3):
                    # 对话框
                    chatbot = gr.Chatbot(
                        label="对话历史",
                        height=500,
                        show_label=False
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
                    temperature,
                    retrieval_method,
                    fusion_method,
                    vector_weight,
                    bm25_weight,
                    enable_reranking,
                    rerank_top_k
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
                    temperature,
                    retrieval_method,
                    fusion_method,
                    vector_weight,
                    bm25_weight,
                    enable_reranking,
                    rerank_top_k
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

            # 检索策略控制混合参数显示
            retrieval_method.change(
                fn=lambda method: gr.update(visible=(method == "hybrid")),
                inputs=[retrieval_method],
                outputs=[hybrid_params],
                queue=False
            )

            # 重排序开关控制参数显示
            enable_reranking.change(
                fn=lambda x: gr.update(visible=x),
                inputs=[enable_reranking],
                outputs=[rerank_params],
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
        temperature: float,
        retrieval_method: str = "hybrid",
        fusion_method: str = "rrf",
        vector_weight: float = 0.5,
        bm25_weight: float = 0.5,
        enable_reranking: bool = True,
        rerank_top_k: int = 10
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
            retrieval_method: 检索方法（vector/bm25/hybrid）
            fusion_method: 融合方法（rrf/weighted/linear）
            vector_weight: 向量检索权重
            bm25_weight: BM25 检索权重
            enable_reranking: 是否启用重排序
            rerank_top_k: 重排序候选数量

        Returns:
            (更新后的历史, 会话ID, 状态信息)
        """
        if not history or history[-1][1] is not None:
            yield history, session_id, "无待处理消息"
            return

        user_message = history[-1][0]
        assistant_message = ""
        rag_contexts = []
        status = "生成中..."

        try:
            # 流式生成
            async for event in self.api_client.chat_stream(
                message=user_message,
                session_id=session_id,
                model_name=model_name,
                enable_rag=enable_rag,
                rag_top_k=rag_top_k,
                temperature=temperature,
                retrieval_method=retrieval_method,
                fusion_method=fusion_method,
                vector_weight=vector_weight,
                bm25_weight=bm25_weight,
                enable_reranking=enable_reranking,
                rerank_top_k=rerank_top_k
            ):
                event_type = event.get("event")
                data = event.get("data", {})

                if event_type == "start":
                    # 更新会话 ID
                    session_id = data.get("session_id", session_id)
                    status = "正在生成..."

                elif event_type == "context":
                    # RAG 检索结果 - 保存以便后续格式化
                    rag_contexts = data.get("contexts", [])
                    status = f"检索到 {len(rag_contexts)} 个相关文档，正在生成..."

                elif event_type == "token":
                    # 追加 token
                    content = data.get("content", "")
                    assistant_message += content

                    # 构建带格式的响应（实时更新）
                    formatted_response = self._format_response(
                        assistant_message,
                        rag_contexts if rag_contexts else None
                    )
                    history[-1][1] = formatted_response

                    # 实时更新 UI
                    yield history, session_id, status

                elif event_type == "end":
                    # 生成结束 - 添加最终格式化
                    formatted_response = self._format_response(
                        assistant_message,
                        rag_contexts if rag_contexts else None
                    )
                    history[-1][1] = formatted_response

                    model = data.get("model", "unknown")
                    token_count = data.get("token_count", 0)
                    duration_ms = data.get("duration_ms", 0)
                    status = f"✅ 完成 | 模型: {model} | Token: {token_count} | 耗时: {duration_ms}ms"

                elif event_type == "error":
                    # 错误处理
                    error_msg = data.get("message", "未知错误")
                    history[-1][1] = f"❌ **错误**: {error_msg}"
                    status = f"错误: {error_msg}"
                    yield history, session_id, status
                    return

        except Exception as e:
            logger.error(f"Bot response error: {e}", exc_info=True)
            history[-1][1] = f"❌ **系统错误**: {str(e)}"
            status = f"错误: {str(e)}"

        yield history, session_id, status

    @staticmethod
    def _format_response(content: str, contexts: Optional[List[dict]] = None) -> str:
        """
        格式化响应内容，添加 RAG 来源引用（支持引用溯源）

        Args:
            content: 原始响应内容
            contexts: RAG 检索结果（包含 citation 信息）

        Returns:
            格式化后的 Markdown/HTML 内容
        """
        formatted = content

        # 如果有 RAG 来源，添加引用部分
        if contexts and len(contexts) > 0:
            formatted += "\n\n---\n\n"
            formatted += "### 📚 参考来源\n\n"

            for i, ctx in enumerate(contexts, 1):
                # 获取引用信息（新增）
                citation = ctx.get("citation", {})

                if citation:
                    # 使用引用溯源组件显示
                    badge_html = create_citation_badge(citation)
                    formatted += f"{badge_html}\n\n"

                    # 显示高亮内容预览
                    ctx_content = ctx.get("content", "")
                    highlights = citation.get("highlights", [])

                    # 截取前 300 字符并高亮
                    preview = ctx_content[:300]
                    if len(ctx_content) > 300:
                        preview += "..."

                    highlighted = highlight_content(preview, highlights)
                    formatted += f"<blockquote style='border-left: 3px solid #0052CC; padding-left: 12px; color: #42526E;'>{highlighted}</blockquote>\n\n"
                else:
                    # 回退到旧格式（向后兼容）
                    source = ctx.get("source", {})
                    score = ctx.get("score", 0)

                    # 提取来源信息
                    source_type = source.get("source_type", "unknown")
                    issue_key = source.get("issue_key", "")
                    title = source.get("title", "未知文档")

                    # 构建来源显示
                    if source_type == "jira_issue" and issue_key:
                        source_text = f"**[{i}] JIRA Issue: {issue_key}** - {title}"
                    elif source_type == "confluence_page":
                        source_text = f"**[{i}] Confluence Page** - {title}"
                    else:
                        source_text = f"**[{i}] 文档** - {title}"

                    # 添加相似度分数
                    score_percent = int(score * 100)
                    formatted += f"{source_text} (相关度: {score_percent}%)\n"

            formatted += "\n> 💡 回答基于以上文档内容生成"

        return formatted

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

        /* 对话框样式优化 */
        .message-row {
            margin-bottom: 12px;
            border-radius: 8px;
        }

        /* 用户消息样式 */
        .message.user {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px;
            border-radius: 12px;
        }

        /* 助手消息样式 */
        .message.bot {
            background: #f7f7f8;
            padding: 12px;
            border-radius: 12px;
            border-left: 4px solid #667eea;
        }

        /* Markdown 代码块样式 */
        .message code {
            background: #282c34;
            color: #abb2bf;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Monaco', 'Consolas', monospace;
            font-size: 0.9em;
        }

        .message pre {
            background: #282c34;
            color: #abb2bf;
            padding: 12px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 8px 0;
        }

        .message pre code {
            background: none;
            padding: 0;
        }

        /* 引用样式 */
        .message blockquote {
            border-left: 4px solid #667eea;
            padding-left: 12px;
            margin: 8px 0;
            color: #666;
            font-style: italic;
        }

        /* 链接样式 */
        .message a {
            color: #667eea;
            text-decoration: none;
            border-bottom: 1px solid #667eea;
        }

        .message a:hover {
            color: #764ba2;
            border-bottom-color: #764ba2;
        }

        /* 按钮样式 */
        .primary-button {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            border: none;
            transition: all 0.3s ease;
        }

        .primary-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }

        /* 状态框样式 */
        .status-box {
            font-size: 0.85em;
            color: #666;
            background: #f0f0f0;
            padding: 8px;
            border-radius: 6px;
        }

        /* 参考来源样式 */
        .message hr {
            border: none;
            border-top: 2px solid #e0e0e0;
            margin: 16px 0;
        }

        /* 输入框样式 */
        textarea {
            border-radius: 8px !important;
            border: 2px solid #e0e0e0 !important;
        }

        textarea:focus {
            border-color: #667eea !important;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
        }

        /* 滑块样式 */
        input[type="range"] {
            accent-color: #667eea;
        }

        /* 复选框样式 */
        input[type="checkbox"] {
            accent-color: #667eea;
        }
        """


def create_chat_page() -> gr.Blocks:
    """创建对话页面（工厂函数）"""
    page = ChatPage()
    return page.create_ui()
