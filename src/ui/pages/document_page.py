"""
文档管理页面
"""
import gradio as gr
import asyncio
from typing import List, Tuple
import logging

from src.ui.utils.api_client import ChatAPIClient

logger = logging.getLogger(__name__)


def create_document_page() -> gr.Blocks:
    """创建文档管理页面"""

    # API 客户端
    client = ChatAPIClient()

    def format_document_row(doc: dict) -> List:
        """格式化文档为表格行"""
        return [
            doc.get("document_id", ""),
            doc.get("title", ""),
            doc.get("source_type", ""),
            doc.get("chunk_count", 0),
            doc.get("tags", []),
            doc.get("indexed_at", "")
        ]

    async def load_documents_async(
        source_type_filter: str = "全部"
    ) -> Tuple[List[List], str]:
        """加载文档列表"""
        try:
            # 准备筛选参数
            source_type = None if source_type_filter == "全部" else source_type_filter.lower()

            # 调用 API
            response = await client.list_documents(
                source_type=source_type,
                limit=100
            )

            if response and "documents" in response:
                documents = response["documents"]
                rows = [format_document_row(doc) for doc in documents]
                total = response.get("total", len(documents))
                status_msg = f"✓ 加载成功，共 {total} 个文档"
                return rows, status_msg
            else:
                return [], "⚠ 未找到文档"

        except Exception as e:
            logger.error(f"Failed to load documents: {e}", exc_info=True)
            return [], f"✗ 加载失败: {str(e)}"

    def load_documents(source_type_filter: str = "全部") -> Tuple[List[List], str]:
        """同步包装"""
        return asyncio.run(load_documents_async(source_type_filter))

    async def upload_document_async(
        title: str,
        content: str,
        tags_input: str
    ) -> Tuple[List[List], str]:
        """上传文档"""
        try:
            # 验证输入
            if not title or not title.strip():
                return [], "✗ 请输入文档标题"
            if not content or not content.strip():
                return [], "✗ 请输入文档内容"

            # 解析标签
            tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()]

            # 调用 API
            response = await client.upload_document(
                title=title.strip(),
                content=content.strip(),
                source_type="local",
                tags=tags
            )

            if response and "document_id" in response:
                # 重新加载文档列表
                rows, _ = await load_documents_async()
                status_msg = f"✓ 上传成功！文档ID: {response['document_id']}"
                return rows, status_msg
            else:
                return [], "✗ 上传失败"

        except Exception as e:
            logger.error(f"Failed to upload document: {e}", exc_info=True)
            return [], f"✗ 上传失败: {str(e)}"

    def upload_document(title: str, content: str, tags: str) -> Tuple[List[List], str]:
        """同步包装"""
        return asyncio.run(upload_document_async(title, content, tags))

    async def upload_file_async(
        file_obj,
        title: str,
        tags_input: str
    ) -> Tuple[List[List], str]:
        """上传文件"""
        try:
            # 验证文件
            if file_obj is None:
                return [], "✗ 请选择文件"

            # 获取文件路径
            file_path = file_obj.name if hasattr(file_obj, 'name') else str(file_obj)

            # 验证文件类型
            allowed_extensions = ['.pdf', '.docx', '.doc', '.md']
            import os
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext not in allowed_extensions:
                return [], f"✗ 不支持的文件类型: {file_ext}。支持的类型: {', '.join(allowed_extensions)}"

            # 验证文件大小（最大 10MB）
            file_size = os.path.getsize(file_path)
            max_size = 10 * 1024 * 1024
            if file_size > max_size:
                return [], f"✗ 文件过大: {file_size / 1024 / 1024:.1f}MB（最大 10MB）"

            # 调用 API
            response = await client.upload_document_file(
                file_path=file_path,
                title=title.strip() if title and title.strip() else None,
                tags=tags_input if tags_input and tags_input.strip() else None
            )

            if response and "document_id" in response:
                # 重新加载文档列表
                rows, _ = await load_documents_async()
                status_msg = f"✓ 上传成功！\n"
                status_msg += f"- 文档ID: {response['document_id']}\n"
                status_msg += f"- 标题: {response.get('title', 'N/A')}\n"
                status_msg += f"- 分块数: {response.get('chunk_count', 0)}\n"
                status_msg += f"- 索引时间: {response.get('indexed_at', 'N/A')}"
                return rows, status_msg
            else:
                return [], "✗ 上传失败"

        except Exception as e:
            logger.error(f"Failed to upload file: {e}", exc_info=True)
            return [], f"✗ 上传失败: {str(e)}"

    def upload_file(file_obj, title: str, tags: str) -> Tuple[List[List], str]:
        """同步包装"""
        return asyncio.run(upload_file_async(file_obj, title, tags))

    async def delete_document_async(
        selected_rows: List[int],
        all_rows: List[List]
    ) -> Tuple[List[List], str]:
        """删除选中的文档"""
        try:
            if not selected_rows:
                return all_rows, "⚠ 请先选择要删除的文档"

            deleted_count = 0
            errors = []

            for row_idx in selected_rows:
                if 0 <= row_idx < len(all_rows):
                    document_id = all_rows[row_idx][0]  # 第一列是 document_id

                    try:
                        response = await client.delete_document(document_id)
                        if response:
                            deleted_count += 1
                    except Exception as e:
                        errors.append(f"{document_id}: {str(e)}")

            # 重新加载文档列表
            rows, _ = await load_documents_async()

            if errors:
                status_msg = f"部分删除失败: {'; '.join(errors)}"
            else:
                status_msg = f"✓ 成功删除 {deleted_count} 个文档"

            return rows, status_msg

        except Exception as e:
            logger.error(f"Failed to delete documents: {e}", exc_info=True)
            return all_rows, f"✗ 删除失败: {str(e)}"

    def delete_document(selected_rows, all_rows) -> Tuple[List[List], str]:
        """同步包装"""
        return asyncio.run(delete_document_async(selected_rows, all_rows))

    async def get_stats_async() -> str:
        """获取统计信息"""
        try:
            response = await client.get_document_stats()

            if response:
                total_docs = response.get("total_documents", 0)
                total_chunks = response.get("total_chunks", 0)
                by_source = response.get("by_source_type", {})
                by_tags = response.get("by_tags", {})

                stats_text = f"**文档统计**\n\n"
                stats_text += f"- 总文档数: {total_docs}\n"
                stats_text += f"- 总分块数: {total_chunks}\n\n"

                if by_source:
                    stats_text += f"**按来源类型**\n"
                    for source, count in sorted(by_source.items()):
                        stats_text += f"- {source}: {count}\n"
                    stats_text += "\n"

                if by_tags:
                    stats_text += f"**按标签**\n"
                    top_tags = sorted(by_tags.items(), key=lambda x: x[1], reverse=True)[:10]
                    for tag, count in top_tags:
                        stats_text += f"- {tag}: {count}\n"

                return stats_text
            else:
                return "⚠ 无法获取统计信息"

        except Exception as e:
            logger.error(f"Failed to get stats: {e}", exc_info=True)
            return f"✗ 获取统计失败: {str(e)}"

    def get_stats() -> str:
        """同步包装"""
        return asyncio.run(get_stats_async())

    # 创建页面布局
    with gr.Blocks(title="文档管理") as demo:
        gr.Markdown("# 📚 文档管理")

        with gr.Row():
            # 左侧：文档列表
            with gr.Column(scale=3):
                gr.Markdown("## 文档列表")

                with gr.Row():
                    source_filter = gr.Dropdown(
                        choices=["全部", "Local", "Jira", "Confluence"],
                        value="全部",
                        label="来源类型筛选"
                    )
                    refresh_btn = gr.Button("🔄 刷新", size="sm")

                # 文档表格
                document_table = gr.Dataframe(
                    headers=["ID", "标题", "来源", "分块数", "标签", "索引时间"],
                    datatype=["str", "str", "str", "number", "str", "str"],
                    column_count=(6, "fixed"),
                    value=[],
                    label="",
                    interactive=False,
                    wrap=True
                )

                with gr.Row():
                    delete_btn = gr.Button("🗑️ 删除选中", variant="stop")
                    status_text = gr.Textbox(
                        label="操作状态",
                        value="",
                        interactive=False,
                        lines=2
                    )

            # 右侧：上传和统计
            with gr.Column(scale=1):
                gr.Markdown("## 上传文档")

                with gr.Tabs():
                    # Tab 1: 文本上传
                    with gr.Tab("📝 文本上传"):
                        upload_title = gr.Textbox(
                            label="标题",
                            placeholder="输入文档标题...",
                            lines=1
                        )
                        upload_content = gr.Textbox(
                            label="内容",
                            placeholder="粘贴文档内容...",
                            lines=10
                        )
                        upload_tags = gr.Textbox(
                            label="标签（逗号分隔）",
                            placeholder="如: python, tutorial, api",
                            lines=1
                        )
                        upload_btn = gr.Button("📤 上传", variant="primary")

                    # Tab 2: 文件上传
                    with gr.Tab("📤 文件上传"):
                        file_input = gr.File(
                            label="选择文件",
                            file_types=[".pdf", ".docx", ".doc", ".md"],
                            file_count="single"
                        )
                        file_title = gr.Textbox(
                            label="文档标题（可选）",
                            placeholder="留空则自动从文件提取...",
                            lines=1
                        )
                        file_tags = gr.Textbox(
                            label="标签（逗号分隔）",
                            placeholder="如: 技术文档, API, 用户指南",
                            lines=1
                        )
                        gr.Markdown(
                            """
                            **支持的文件格式**:
                            - PDF (.pdf)
                            - Word (.docx, .doc)
                            - Markdown (.md)

                            **文件大小限制**: 最大 10MB
                            """
                        )
                        upload_file_btn = gr.Button("📤 上传文件", variant="primary")

                gr.Markdown("---")
                gr.Markdown("## 统计信息")
                stats_display = gr.Markdown(value="点击\"刷新统计\"查看")
                stats_btn = gr.Button("🔄 刷新统计", size="sm")

        # 事件绑定
        # 页面加载时自动刷新
        demo.load(
            fn=load_documents,
            inputs=[source_filter],
            outputs=[document_table, status_text]
        )

        # 刷新按钮
        refresh_btn.click(
            fn=load_documents,
            inputs=[source_filter],
            outputs=[document_table, status_text]
        )

        # 来源类型筛选变化
        source_filter.change(
            fn=load_documents,
            inputs=[source_filter],
            outputs=[document_table, status_text]
        )

        # 上传按钮（文本）
        upload_btn.click(
            fn=upload_document,
            inputs=[upload_title, upload_content, upload_tags],
            outputs=[document_table, status_text]
        ).then(
            fn=lambda: ("", "", ""),  # 清空上传表单
            outputs=[upload_title, upload_content, upload_tags]
        )

        # 上传按钮（文件）
        upload_file_btn.click(
            fn=upload_file,
            inputs=[file_input, file_title, file_tags],
            outputs=[document_table, status_text]
        ).then(
            fn=lambda: (None, "", ""),  # 清空文件上传表单
            outputs=[file_input, file_title, file_tags]
        )

        # 删除按钮（注意：Gradio Dataframe 选择功能有限，暂时使用简化实现）
        # 删除功能在 Gradio 中不太好实现行选择，这里提供一个简化版本
        # 用户需要手动输入要删除的文档ID

        # 统计按钮
        stats_btn.click(
            fn=get_stats,
            outputs=[stats_display]
        )

    return demo


if __name__ == "__main__":
    # 测试页面
    demo = create_document_page()
    demo.queue()
    demo.launch(server_name="0.0.0.0", server_port=7862, share=False)
