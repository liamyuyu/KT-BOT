"""
对话服务模块
Story 5.1: 对话历史管理
"""

from .manager import ConversationManager
from .title_generator import TitleGenerator
from .exporters import ConversationExporter
from .models import (
    MessageRole,
    MessageCreate,
    MessageResponse,
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    ConversationDetail,
    ConversationListResponse,
    ConversationStats,
    ExportFormat,
    ExportRequest,
    TitleGenerationMethod,
    TitleGenerationConfig,
)

__all__ = [
    # 核心服务
    "ConversationManager",
    "TitleGenerator",
    "ConversationExporter",
    # 模型
    "MessageRole",
    "MessageCreate",
    "MessageResponse",
    "ConversationCreate",
    "ConversationUpdate",
    "ConversationResponse",
    "ConversationDetail",
    "ConversationListResponse",
    "ConversationStats",
    "ExportFormat",
    "ExportRequest",
    "TitleGenerationMethod",
    "TitleGenerationConfig",
]
