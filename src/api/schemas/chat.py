"""
对话相关的 Pydantic 数据模型
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


# ============ 请求模型 ============

class ChatMessage(BaseModel):
    """单条消息模型"""
    model_config = ConfigDict(from_attributes=True)

    role: str = Field(..., description="角色：user/assistant/system")
    content: str = Field(..., description="消息内容")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")


class ChatRequest(BaseModel):
    """对话请求模型"""
    model_config = ConfigDict(from_attributes=True)

    message: str = Field(..., min_length=1, description="用户消息")
    session_id: Optional[str] = Field(None, description="会话 ID（首次为 None）")
    model_name: Optional[str] = Field(None, description="指定模型（默认使用配置）")
    enable_rag: bool = Field(True, description="是否启用 RAG 检索")
    rag_top_k: int = Field(3, ge=1, le=10, description="RAG 检索文档数")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="生成温度")
    max_tokens: Optional[int] = Field(None, ge=1, description="最大生成 token 数")


# ============ 响应模型 ============

class RetrievedContext(BaseModel):
    """检索到的上下文"""
    model_config = ConfigDict(from_attributes=True)

    chunk_id: str = Field(..., description="块 ID")
    content: str = Field(..., description="文本内容")
    score: float = Field(..., description="相似度分数")
    source: Dict[str, Any] = Field(..., description="来源信息（issue_key, project_key 等）")


class ChatResponse(BaseModel):
    """对话响应模型（非流式）"""
    model_config = ConfigDict(from_attributes=True)

    session_id: str = Field(..., description="会话 ID")
    message: str = Field(..., description="助手回复")
    model: str = Field(..., description="使用的模型")
    rag_enabled: bool = Field(..., description="是否使用了 RAG")
    retrieved_contexts: Optional[List[RetrievedContext]] = Field(
        None, description="检索到的上下文"
    )
    token_count: Optional[int] = Field(None, description="生成 token 数")
    duration_ms: Optional[int] = Field(None, description="耗时（毫秒）")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")


class StreamChunk(BaseModel):
    """流式响应块"""
    model_config = ConfigDict(from_attributes=True)

    type: str = Field(..., description="类型：start/token/context/end/error")
    content: Optional[str] = Field(None, description="内容")
    data: Optional[Dict[str, Any]] = Field(None, description="额外数据")


# ============ 历史记录模型 ============

class ChatHistory(BaseModel):
    """对话历史"""
    model_config = ConfigDict(from_attributes=True)

    session_id: str = Field(..., description="会话 ID")
    messages: List[ChatMessage] = Field(default_factory=list, description="消息列表")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    model_name: str = Field(..., description="使用的模型")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")


class HistoryListResponse(BaseModel):
    """历史列表响应"""
    model_config = ConfigDict(from_attributes=True)

    histories: List[ChatHistory] = Field(..., description="历史记录列表")
    total: int = Field(..., description="总数")
