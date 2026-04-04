"""
对话服务数据模型
Story 5.1: 对话历史管理
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    """消息角色枚举"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageCreate(BaseModel):
    """创建消息请求"""
    role: MessageRole = Field(..., description="消息角色")
    content: str = Field(..., min_length=1, description="消息内容")
    contexts: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="RAG检索上下文"
    )
    citations: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="引用信息"
    )
    model_name: Optional[str] = Field(None, description="模型名称")
    token_count: Optional[int] = Field(None, ge=0, description="Token数量")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class MessageResponse(BaseModel):
    """消息响应"""
    id: str = Field(..., description="消息ID")
    conversation_id: str = Field(..., description="对话ID")
    role: str = Field(..., description="消息角色")
    content: str = Field(..., description="消息内容")
    contexts: Optional[List[Dict[str, Any]]] = Field(None, description="检索上下文")
    citations: Optional[List[Dict[str, Any]]] = Field(None, description="引用信息")
    model_name: Optional[str] = Field(None, description="模型名称")
    token_count: Optional[int] = Field(None, description="Token数量")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    """创建对话请求"""
    title: str = Field(..., min_length=1, max_length=500, description="对话标题")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class ConversationUpdate(BaseModel):
    """更新对话请求"""
    title: Optional[str] = Field(None, min_length=1, max_length=500, description="对话标题")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class ConversationResponse(BaseModel):
    """对话响应"""
    id: str = Field(..., description="对话ID")
    user_id: str = Field(..., description="用户ID")
    title: str = Field(..., description="对话标题")
    message_count: int = Field(..., description="消息数量")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class ConversationDetail(ConversationResponse):
    """对话详情（包含消息列表）"""
    messages: List[MessageResponse] = Field(default_factory=list, description="消息列表")


class ConversationListResponse(BaseModel):
    """对话列表响应"""
    conversations: List[ConversationResponse] = Field(..., description="对话列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")


class ConversationStats(BaseModel):
    """对话统计信息"""
    total: int = Field(..., description="总对话数")
    today: int = Field(..., description="今日对话数")
    this_week: int = Field(..., description="本周对话数")
    this_month: int = Field(..., description="本月对话数")


class ExportFormat(str, Enum):
    """导出格式枚举"""
    MARKDOWN = "markdown"
    JSON = "json"
    PDF = "pdf"


class ExportRequest(BaseModel):
    """导出请求"""
    conversation_id: str = Field(..., description="对话ID")
    format: ExportFormat = Field(..., description="导出格式")
    include_metadata: bool = Field(True, description="是否包含元数据")
    include_contexts: bool = Field(False, description="是否包含RAG上下文")


class TitleGenerationMethod(str, Enum):
    """标题生成方法枚举"""
    KEYWORD = "keyword"  # 关键词提取
    LLM = "llm"         # LLM 生成
    AUTO = "auto"       # 自动选择


class TitleGenerationConfig(BaseModel):
    """标题生成配置"""
    method: TitleGenerationMethod = Field(
        TitleGenerationMethod.AUTO,
        description="生成方法"
    )
    max_length: int = Field(50, ge=10, le=200, description="最大标题长度")
    use_first_message: bool = Field(True, description="是否使用首条消息生成")
    keyword_count: int = Field(3, ge=1, le=5, description="关键词数量")
