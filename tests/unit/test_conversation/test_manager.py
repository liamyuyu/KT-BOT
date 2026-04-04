"""
ConversationManager 单元测试
Story 5.1 Phase 5
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.services.conversation import (
    ConversationManager,
    ConversationCreate,
    ConversationUpdate,
    MessageCreate,
    MessageRole,
    ExportFormat
)
from src.storage.database.models import Conversation, Message


@pytest.fixture
def mock_session():
    """模拟数据库会话"""
    return AsyncMock()


@pytest.fixture
def mock_repo():
    """模拟 Repository"""
    return AsyncMock()


@pytest.fixture
def manager(mock_session):
    """创建 Manager 实例"""
    return ConversationManager(session=mock_session)


@pytest.fixture
def sample_conversation():
    """示例对话"""
    return Conversation(
        id="conv-123",
        user_id="user-123",
        title="测试对话",
        message_count=5,
        metadata_json={"test": True},
        is_deleted=False,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        messages=[]
    )


@pytest.fixture
def sample_message():
    """示例消息"""
    return Message(
        id="msg-123",
        conversation_id="conv-123",
        role="user",
        content="测试消息",
        contexts=None,
        citations=None,
        model_name="qwen2.5:14b",
        token_count=10,
        metadata_json=None,
        created_at=datetime.now()
    )


class TestConversationManager:
    """测试 ConversationManager"""

    @pytest.mark.asyncio
    async def test_create_conversation(self, manager, sample_conversation):
        """测试创建对话"""
        # Mock repository
        manager.repo.create_conversation = AsyncMock(return_value=sample_conversation)

        request = ConversationCreate(
            title="测试对话",
            metadata={"test": True}
        )

        result = await manager.create_conversation(
            user_id="user-123",
            request=request
        )

        assert result.id == "conv-123"
        assert result.title == "测试对话"
        assert result.message_count == 5

        # 验证调用
        manager.repo.create_conversation.assert_called_once_with(
            user_id="user-123",
            title="测试对话",
            metadata={"test": True}
        )

    @pytest.mark.asyncio
    async def test_create_conversation_with_auto_title(self, manager, sample_conversation):
        """测试创建对话（自动生成标题）"""
        # Mock repository 和 title generator
        sample_conversation.title = "如何优化 Python 性能"
        manager.repo.create_conversation = AsyncMock(return_value=sample_conversation)
        manager.title_generator.generate_title = MagicMock(
            return_value="如何优化 Python 性能"
        )

        request = ConversationCreate(title="新对话")

        result = await manager.create_conversation(
            user_id="user-123",
            request=request,
            auto_generate_title=True,
            first_message="如何优化 Python 性能？"
        )

        assert result.title == "如何优化 Python 性能"

        # 验证标题生成器被调用
        manager.title_generator.generate_title.assert_called_once_with(
            "如何优化 Python 性能？"
        )

    @pytest.mark.asyncio
    async def test_get_conversation(self, manager, sample_conversation):
        """测试获取对话详情"""
        # Mock repository
        manager.repo.get_conversation_by_id = AsyncMock(return_value=sample_conversation)

        result = await manager.get_conversation(
            conversation_id="conv-123",
            include_messages=True
        )

        assert result is not None
        assert result.id == "conv-123"
        assert result.title == "测试对话"

    @pytest.mark.asyncio
    async def test_get_conversation_not_found(self, manager):
        """测试获取不存在的对话"""
        # Mock repository
        manager.repo.get_conversation_by_id = AsyncMock(return_value=None)

        result = await manager.get_conversation(
            conversation_id="nonexistent"
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_list_conversations(self, manager, sample_conversation):
        """测试对话列表"""
        # Mock repository
        manager.repo.list_conversations = AsyncMock(
            return_value=([sample_conversation], 1)
        )

        result = await manager.list_conversations(
            user_id="user-123",
            page=1,
            page_size=20
        )

        assert result.total == 1
        assert len(result.conversations) == 1
        assert result.conversations[0].id == "conv-123"

    @pytest.mark.asyncio
    async def test_search_conversations(self, manager, sample_conversation):
        """测试搜索对话"""
        # Mock repository
        manager.repo.search_conversations = AsyncMock(
            return_value=([sample_conversation], 1)
        )

        result = await manager.search_conversations(
            user_id="user-123",
            keyword="Python",
            page=1,
            page_size=20
        )

        assert result.total == 1
        assert len(result.conversations) == 1

        # 验证调用
        manager.repo.search_conversations.assert_called_once_with(
            user_id="user-123",
            keyword="Python",
            offset=0,
            limit=20
        )

    @pytest.mark.asyncio
    async def test_update_conversation(self, manager, sample_conversation):
        """测试更新对话"""
        # Mock repository
        sample_conversation.title = "更新后的标题"
        manager.repo.update_conversation = AsyncMock(return_value=sample_conversation)

        request = ConversationUpdate(title="更新后的标题")

        result = await manager.update_conversation(
            conversation_id="conv-123",
            request=request
        )

        assert result is not None
        assert result.title == "更新后的标题"

    @pytest.mark.asyncio
    async def test_delete_conversation(self, manager):
        """测试删除对话"""
        # Mock repository
        manager.repo.delete_conversation = AsyncMock(return_value=True)

        result = await manager.delete_conversation(
            conversation_id="conv-123",
            soft_delete=True
        )

        assert result is True

        # 验证调用
        manager.repo.delete_conversation.assert_called_once_with(
            "conv-123",
            soft_delete=True
        )

    @pytest.mark.asyncio
    async def test_delete_conversations_batch(self, manager):
        """测试批量删除对话"""
        # Mock repository
        manager.repo.delete_conversations_batch = AsyncMock(return_value=3)

        result = await manager.delete_conversations_batch(
            conversation_ids=["conv-1", "conv-2", "conv-3"],
            soft_delete=True
        )

        assert result == 3

    @pytest.mark.asyncio
    async def test_add_message(self, manager, sample_message):
        """测试添加消息"""
        # Mock repository
        manager.repo.add_message = AsyncMock(return_value=sample_message)

        request = MessageCreate(
            role=MessageRole.USER,
            content="测试消息",
            model_name="qwen2.5:14b",
            token_count=10
        )

        result = await manager.add_message(
            conversation_id="conv-123",
            request=request
        )

        assert result is not None
        assert result.id == "msg-123"
        assert result.content == "测试消息"

    @pytest.mark.asyncio
    async def test_get_messages(self, manager, sample_message):
        """测试获取消息列表"""
        # Mock repository
        manager.repo.get_messages_by_conversation = AsyncMock(
            return_value=[sample_message]
        )

        result = await manager.get_messages(
            conversation_id="conv-123",
            page=1,
            page_size=50
        )

        assert len(result) == 1
        assert result[0].id == "msg-123"

    @pytest.mark.asyncio
    async def test_delete_message(self, manager):
        """测试删除消息"""
        # Mock repository
        manager.repo.delete_message = AsyncMock(return_value=True)

        result = await manager.delete_message(message_id="msg-123")

        assert result is True

    @pytest.mark.asyncio
    async def test_get_stats(self, manager):
        """测试获取统计信息"""
        # Mock repository
        manager.repo.get_conversation_stats = AsyncMock(
            return_value={
                "total": 42,
                "today": 3,
                "this_week": 12,
                "this_month": 28
            }
        )

        result = await manager.get_stats(user_id="user-123")

        assert result.total == 42
        assert result.today == 3
        assert result.this_week == 12
        assert result.this_month == 28

    @pytest.mark.asyncio
    async def test_export_conversation_markdown(self, manager, sample_conversation):
        """测试导出对话为 Markdown"""
        # 添加消息
        sample_conversation.messages = [
            Message(
                id="msg-1",
                conversation_id="conv-123",
                role="user",
                content="用户消息",
                created_at=datetime.now()
            ),
            Message(
                id="msg-2",
                conversation_id="conv-123",
                role="assistant",
                content="助手回复",
                created_at=datetime.now()
            )
        ]

        # Mock repository
        manager.repo.get_conversation_by_id = AsyncMock(return_value=sample_conversation)

        # Mock exporter
        manager.exporter.export = MagicMock(return_value=b"# Markdown content")

        result = await manager.export_conversation(
            conversation_id="conv-123",
            format=ExportFormat.MARKDOWN
        )

        assert result is not None
        assert isinstance(result, bytes)

        # 验证 exporter 被调用
        manager.exporter.export.assert_called_once()

    @pytest.mark.asyncio
    async def test_export_conversation_not_found(self, manager):
        """测试导出不存在的对话"""
        # Mock repository
        manager.repo.get_conversation_by_id = AsyncMock(return_value=None)

        result = await manager.export_conversation(
            conversation_id="nonexistent",
            format=ExportFormat.MARKDOWN
        )

        assert result is None
