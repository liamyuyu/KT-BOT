"""
对话管理服务
Story 5.1 Phase 2: 对话管理服务层
"""

import logging
from typing import Optional, List, Tuple
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.storage.database.repository import ConversationRepository
from src.storage.database.models import Conversation, Message

from .models import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    ConversationDetail,
    ConversationListResponse,
    ConversationStats,
    MessageCreate,
    MessageResponse,
    ExportFormat,
    TitleGenerationConfig
)
from .title_generator import TitleGenerator
from .exporters import ConversationExporter

logger = logging.getLogger(__name__)


class ConversationManager:
    """
    对话管理服务

    提供对话的业务逻辑，包括：
    - 对话 CRUD 操作
    - 消息管理
    - 标题自动生成
    - 对话导出
    - 统计信息
    """

    def __init__(
        self,
        session: AsyncSession,
        title_generator: Optional[TitleGenerator] = None,
        exporter: Optional[ConversationExporter] = None
    ):
        """
        初始化对话管理器

        Args:
            session: 数据库会话
            title_generator: 标题生成器（可选）
            exporter: 导出器（可选）
        """
        self.repo = ConversationRepository(session)
        self.title_generator = title_generator or TitleGenerator()
        self.exporter = exporter or ConversationExporter()
        logger.info("ConversationManager initialized")

    async def create_conversation(
        self,
        user_id: str,
        request: ConversationCreate,
        auto_generate_title: bool = False,
        first_message: Optional[str] = None
    ) -> ConversationResponse:
        """
        创建新对话

        Args:
            user_id: 用户 ID
            request: 创建请求
            auto_generate_title: 是否自动生成标题
            first_message: 首条消息（用于生成标题）

        Returns:
            ConversationResponse: 创建的对话
        """
        # 如果需要自动生成标题
        title = request.title
        if auto_generate_title and first_message:
            try:
                title = self.title_generator.generate_title(first_message)
                logger.info(f"Auto-generated title: {title}")
            except Exception as e:
                logger.error(f"Failed to generate title: {e}", exc_info=True)
                # 保持原标题

        # 创建对话
        conversation = await self.repo.create_conversation(
            user_id=user_id,
            title=title,
            metadata=request.metadata
        )

        logger.info(f"Conversation created: id={conversation.id}, user_id={user_id}")

        return self._to_conversation_response(conversation)

    async def get_conversation(
        self,
        conversation_id: str,
        include_messages: bool = True
    ) -> Optional[ConversationDetail]:
        """
        获取对话详情

        Args:
            conversation_id: 对话 ID
            include_messages: 是否包含消息列表

        Returns:
            ConversationDetail 或 None
        """
        conversation = await self.repo.get_conversation_by_id(
            conversation_id,
            include_messages=include_messages
        )

        if not conversation:
            logger.warning(f"Conversation not found: id={conversation_id}")
            return None

        return self._to_conversation_detail(conversation)

    async def list_conversations(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        include_deleted: bool = False
    ) -> ConversationListResponse:
        """
        获取对话列表

        Args:
            user_id: 用户 ID
            page: 页码（从1开始）
            page_size: 每页数量
            include_deleted: 是否包含已删除

        Returns:
            ConversationListResponse: 对话列表
        """
        offset = (page - 1) * page_size

        conversations, total = await self.repo.list_conversations(
            user_id=user_id,
            offset=offset,
            limit=page_size,
            include_deleted=include_deleted
        )

        logger.info(
            f"Listed conversations: user_id={user_id}, page={page}, "
            f"total={total}, count={len(conversations)}"
        )

        return ConversationListResponse(
            conversations=[
                self._to_conversation_response(conv)
                for conv in conversations
            ],
            total=total,
            page=page,
            page_size=page_size
        )

    async def search_conversations(
        self,
        user_id: str,
        keyword: str,
        page: int = 1,
        page_size: int = 20
    ) -> ConversationListResponse:
        """
        搜索对话

        Args:
            user_id: 用户 ID
            keyword: 搜索关键词
            page: 页码
            page_size: 每页数量

        Returns:
            ConversationListResponse: 搜索结果
        """
        offset = (page - 1) * page_size

        conversations, total = await self.repo.search_conversations(
            user_id=user_id,
            keyword=keyword,
            offset=offset,
            limit=page_size
        )

        logger.info(
            f"Searched conversations: user_id={user_id}, keyword='{keyword}', "
            f"total={total}"
        )

        return ConversationListResponse(
            conversations=[
                self._to_conversation_response(conv)
                for conv in conversations
            ],
            total=total,
            page=page,
            page_size=page_size
        )

    async def update_conversation(
        self,
        conversation_id: str,
        request: ConversationUpdate
    ) -> Optional[ConversationResponse]:
        """
        更新对话

        Args:
            conversation_id: 对话 ID
            request: 更新请求

        Returns:
            ConversationResponse 或 None
        """
        conversation = await self.repo.update_conversation(
            conversation_id=conversation_id,
            title=request.title,
            metadata=request.metadata
        )

        if not conversation:
            logger.warning(f"Conversation not found for update: id={conversation_id}")
            return None

        logger.info(f"Conversation updated: id={conversation_id}")

        return self._to_conversation_response(conversation)

    async def delete_conversation(
        self,
        conversation_id: str,
        soft_delete: bool = True
    ) -> bool:
        """
        删除对话

        Args:
            conversation_id: 对话 ID
            soft_delete: 是否软删除

        Returns:
            是否删除成功
        """
        success = await self.repo.delete_conversation(
            conversation_id,
            soft_delete=soft_delete
        )

        if success:
            logger.info(
                f"Conversation deleted: id={conversation_id}, "
                f"soft_delete={soft_delete}"
            )
        else:
            logger.warning(f"Failed to delete conversation: id={conversation_id}")

        return success

    async def delete_conversations_batch(
        self,
        conversation_ids: List[str],
        soft_delete: bool = True
    ) -> int:
        """
        批量删除对话

        Args:
            conversation_ids: 对话 ID 列表
            soft_delete: 是否软删除

        Returns:
            删除的数量
        """
        count = await self.repo.delete_conversations_batch(
            conversation_ids,
            soft_delete=soft_delete
        )

        logger.info(f"Batch deleted {count} conversations")

        return count

    async def add_message(
        self,
        conversation_id: str,
        request: MessageCreate
    ) -> Optional[MessageResponse]:
        """
        添加消息到对话

        Args:
            conversation_id: 对话 ID
            request: 消息创建请求

        Returns:
            MessageResponse 或 None
        """
        message = await self.repo.add_message(
            conversation_id=conversation_id,
            role=request.role.value,
            content=request.content,
            contexts=request.contexts,
            citations=request.citations,
            model_name=request.model_name,
            token_count=request.token_count,
            metadata=request.metadata
        )

        if not message:
            logger.warning(
                f"Failed to add message: conversation_id={conversation_id}"
            )
            return None

        logger.info(
            f"Message added: id={message.id}, conversation_id={conversation_id}, "
            f"role={request.role}"
        )

        return self._to_message_response(message)

    async def get_messages(
        self,
        conversation_id: str,
        page: int = 1,
        page_size: Optional[int] = None
    ) -> List[MessageResponse]:
        """
        获取对话的消息列表

        Args:
            conversation_id: 对话 ID
            page: 页码（从1开始）
            page_size: 每页数量（None 表示不限制）

        Returns:
            消息列表
        """
        offset = (page - 1) * page_size if page_size else 0

        messages = await self.repo.get_messages_by_conversation(
            conversation_id=conversation_id,
            offset=offset,
            limit=page_size
        )

        logger.info(
            f"Retrieved messages: conversation_id={conversation_id}, "
            f"count={len(messages)}"
        )

        return [self._to_message_response(msg) for msg in messages]

    async def delete_message(self, message_id: str) -> bool:
        """
        删除消息

        Args:
            message_id: 消息 ID

        Returns:
            是否删除成功
        """
        success = await self.repo.delete_message(message_id)

        if success:
            logger.info(f"Message deleted: id={message_id}")
        else:
            logger.warning(f"Failed to delete message: id={message_id}")

        return success

    async def get_stats(self, user_id: str) -> ConversationStats:
        """
        获取对话统计信息

        Args:
            user_id: 用户 ID

        Returns:
            ConversationStats: 统计信息
        """
        stats_dict = await self.repo.get_conversation_stats(user_id)

        logger.info(f"Retrieved stats for user: {user_id}, total={stats_dict['total']}")

        return ConversationStats(**stats_dict)

    async def export_conversation(
        self,
        conversation_id: str,
        format: ExportFormat,
        include_metadata: bool = True,
        include_contexts: bool = False
    ) -> Optional[bytes]:
        """
        导出对话

        Args:
            conversation_id: 对话 ID
            format: 导出格式
            include_metadata: 是否包含元数据
            include_contexts: 是否包含上下文

        Returns:
            导出的字节内容，如果对话不存在则返回 None
        """
        # 获取对话详情
        conversation = await self.get_conversation(
            conversation_id,
            include_messages=True
        )

        if not conversation:
            logger.warning(f"Conversation not found for export: id={conversation_id}")
            return None

        # 导出
        try:
            content = self.exporter.export(
                conversation=conversation,
                format=format,
                include_metadata=include_metadata,
                include_contexts=include_contexts
            )

            logger.info(
                f"Conversation exported: id={conversation_id}, format={format.value}"
            )

            return content

        except Exception as e:
            logger.error(f"Failed to export conversation: {e}", exc_info=True)
            return None

    def _to_conversation_response(
        self,
        conversation: Conversation
    ) -> ConversationResponse:
        """将 ORM 模型转换为响应模型"""
        return ConversationResponse(
            id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title,
            message_count=conversation.message_count,
            metadata=conversation.metadata_json,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at
        )

    def _to_conversation_detail(
        self,
        conversation: Conversation
    ) -> ConversationDetail:
        """将 ORM 模型转换为详情模型"""
        return ConversationDetail(
            id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title,
            message_count=conversation.message_count,
            metadata=conversation.metadata_json,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            messages=[
                self._to_message_response(msg)
                for msg in conversation.messages
            ]
        )

    def _to_message_response(self, message: Message) -> MessageResponse:
        """将 ORM 模型转换为响应模型"""
        return MessageResponse(
            id=message.id,
            conversation_id=message.conversation_id,
            role=message.role,
            content=message.content,
            contexts=message.contexts,
            citations=message.citations,
            model_name=message.model_name,
            token_count=message.token_count,
            metadata=message.metadata_json,
            created_at=message.created_at
        )
