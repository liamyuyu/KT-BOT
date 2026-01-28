"""
API层过滤集成测试
测试 ChatRequest 和 ChatService 的过滤功能
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.api.schemas.chat import ChatRequest
from src.api.services.chat_service import ChatService
from src.core.rag.models import FilterConfig, TimeRange, RetrievalResult


# ========================================================================
# Fixtures
# ========================================================================

@pytest.fixture
def mock_llm_manager():
    """模拟 LLM 管理器"""
    manager = Mock()
    llm = AsyncMock()
    response = Mock()
    response.content = "This is a test response"
    response.model = "test-model"
    response.eval_count = 100
    llm.chat = AsyncMock(return_value=response)
    llm.model_name = "test-model"
    manager.create_llm = Mock(return_value=llm)
    return manager


@pytest.fixture
def mock_retrievers():
    """模拟检索器"""
    vector_retriever = AsyncMock()
    bm25_retriever = AsyncMock()
    hybrid_retriever = AsyncMock()

    # 模拟检索结果
    sample_result = RetrievalResult(
        chunk_id="test_chunk_0",
        parent_id="TEST-123",
        content="Test content",
        metadata={
            "source": "jira",
            "issue_key": "TEST-123",
            "priority": "High",
            "created_at": datetime.now().isoformat()
        },
        score=0.9,
        distance=0.1,
        chunk_index=0
    )

    vector_retriever.retrieve = AsyncMock(return_value=[sample_result])
    bm25_retriever.retrieve = AsyncMock(return_value=[sample_result])
    hybrid_retriever.retrieve = AsyncMock(return_value=[sample_result])

    return vector_retriever, bm25_retriever, hybrid_retriever


@pytest.fixture
def mock_session_manager():
    """模拟会话管理器"""
    manager = AsyncMock()
    manager.get_messages = AsyncMock(return_value=[])
    manager.add_message = AsyncMock()
    return manager


@pytest.fixture
def chat_service(mock_llm_manager, mock_retrievers, mock_session_manager):
    """创建 ChatService 实例"""
    vector_retriever, bm25_retriever, hybrid_retriever = mock_retrievers
    return ChatService(
        llm_manager=mock_llm_manager,
        vector_retriever=vector_retriever,
        bm25_retriever=bm25_retriever,
        hybrid_retriever=hybrid_retriever,
        session_manager=mock_session_manager,
        reranker=None  # 禁用重排序以简化测试
    )


# ========================================================================
# ChatRequest Filter Fields Tests
# ========================================================================

class TestChatRequestFilterFields:
    """测试 ChatRequest 的过滤字段"""

    def test_filter_config_field(self):
        """测试 filter_config 字段"""
        filter_config = FilterConfig(
            sources=["jira"],
            metadata={"priority": "High"}
        )

        request = ChatRequest(
            message="test",
            filter_config=filter_config
        )

        assert request.filter_config is not None
        assert request.filter_config.sources == ["jira"]
        assert request.filter_config.metadata == {"priority": "High"}

    def test_filter_sources_shortcut(self):
        """测试 filter_sources 快捷字段"""
        request = ChatRequest(
            message="test",
            filter_sources=["jira", "confluence"]
        )

        assert request.filter_sources == ["jira", "confluence"]

    def test_filter_time_preset_shortcut(self):
        """测试 filter_time_preset 快捷字段"""
        request = ChatRequest(
            message="test",
            filter_time_preset="7d"
        )

        assert request.filter_time_preset == "7d"

    def test_filter_doc_types_shortcut(self):
        """测试 filter_doc_types 快捷字段"""
        request = ChatRequest(
            message="test",
            filter_doc_types=["issue", "page"]
        )

        assert request.filter_doc_types == ["issue", "page"]

    def test_filter_metadata_shortcut(self):
        """测试 filter_metadata 快捷字段"""
        request = ChatRequest(
            message="test",
            filter_metadata={"priority": "High", "status": "Open"}
        )

        assert request.filter_metadata == {"priority": "High", "status": "Open"}

    def test_all_filter_fields(self):
        """测试所有过滤字段组合"""
        request = ChatRequest(
            message="test",
            filter_sources=["jira"],
            filter_time_preset="30d",
            filter_doc_types=["issue"],
            filter_metadata={"priority": "High"}
        )

        assert request.filter_sources is not None
        assert request.filter_time_preset is not None
        assert request.filter_doc_types is not None
        assert request.filter_metadata is not None


# ========================================================================
# ChatService Filter Integration Tests
# ========================================================================

class TestChatServiceFilterIntegration:
    """测试 ChatService 的过滤集成"""

    @pytest.mark.asyncio
    async def test_build_filter_config_from_full_config(self, chat_service):
        """测试从完整 FilterConfig 构建"""
        filter_config = FilterConfig(
            sources=["jira"],
            metadata={"priority": "High"}
        )

        request = ChatRequest(
            message="test",
            filter_config=filter_config
        )

        built_config = chat_service._build_filter_config(request)

        assert built_config is not None
        assert built_config.sources == ["jira"]
        assert built_config.metadata == {"priority": "High"}

    @pytest.mark.asyncio
    async def test_build_filter_config_from_shortcuts(self, chat_service):
        """测试从快捷字段构建 FilterConfig"""
        request = ChatRequest(
            message="test",
            filter_sources=["jira", "confluence"],
            filter_time_preset="7d",
            filter_doc_types=["issue"],
            filter_metadata={"priority": "High"}
        )

        built_config = chat_service._build_filter_config(request)

        assert built_config is not None
        assert built_config.sources == ["jira", "confluence"]
        assert built_config.time_range is not None
        assert built_config.time_range.preset == "7d"
        assert built_config.doc_types == ["issue"]
        assert built_config.metadata == {"priority": "High"}
        assert built_config.logic == "AND"

    @pytest.mark.asyncio
    async def test_build_filter_config_none(self, chat_service):
        """测试没有过滤条件时返回 None"""
        request = ChatRequest(message="test")
        built_config = chat_service._build_filter_config(request)

        assert built_config is None

    @pytest.mark.asyncio
    async def test_chat_with_filter_sources(self, chat_service, mock_retrievers):
        """测试带来源过滤的对话"""
        vector_retriever, _, _ = mock_retrievers

        request = ChatRequest(
            message="test question",
            enable_rag=True,
            filter_sources=["jira"]
        )

        response = await chat_service.chat(request)

        # 验证响应
        assert response.session_id is not None
        assert response.message is not None
        assert response.rag_enabled is True

        # 验证检索器被调用时传入了过滤条件
        vector_retriever.retrieve.assert_called_once()
        call_kwargs = vector_retriever.retrieve.call_args.kwargs
        assert "filters" in call_kwargs
        assert call_kwargs["filters"] is not None

    @pytest.mark.asyncio
    async def test_chat_with_filter_time_range(self, chat_service, mock_retrievers):
        """测试带时间过滤的对话"""
        vector_retriever, _, _ = mock_retrievers

        request = ChatRequest(
            message="test question",
            enable_rag=True,
            filter_time_preset="7d"
        )

        response = await chat_service.chat(request)

        # 验证响应
        assert response.rag_enabled is True

        # 验证检索器被调用时传入了时间过滤
        vector_retriever.retrieve.assert_called_once()
        call_kwargs = vector_retriever.retrieve.call_args.kwargs
        assert "filters" in call_kwargs

        # 检查过滤配置包含时间范围
        filter_config = call_kwargs["filters"]
        assert filter_config is not None
        assert filter_config.time_range is not None
        assert filter_config.time_range.preset == "7d"

    @pytest.mark.asyncio
    async def test_chat_with_multiple_filters(self, chat_service, mock_retrievers):
        """测试带多个过滤条件的对话"""
        vector_retriever, _, _ = mock_retrievers

        request = ChatRequest(
            message="test question",
            enable_rag=True,
            filter_sources=["jira"],
            filter_time_preset="30d",
            filter_metadata={"priority": "High"}
        )

        response = await chat_service.chat(request)

        # 验证响应
        assert response.rag_enabled is True

        # 验证检索器被调用
        vector_retriever.retrieve.assert_called_once()
        call_kwargs = vector_retriever.retrieve.call_args.kwargs

        # 检查所有过滤条件
        filter_config = call_kwargs["filters"]
        assert filter_config is not None
        assert filter_config.sources == ["jira"]
        assert filter_config.time_range.preset == "30d"
        assert filter_config.metadata == {"priority": "High"}

    @pytest.mark.asyncio
    async def test_chat_without_filters(self, chat_service, mock_retrievers):
        """测试没有过滤条件的对话"""
        vector_retriever, _, _ = mock_retrievers

        request = ChatRequest(
            message="test question",
            enable_rag=True
        )

        response = await chat_service.chat(request)

        # 验证响应
        assert response.rag_enabled is True

        # 验证检索器被调用时没有过滤条件
        vector_retriever.retrieve.assert_called_once()
        call_kwargs = vector_retriever.retrieve.call_args.kwargs
        assert "filters" in call_kwargs
        assert call_kwargs["filters"] is None


# ========================================================================
# Streaming Chat Filter Tests
# ========================================================================

class TestStreamingChatWithFilters:
    """测试流式对话的过滤功能"""

    @pytest.mark.asyncio
    async def test_chat_stream_with_filters(self, chat_service, mock_retrievers):
        """测试带过滤的流式对话"""
        vector_retriever, _, _ = mock_retrievers

        request = ChatRequest(
            message="test question",
            enable_rag=True,
            filter_sources=["jira"],
            filter_time_preset="7d"
        )

        events = []
        async for event in chat_service.chat_stream(request):
            events.append(event)

        # 验证事件流
        event_types = [e["event"] for e in events]
        assert "start" in event_types
        assert "end" in event_types

        # 验证检索器被调用时传入了过滤条件
        vector_retriever.retrieve.assert_called_once()
        call_kwargs = vector_retriever.retrieve.call_args.kwargs
        assert "filters" in call_kwargs

        filter_config = call_kwargs["filters"]
        assert filter_config is not None
        assert filter_config.sources == ["jira"]
        assert filter_config.time_range.preset == "7d"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
