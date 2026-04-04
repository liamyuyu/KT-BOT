"""
ConversationRepository 单元测试
Story 5.1 Phase 5
"""

import pytest
from datetime import datetime
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.storage.database.base import Base
from src.storage.database.models import Conversation, Message
from src.storage.database.repository import ConversationRepository


@pytest.fixture
async def test_db():
    """创建测试数据库"""
    # 使用内存数据库
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_factory = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session_factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def test_user_id():
    """测试用户 ID"""
    return "test_user_123"


@pytest.fixture
async def repo(test_db):
    """创建 Repository 实例"""
    return ConversationRepository(session=test_db)


class TestConversationRepository:
    """测试 ConversationRepository"""

    @pytest.mark.asyncio
    async def test_create_conversation(self, repo, test_user_id):
        """测试创建对话"""
        conversation = await repo.create_conversation(
            user_id=test_user_id,
            title="测试对话",
            metadata={"test": True}
        )

        assert conversation is not None
        assert conversation.id is not None
        assert conversation.user_id == test_user_id
        assert conversation.title == "测试对话"
        assert conversation.message_count == 0
        assert conversation.metadata_json == {"test": True}
        assert conversation.is_deleted is False
        assert conversation.created_at is not None
        assert conversation.updated_at is not None

    @pytest.mark.asyncio
    async def test_get_conversation_by_id(self, repo, test_user_id):
        """测试根据 ID 获取对话"""
        # 创建对话
        created = await repo.create_conversation(
            user_id=test_user_id,
            title="测试对话"
        )

        # 获取对话
        conversation = await repo.get_conversation_by_id(created.id)

        assert conversation is not None
        assert conversation.id == created.id
        assert conversation.title == "测试对话"

    @pytest.mark.asyncio
    async def test_get_conversation_not_found(self, repo):
        """测试获取不存在的对话"""
        conversation = await repo.get_conversation_by_id("nonexistent")

        assert conversation is None

    @pytest.mark.asyncio
    async def test_list_conversations(self, repo, test_user_id):
        """测试对话列表"""
        # 创建多个对话
        for i in range(5):
            await repo.create_conversation(
                user_id=test_user_id,
                title=f"对话 {i+1}"
            )

        # 获取列表
        conversations, total = await repo.list_conversations(
            user_id=test_user_id,
            offset=0,
            limit=10
        )

        assert len(conversations) == 5
        assert total == 5
        # 验证按创建时间倒序
        assert conversations[0].title == "对话 5"
        assert conversations[4].title == "对话 1"

    @pytest.mark.asyncio
    async def test_list_conversations_pagination(self, repo, test_user_id):
        """测试分页"""
        # 创建 10 个对话
        for i in range(10):
            await repo.create_conversation(
                user_id=test_user_id,
                title=f"对话 {i+1}"
            )

        # 第一页
        page1, total = await repo.list_conversations(
            user_id=test_user_id,
            offset=0,
            limit=3
        )

        assert len(page1) == 3
        assert total == 10

        # 第二页
        page2, total = await repo.list_conversations(
            user_id=test_user_id,
            offset=3,
            limit=3
        )

        assert len(page2) == 3
        assert total == 10

        # 验证不重复
        page1_ids = {conv.id for conv in page1}
        page2_ids = {conv.id for conv in page2}
        assert page1_ids.isdisjoint(page2_ids)

    @pytest.mark.asyncio
    async def test_search_conversations(self, repo, test_user_id):
        """测试搜索对话"""
        # 创建对话
        await repo.create_conversation(user_id=test_user_id, title="Python 性能优化")
        await repo.create_conversation(user_id=test_user_id, title="Docker 部署指南")
        await repo.create_conversation(user_id=test_user_id, title="Python 最佳实践")

        # 搜索 Python
        conversations, total = await repo.search_conversations(
            user_id=test_user_id,
            keyword="Python"
        )

        assert len(conversations) == 2
        assert total == 2
        assert all("Python" in conv.title for conv in conversations)

    @pytest.mark.asyncio
    async def test_update_conversation(self, repo, test_user_id):
        """测试更新对话"""
        # 创建对话
        conversation = await repo.create_conversation(
            user_id=test_user_id,
            title="原标题",
            metadata={"old": True}
        )

        original_updated_at = conversation.updated_at

        # 更新对话
        updated = await repo.update_conversation(
            conversation_id=conversation.id,
            title="新标题",
            metadata={"new": True}
        )

        assert updated is not None
        assert updated.title == "新标题"
        assert updated.metadata_json == {"new": True}
        assert updated.updated_at > original_updated_at

    @pytest.mark.asyncio
    async def test_delete_conversation_soft(self, repo, test_user_id):
        """测试软删除对话"""
        # 创建对话
        conversation = await repo.create_conversation(
            user_id=test_user_id,
            title="待删除对话"
        )

        # 软删除
        success = await repo.delete_conversation(
            conversation_id=conversation.id,
            soft_delete=True
        )

        assert success is True

        # 验证软删除
        deleted = await repo.get_conversation_by_id(conversation.id)
        assert deleted is None  # is_deleted=True 的对话不返回

    @pytest.mark.asyncio
    async def test_delete_conversation_hard(self, repo, test_user_id):
        """测试硬删除对话"""
        # 创建对话
        conversation = await repo.create_conversation(
            user_id=test_user_id,
            title="待删除对话"
        )

        # 硬删除
        success = await repo.delete_conversation(
            conversation_id=conversation.id,
            soft_delete=False
        )

        assert success is True

        # 验证硬删除
        deleted = await repo.get_conversation_by_id(conversation.id)
        assert deleted is None

    @pytest.mark.asyncio
    async def test_delete_conversations_batch(self, repo, test_user_id):
        """测试批量删除"""
        # 创建 3 个对话
        conv_ids = []
        for i in range(3):
            conv = await repo.create_conversation(
                user_id=test_user_id,
                title=f"对话 {i+1}"
            )
            conv_ids.append(conv.id)

        # 批量删除
        deleted_count = await repo.delete_conversations_batch(
            conversation_ids=conv_ids,
            soft_delete=True
        )

        assert deleted_count == 3

        # 验证删除
        conversations, total = await repo.list_conversations(
            user_id=test_user_id,
            include_deleted=False
        )

        assert total == 0

    @pytest.mark.asyncio
    async def test_add_message(self, repo, test_user_id):
        """测试添加消息"""
        # 创建对话
        conversation = await repo.create_conversation(
            user_id=test_user_id,
            title="测试对话"
        )

        # 添加消息
        message = await repo.add_message(
            conversation_id=conversation.id,
            role="user",
            content="测试消息",
            model_name="qwen2.5:14b",
            token_count=10
        )

        assert message is not None
        assert message.conversation_id == conversation.id
        assert message.role == "user"
        assert message.content == "测试消息"
        assert message.model_name == "qwen2.5:14b"
        assert message.token_count == 10

        # 验证对话消息计数更新
        updated_conv = await repo.get_conversation_by_id(conversation.id)
        assert updated_conv.message_count == 1

    @pytest.mark.asyncio
    async def test_add_message_with_contexts(self, repo, test_user_id):
        """测试添加带上下文的消息"""
        # 创建对话
        conversation = await repo.create_conversation(
            user_id=test_user_id,
            title="测试对话"
        )

        contexts = [
            {"doc_id": "doc1", "content": "上下文1"},
            {"doc_id": "doc2", "content": "上下文2"}
        ]

        citations = [
            {"title": "文档1", "url": "http://example.com/1"}
        ]

        # 添加消息
        message = await repo.add_message(
            conversation_id=conversation.id,
            role="assistant",
            content="回答内容",
            contexts=contexts,
            citations=citations
        )

        assert message.contexts == contexts
        assert message.citations == citations

    @pytest.mark.asyncio
    async def test_get_messages_by_conversation(self, repo, test_user_id):
        """测试获取对话消息列表"""
        # 创建对话
        conversation = await repo.create_conversation(
            user_id=test_user_id,
            title="测试对话"
        )

        # 添加多条消息
        for i in range(5):
            await repo.add_message(
                conversation_id=conversation.id,
                role="user" if i % 2 == 0 else "assistant",
                content=f"消息 {i+1}"
            )

        # 获取消息列表
        messages = await repo.get_messages_by_conversation(
            conversation_id=conversation.id
        )

        assert len(messages) == 5
        # 验证按创建时间正序
        assert messages[0].content == "消息 1"
        assert messages[4].content == "消息 5"

    @pytest.mark.asyncio
    async def test_get_messages_pagination(self, repo, test_user_id):
        """测试消息分页"""
        # 创建对话
        conversation = await repo.create_conversation(
            user_id=test_user_id,
            title="测试对话"
        )

        # 添加 10 条消息
        for i in range(10):
            await repo.add_message(
                conversation_id=conversation.id,
                role="user",
                content=f"消息 {i+1}"
            )

        # 分页获取
        page1 = await repo.get_messages_by_conversation(
            conversation_id=conversation.id,
            offset=0,
            limit=3
        )

        assert len(page1) == 3

        page2 = await repo.get_messages_by_conversation(
            conversation_id=conversation.id,
            offset=3,
            limit=3
        )

        assert len(page2) == 3

        # 验证不重复
        page1_ids = {msg.id for msg in page1}
        page2_ids = {msg.id for msg in page2}
        assert page1_ids.isdisjoint(page2_ids)

    @pytest.mark.asyncio
    async def test_delete_message(self, repo, test_user_id):
        """测试删除消息"""
        # 创建对话和消息
        conversation = await repo.create_conversation(
            user_id=test_user_id,
            title="测试对话"
        )

        message = await repo.add_message(
            conversation_id=conversation.id,
            role="user",
            content="待删除消息"
        )

        # 删除消息
        success = await repo.delete_message(message.id)

        assert success is True

        # 验证消息计数更新
        updated_conv = await repo.get_conversation_by_id(conversation.id)
        assert updated_conv.message_count == 0

    @pytest.mark.asyncio
    async def test_get_conversation_stats(self, repo, test_user_id):
        """测试获取对话统计"""
        # 创建对话
        for i in range(5):
            await repo.create_conversation(
                user_id=test_user_id,
                title=f"对话 {i+1}"
            )

        # 获取统计
        stats = await repo.get_conversation_stats(user_id=test_user_id)

        assert stats["total"] == 5
        assert stats["today"] >= 0
        assert stats["this_week"] >= 0
        assert stats["this_month"] >= 0

    @pytest.mark.asyncio
    async def test_cascade_delete(self, repo, test_user_id):
        """测试级联删除（删除对话时删除所有消息）"""
        # 创建对话
        conversation = await repo.create_conversation(
            user_id=test_user_id,
            title="测试对话"
        )

        # 添加消息
        for i in range(3):
            await repo.add_message(
                conversation_id=conversation.id,
                role="user",
                content=f"消息 {i+1}"
            )

        # 硬删除对话
        success = await repo.delete_conversation(
            conversation_id=conversation.id,
            soft_delete=False
        )

        assert success is True

        # 验证消息也被删除
        messages = await repo.get_messages_by_conversation(
            conversation_id=conversation.id
        )

        assert len(messages) == 0
