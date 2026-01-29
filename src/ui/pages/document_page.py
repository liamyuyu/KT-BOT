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

    # ========== 批量上传功能 (Story 5.2) ==========

    def handle_file_selection(files) -> List[List]:
        """处理文件选择，显示文件列表"""
        if not files:
            return []

        file_list = []
        for file_obj in files:
            if file_obj is None:
                continue

            file_path = file_obj.name if hasattr(file_obj, 'name') else str(file_obj)
            file_name = file_path.split('/')[-1]

            # 获取文件大小
            try:
                import os
                file_size = os.path.getsize(file_path)
                size_str = f"{file_size / 1024 / 1024:.2f} MB" if file_size > 1024*1024 else f"{file_size / 1024:.2f} KB"
            except:
                size_str = "未知"

            file_list.append([file_name, size_str, "待上传"])

        return file_list

    async def batch_upload_async(
        files,
        tags: str
    ) -> Tuple[str, List[List]]:
        """批量上传文件"""
        try:
            if not files:
                return "⚠ 请先选择文件", []

            # 验证文件数量
            if len(files) > 10:
                return f"✗ 最多支持 10 个文件，当前选择了 {len(files)} 个", []

            # 准备文件路径列表
            file_paths = []
            for file_obj in files:
                if file_obj is None:
                    continue
                file_path = file_obj.name if hasattr(file_obj, 'name') else str(file_obj)
                file_paths.append(file_path)

            if not file_paths:
                return "✗ 没有有效的文件", []

            # 调用批量上传 API
            response = await client.batch_upload_documents(
                file_paths=file_paths,
                user_id="default",
                tags=tags if tags and tags.strip() else None
            )

            if not response:
                return "✗ 批量上传失败", []

            # 显示结果
            progress_text = f"📦 批次 ID: {response['batch_id']}\n\n"
            progress_text += f"✓ 总文件数: {response['total_files']}\n"
            progress_text += f"✓ 接受文件: {response['accepted_files']}\n"

            if response['rejected_files']:
                progress_text += f"\n⚠ 拒绝文件 ({len(response['rejected_files'])}):\n"
                for rejected in response['rejected_files']:
                    progress_text += f"  - {rejected['file_name']}: {rejected['reason']}\n"

            progress_text += f"\n📋 任务 ID 列表:\n"
            for task_id in response['task_ids']:
                progress_text += f"  - {task_id}\n"

            progress_text += "\n⏳ 文件正在后台处理中..."
            progress_text += "\n💡 提示: 切换到\"上传历史\"标签查看详细进度"

            # 刷新上传历史
            history_data = await get_upload_history_async()

            return progress_text, history_data

        except Exception as e:
            logger.error(f"Batch upload failed: {e}", exc_info=True)
            return f"✗ 批量上传失败: {str(e)}", []

    def batch_upload(files, tags: str) -> Tuple[str, List[List]]:
        """同步包装"""
        return asyncio.run(batch_upload_async(files, tags))

    async def get_upload_history_async(
        status_filter: str = "全部"
    ) -> List[List]:
        """获取上传历史"""
        try:
            status = None if status_filter == "全部" else status_filter

            tasks = await client.list_upload_tasks(
                user_id="default",
                status=status,
                limit=50
            )

            if not tasks:
                return []

            # 格式化为表格数据
            history_rows = []
            for task in tasks:
                file_name = task.get('file_name', '')
                status = task.get('status', '')
                progress = task.get('progress_percentage', 0.0)
                doc_id = task.get('document_id', '') or '-'
                error = task.get('error_message', '') or '-'
                created = task.get('created_at', '')[:19] if task.get('created_at') else ''

                history_rows.append([
                    file_name,
                    status,
                    round(progress, 1),
                    doc_id,
                    error[:50] + '...' if len(error) > 50 else error,
                    created
                ])

            return history_rows

        except Exception as e:
            logger.error(f"Get upload history failed: {e}", exc_info=True)
            return []

    def get_upload_history(status_filter: str = "全部") -> List[List]:
        """同步包装"""
        return asyncio.run(get_upload_history_async(status_filter))

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

                    # Tab 2: 文件上传 (单个)
                    with gr.Tab("📤 文件上传"):
                        file_input = gr.File(
                            label="选择文件",
                            file_types=[".pdf", ".docx", ".doc", ".md", ".html", ".htm"],
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
                            - HTML (.html, .htm)

                            **文件大小限制**: 最大 10MB
                            """
                        )
                        upload_file_btn = gr.Button("📤 上传文件", variant="primary")

                    # Tab 3: 批量上传 (新增)
                    with gr.Tab("📦 批量上传"):
                        batch_file_input = gr.File(
                            label="选择多个文件（最多10个）",
                            file_types=[".pdf", ".docx", ".doc", ".md", ".html", ".htm"],
                            file_count="multiple"
                        )

                        # 文件列表预览
                        file_list_display = gr.Dataframe(
                            headers=["文件名", "大小", "状态"],
                            datatype=["str", "str", "str"],
                            label="待上传文件",
                            interactive=False,
                            wrap=True
                        )

                        batch_tags = gr.Textbox(
                            label="标签（逗号分隔，应用于所有文件）",
                            placeholder="如: 技术文档, API",
                            lines=1
                        )

                        with gr.Row():
                            batch_upload_btn = gr.Button("🚀 开始批量上传", variant="primary", size="lg")
                            clear_btn = gr.Button("🗑️ 清空列表", size="sm")

                        # 上传进度显示
                        progress_display = gr.Textbox(
                            label="上传进度",
                            value="",
                            lines=8,
                            interactive=False,
                            max_lines=15
                        )

                        gr.Markdown(
                            """
                            **批量上传说明**:
                            - 最多同时上传 10 个文件
                            - 单个文件最大 50MB
                            - 支持格式: PDF, Word, Markdown, HTML
                            - 文件将自动解析并索引
                            """
                        )

                    # Tab 4: 上传历史 (新增)
                    with gr.Tab("📜 上传历史"):
                        with gr.Row():
                            history_status_filter = gr.Dropdown(
                                choices=["全部", "pending", "validating", "parsing", "indexing", "completed", "failed", "cancelled"],
                                value="全部",
                                label="状态筛选"
                            )
                            history_refresh_btn = gr.Button("🔄 刷新历史", size="sm")

                        history_table = gr.Dataframe(
                            headers=["文件名", "状态", "进度%", "文档ID", "错误信息", "创建时间"],
                            datatype=["str", "str", "number", "str", "str", "str"],
                            label="上传历史记录",
                            interactive=False,
                            wrap=True
                        )

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

        # ========== 批量上传事件绑定 ==========

        # 文件选择变化时更新文件列表预览
        batch_file_input.change(
            fn=handle_file_selection,
            inputs=[batch_file_input],
            outputs=[file_list_display]
        )

        # 清空文件列表
        clear_btn.click(
            fn=lambda: (None, []),
            outputs=[batch_file_input, file_list_display]
        )

        # 批量上传按钮
        batch_upload_btn.click(
            fn=batch_upload,
            inputs=[batch_file_input, batch_tags],
            outputs=[progress_display, history_table]
        ).then(
            fn=lambda: (None, [], ""),  # 清空表单
            outputs=[batch_file_input, file_list_display, batch_tags]
        )

        # 刷新上传历史
        history_refresh_btn.click(
            fn=get_upload_history,
            inputs=[history_status_filter],
            outputs=[history_table]
        )

        # 状态筛选变化
        history_status_filter.change(
            fn=get_upload_history,
            inputs=[history_status_filter],
            outputs=[history_table]
        )

    return demo


if __name__ == "__main__":
    # 测试页面
    demo = create_document_page()
    demo.queue()
    demo.launch(server_name="0.0.0.0", server_port=7862, share=False)
