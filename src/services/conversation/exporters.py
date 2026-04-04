"""
对话导出器
Story 5.1 Phase 2: 对话导出功能
"""

import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT

from .models import ExportFormat, MessageResponse, ConversationDetail

logger = logging.getLogger(__name__)


class ConversationExporter:
    """
    对话导出器

    支持多种格式：
    1. Markdown - 适合文档编辑和分享
    2. JSON - 适合数据交换和备份
    3. PDF - 适合打印和存档
    """

    def __init__(self):
        """初始化导出器"""
        logger.info("ConversationExporter initialized")

    def export(
        self,
        conversation: ConversationDetail,
        format: ExportFormat,
        include_metadata: bool = True,
        include_contexts: bool = False
    ) -> bytes:
        """
        导出对话

        Args:
            conversation: 对话详情
            format: 导出格式
            include_metadata: 是否包含元数据
            include_contexts: 是否包含RAG上下文

        Returns:
            导出的字节内容
        """
        if format == ExportFormat.MARKDOWN:
            content = self._export_markdown(
                conversation,
                include_metadata,
                include_contexts
            )
            return content.encode('utf-8')
        elif format == ExportFormat.JSON:
            content = self._export_json(
                conversation,
                include_metadata,
                include_contexts
            )
            return content.encode('utf-8')
        elif format == ExportFormat.PDF:
            return self._export_pdf(
                conversation,
                include_metadata,
                include_contexts
            )
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def _export_markdown(
        self,
        conversation: ConversationDetail,
        include_metadata: bool,
        include_contexts: bool
    ) -> str:
        """
        导出为 Markdown 格式

        Args:
            conversation: 对话详情
            include_metadata: 是否包含元数据
            include_contexts: 是否包含上下文

        Returns:
            Markdown 文本
        """
        lines = []

        # 标题
        lines.append(f"# {conversation.title}\n")

        # 元数据
        if include_metadata:
            lines.append("## 对话信息\n")
            lines.append(f"- **对话 ID**: `{conversation.id}`")
            lines.append(f"- **创建时间**: {conversation.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"- **更新时间**: {conversation.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"- **消息数量**: {conversation.message_count}")

            if conversation.metadata:
                lines.append(f"- **元数据**: {json.dumps(conversation.metadata, ensure_ascii=False, indent=2)}")

            lines.append("")

        # 消息列表
        lines.append("## 对话内容\n")

        for i, message in enumerate(conversation.messages, 1):
            # 消息头部
            role_emoji = "🧑" if message.role == "user" else "🤖" if message.role == "assistant" else "⚙️"
            role_name = {"user": "用户", "assistant": "助手", "system": "系统"}.get(message.role, message.role)

            lines.append(f"### {role_emoji} {role_name} - 消息 #{i}\n")

            # 时间戳
            lines.append(f"**时间**: {message.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n")

            # 内容
            lines.append(message.content)
            lines.append("")

            # 引用信息
            if message.citations and include_contexts:
                lines.append("**引用来源**:")
                for j, citation in enumerate(message.citations, 1):
                    title = citation.get('title', '未知')
                    source = citation.get('source', '未知')
                    lines.append(f"{j}. [{title}]({source})")
                lines.append("")

            # 模型信息
            if message.model_name or message.token_count:
                info_parts = []
                if message.model_name:
                    info_parts.append(f"模型: {message.model_name}")
                if message.token_count:
                    info_parts.append(f"Token: {message.token_count}")
                lines.append(f"*{' | '.join(info_parts)}*")
                lines.append("")

            lines.append("---\n")

        # 页脚
        lines.append(f"\n*导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

        return "\n".join(lines)

    def _export_json(
        self,
        conversation: ConversationDetail,
        include_metadata: bool,
        include_contexts: bool
    ) -> str:
        """
        导出为 JSON 格式

        Args:
            conversation: 对话详情
            include_metadata: 是否包含元数据
            include_contexts: 是否包含上下文

        Returns:
            JSON 文本
        """
        # 构建导出数据
        export_data = {
            "conversation": {
                "id": conversation.id,
                "user_id": conversation.user_id,
                "title": conversation.title,
                "message_count": conversation.message_count,
                "created_at": conversation.created_at.isoformat(),
                "updated_at": conversation.updated_at.isoformat(),
            },
            "messages": []
        }

        # 添加元数据
        if include_metadata and conversation.metadata:
            export_data["conversation"]["metadata"] = conversation.metadata

        # 添加消息
        for message in conversation.messages:
            message_data = {
                "id": message.id,
                "role": message.role,
                "content": message.content,
                "created_at": message.created_at.isoformat(),
            }

            # 可选字段
            if message.model_name:
                message_data["model_name"] = message.model_name
            if message.token_count:
                message_data["token_count"] = message.token_count

            # 上下文和引用
            if include_contexts:
                if message.contexts:
                    message_data["contexts"] = message.contexts
                if message.citations:
                    message_data["citations"] = message.citations

            # 元数据
            if include_metadata and message.metadata:
                message_data["metadata"] = message.metadata

            export_data["messages"].append(message_data)

        # 导出信息
        export_data["export_info"] = {
            "format": "json",
            "exported_at": datetime.now().isoformat(),
            "version": "1.0"
        }

        return json.dumps(export_data, ensure_ascii=False, indent=2)

    def _export_pdf(
        self,
        conversation: ConversationDetail,
        include_metadata: bool,
        include_contexts: bool
    ) -> bytes:
        """
        导出为 PDF 格式

        Args:
            conversation: 对话详情
            include_metadata: 是否包含元数据
            include_contexts: 是否包含上下文

        Returns:
            PDF 字节内容
        """
        buffer = BytesIO()

        # 创建 PDF 文档
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )

        # 样式
        styles = getSampleStyleSheet()

        # 标题样式
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            spaceAfter=30,
            alignment=TA_LEFT
        )

        # 普通文本样式
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            alignment=TA_LEFT
        )

        # 构建文档内容
        story = []

        # 标题
        story.append(Paragraph(self._escape_xml(conversation.title), title_style))
        story.append(Spacer(1, 0.2 * inch))

        # 元数据
        if include_metadata:
            info_text = f"""
            <b>对话 ID:</b> {conversation.id}<br/>
            <b>创建时间:</b> {conversation.created_at.strftime('%Y-%m-%d %H:%M:%S')}<br/>
            <b>更新时间:</b> {conversation.updated_at.strftime('%Y-%m-%d %H:%M:%S')}<br/>
            <b>消息数量:</b> {conversation.message_count}
            """
            story.append(Paragraph(info_text, normal_style))
            story.append(Spacer(1, 0.3 * inch))

        # 消息列表
        for i, message in enumerate(conversation.messages, 1):
            # 角色标识
            role_name = {"user": "用户", "assistant": "助手", "system": "系统"}.get(
                message.role,
                message.role
            )

            # 消息头部
            header_text = f"<b>{role_name} - 消息 #{i}</b><br/>"
            header_text += f"<i>{message.created_at.strftime('%Y-%m-%d %H:%M:%S')}</i>"
            story.append(Paragraph(header_text, normal_style))
            story.append(Spacer(1, 0.1 * inch))

            # 消息内容
            content = self._escape_xml(message.content)
            story.append(Paragraph(content, normal_style))
            story.append(Spacer(1, 0.2 * inch))

            # 模型信息
            if message.model_name or message.token_count:
                info_parts = []
                if message.model_name:
                    info_parts.append(f"模型: {message.model_name}")
                if message.token_count:
                    info_parts.append(f"Token: {message.token_count}")

                info_text = f"<i>{' | '.join(info_parts)}</i>"
                story.append(Paragraph(info_text, normal_style))
                story.append(Spacer(1, 0.2 * inch))

            # 分隔线
            if i < len(conversation.messages):
                story.append(Spacer(1, 0.2 * inch))

        # 页脚
        footer_text = f"<i>导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"
        story.append(Spacer(1, 0.3 * inch))
        story.append(Paragraph(footer_text, normal_style))

        # 生成 PDF
        doc.build(story)

        # 获取 PDF 内容
        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes

    def _escape_xml(self, text: str) -> str:
        """
        转义 XML 特殊字符

        Args:
            text: 原始文本

        Returns:
            转义后的文本
        """
        if not text:
            return ""

        # 基本 XML 转义
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        text = text.replace('"', "&quot;")
        text = text.replace("'", "&apos;")

        return text
