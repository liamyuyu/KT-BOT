"""
对话历史数据访问层

提供对话和消息的 CRUD 操作。
"""

from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models import Conversation, Message


class ConversationRepository:
    """
    对话历史仓库

    提供对话和消息的数据访问操作，包括：
    - 对话 CRUD
    - 消息 CRUD
    - 对话搜索
    - 统计信息
    """

    def __init__(self, session: AsyncSession):
        """
        初始化仓库

        Args:
            session: 异步数据库会话
        """
        self.session = session

    async def create_conversation(
        self,
        user_id: str,
        title: str,
        metadata: Optional[dict] = None
    ) -> Conversation:
        """
        创建新对话

        Args:
            user_id: 用户 ID
            title: 对话标题
            metadata: 元数据（可选）

        Returns:
            Conversation: 创建的对话对象
        """
        conversation = Conversation(
            id=str(uuid4()),
            user_id=user_id,
            title=title,
            message_count=0,
            metadata_json=metadata,
            is_deleted=False,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        self.session.add(conversation)
        await self.session.commit()
        await self.session.refresh(conversation)

        return conversation

    async def get_conversation_by_id(
        self,
        conversation_id: str,
        include_messages: bool = True
    ) -> Optional[Conversation]:
        """
        根据 ID 获取对话

        Args:
            conversation_id: 对话 ID
            include_messages: 是否包含消息（默认 True）

        Returns:
            Optional[Conversation]: 对话对象，如果不存在则返回 None
        """
        query = select(Conversation).where(
            and_(
                Conversation.id == conversation_id,
                Conversation.is_deleted == False
            )
        )

        if include_messages:
            query = query.options(selectinload(Conversation.messages))

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_conversations(
        self,
        user_id: str,
        offset: int = 0,
        limit: int = 20,
        include_deleted: bool = False
    ) -> tuple[List[Conversation], int]:
        """
        获取对话列表（分页）

        Args:
            user_id: 用户 ID
            offset: 偏移量
            limit: 每页数量
            include_deleted: 是否包含已删除的对话

        Returns:
            tuple[List[Conversation], int]: (对话列表, 总数)
        """
        # 构建查询条件
        conditions = [Conversation.user_id == user_id]
        if not include_deleted:
            conditions.append(Conversation.is_deleted == False)

        # 查询总数
        count_query = select(func.count(Conversation.id)).where(and_(*conditions))
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        # 查询列表
        list_query = (
            select(Conversation)
            .where(and_(*conditions))
            .order_by(desc(Conversation.created_at))
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(list_query)
        conversations = result.scalars().all()

        return list(conversations), total

    async def search_conversations(
        self,
        user_id: str,
        keyword: str,
        offset: int = 0,
        limit: int = 20
    ) -> tuple[List[Conversation], int]:
        """
        搜索对话（按标题搜索）

        Args:
            user_id: 用户 ID
            keyword: 搜索关键词
            offset: 偏移量
            limit: 每页数量

        Returns:
            tuple[List[Conversation], int]: (对话列表, 总数)
        """
        conditions = [
            Conversation.user_id == user_id,
            Conversation.is_deleted == False,
            Conversation.title.ilike(f"%{keyword}%")
        ]

        # 查询总数
        count_query = select(func.count(Conversation.id)).where(and_(*conditions))
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        # 查询列表
        list_query = (
            select(Conversation)
            .where(and_(*conditions))
            .order_by(desc(Conversation.created_at))
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(list_query)
        conversations = result.scalars().all()

        return list(conversations), total

    async def update_conversation(
        self,
        conversation_id: str,
        title: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> Optional[Conversation]:
        """
        更新对话

        Args:
            conversation_id: 对话 ID
            title: 新标题（可选）
            metadata: 新元数据（可选）

        Returns:
            Optional[Conversation]: 更新后的对话，如果不存在则返回 None
        """
        conversation = await self.get_conversation_by_id(conversation_id, include_messages=False)
        if not conversation:
            return None

        if title is not None:
            conversation.title = title
        if metadata is not None:
            conversation.metadata_json = metadata

        conversation.updated_at = datetime.now()

        await self.session.commit()
        await self.session.refresh(conversation)

        return conversation

    async def delete_conversation(
        self,
        conversation_id: str,
        soft_delete: bool = True
    ) -> bool:
        """
        删除对话

        Args:
            conversation_id: 对话 ID
            soft_delete: 是否软删除（默认 True）

        Returns:
            bool: 是否删除成功
        """
        conversation = await self.get_conversation_by_id(conversation_id, include_messages=False)
        if not conversation:
            return False

        if soft_delete:
            conversation.is_deleted = True
            conversation.updated_at = datetime.now()
            await self.session.commit()
        else:
            await self.session.delete(conversation)
            await self.session.commit()

        return True

    async def delete_conversations_batch(
        self,
        conversation_ids: List[str],
        soft_delete: bool = True
    ) -> int:
        """
        批量删除对话

        Args:
            conversation_ids: 对话 ID 列表
            soft_delete: 是否软删除（默认 True）

        Returns:
            int: 删除的对话数量
        """
        deleted_count = 0

        for conversation_id in conversation_ids:
            success = await self.delete_conversation(conversation_id, soft_delete)
            if success:
                deleted_count += 1

        return deleted_count

    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        contexts: Optional[List[dict]] = None,
        citations: Optional[List[dict]] = None,
        model_name: Optional[str] = None,
        token_count: Optional[int] = None,
        metadata: Optional[dict] = None
    ) -> Optional[Message]:
        """
        添加消息到对话

        Args:
            conversation_id: 对话 ID
            role: 消息角色（user, assistant, system）
            content: 消息内容
            contexts: 检索上下文（可选）
            citations: 引用信息（可选）
            model_name: 模型名称（可选）
            token_count: Token 数量（可选）
            metadata: 元数据（可选）

        Returns:
            Optional[Message]: 创建的消息，如果对话不存在则返回 None
        """
        # 检查对话是否存在
        conversation = await self.get_conversation_by_id(conversation_id, include_messages=False)
        if not conversation:
            return None

        # 创建消息
        message = Message(
            id=str(uuid4()),
            conversation_id=conversation_id,
            role=role,
            content=content,
            contexts=contexts,
            citations=citations,
            model_name=model_name,
            token_count=token_count,
            metadata_json=metadata,
            created_at=datetime.now()
        )

        self.session.add(message)

        # 更新对话的消息计数和更新时间
        conversation.message_count += 1
        conversation.updated_at = datetime.now()

        await self.session.commit()
        await self.session.refresh(message)

        return message

    async def get_messages_by_conversation(
        self,
        conversation_id: str,
        offset: int = 0,
        limit: Optional[int] = None
    ) -> List[Message]:
        """
        获取对话的消息列表

        Args:
            conversation_id: 对话 ID
            offset: 偏移量
            limit: 每页数量（可选，None 表示不限制）

        Returns:
            List[Message]: 消息列表
        """
        query = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
            .offset(offset)
        )

        if limit is not None:
            query = query.limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def delete_message(self, message_id: str) -> bool:
        """
        删除消息

        Args:
            message_id: 消息 ID

        Returns:
            bool: 是否删除成功
        """
        query = select(Message).where(Message.id == message_id)
        result = await self.session.execute(query)
        message = result.scalar_one_or_none()

        if not message:
            return False

        # 更新对话的消息计数
        conversation = await self.get_conversation_by_id(
            message.conversation_id,
            include_messages=False
        )
        if conversation:
            conversation.message_count = max(0, conversation.message_count - 1)
            conversation.updated_at = datetime.now()

        await self.session.delete(message)
        await self.session.commit()

        return True

    async def get_conversation_stats(self, user_id: str) -> dict:
        """
        获取对话统计信息

        Args:
            user_id: 用户 ID

        Returns:
            dict: 统计信息
                - total: 总对话数
                - today: 今日对话数
                - this_week: 本周对话数
                - this_month: 本月对话数
        """
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start.replace(day=today_start.day - today_start.weekday())
        month_start = today_start.replace(day=1)

        # 总对话数
        total_query = select(func.count(Conversation.id)).where(
            and_(
                Conversation.user_id == user_id,
                Conversation.is_deleted == False
            )
        )
        total_result = await self.session.execute(total_query)
        total = total_result.scalar_one()

        # 今日对话数
        today_query = select(func.count(Conversation.id)).where(
            and_(
                Conversation.user_id == user_id,
                Conversation.is_deleted == False,
                Conversation.created_at >= today_start
            )
        )
        today_result = await self.session.execute(today_query)
        today = today_result.scalar_one()

        # 本周对话数
        week_query = select(func.count(Conversation.id)).where(
            and_(
                Conversation.user_id == user_id,
                Conversation.is_deleted == False,
                Conversation.created_at >= week_start
            )
        )
        week_result = await self.session.execute(week_query)
        this_week = week_result.scalar_one()

        # 本月对话数
        month_query = select(func.count(Conversation.id)).where(
            and_(
                Conversation.user_id == user_id,
                Conversation.is_deleted == False,
                Conversation.created_at >= month_start
            )
        )
        month_result = await self.session.execute(month_query)
        this_month = month_result.scalar_one()

        return {
            "total": total,
            "today": today,
            "this_week": this_week,
            "this_month": this_month
        }
