"""
对话相关的 Pydantic 数据模型
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

from src.core.rag.models import FilterConfig


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
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    message: str = Field(..., min_length=1, description="用户消息")
    session_id: Optional[str] = Field(None, description="会话 ID（首次为 None）")
    model_name: Optional[str] = Field(None, description="指定模型（默认使用配置）")
    enable_rag: bool = Field(True, description="是否启用 RAG 检索")
    rag_top_k: int = Field(3, ge=1, le=10, description="RAG 检索文档数")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="生成温度")
    max_tokens: Optional[int] = Field(None, ge=1, description="最大生成 token 数")

    # 混合检索参数
    retrieval_method: str = Field(
        "hybrid",
        description="检索方法：vector（向量检索）/ bm25（全文检索）/ hybrid（混合检索）"
    )
    vector_weight: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="向量检索权重（0.0-1.0，仅在 hybrid 模式下生效）"
    )
    bm25_weight: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="BM25 检索权重（0.0-1.0，仅在 hybrid 模式下生效）"
    )
    fusion_method: str = Field(
        "rrf",
        description="融合方法：rrf（Reciprocal Rank Fusion）/ weighted（加权平均）/ linear（线性组合）"
    )

    # 重排序参数
    enable_reranking: bool = Field(
        True,
        description="是否启用重排序（Cross-Encoder 模型重新评分）"
    )
    rerank_top_k: int = Field(
        10,
        ge=5,
        le=50,
        description="重排序前的候选数量（先召回 rerank_top_k 个，重排序后返回 rag_top_k 个）"
    )

    # 过滤参数 (Story 3.7)
    filter_config: Optional[FilterConfig] = Field(
        None,
        description="检索结果过滤配置（按来源、时间范围、文档类型、元数据等过滤）"
    )
    filter_sources: Optional[List[str]] = Field(
        None,
        description="快捷过滤：按来源过滤（如 ['jira', 'confluence']）"
    )
    filter_time_preset: Optional[str] = Field(
        None,
        description="快捷过滤：时间预设（1d/7d/30d/90d）"
    )
    filter_doc_types: Optional[List[str]] = Field(
        None,
        description="快捷过滤：按文档类型过滤（如 ['issue', 'page']）"
    )
    filter_metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="快捷过滤：按元数据过滤（如 {'priority': 'High', 'status': 'Open'}）"
    )


# ============ 响应模型 ============

class RetrievedContext(BaseModel):
    """检索到的上下文"""
    model_config = ConfigDict(from_attributes=True)

    chunk_id: str = Field(..., description="块 ID")
    content: str = Field(..., description="文本内容")
    score: float = Field(..., description="相似度分数")
    source: Dict[str, Any] = Field(..., description="来源信息（issue_key, project_key 等）")
    retrieval_method: Optional[str] = Field(None, description="使用的检索方法（vector/bm25/hybrid）")
    distance: Optional[float] = Field(None, description="向量距离（越小越相似）")

    # 重排序信息
    rerank_score: Optional[float] = Field(None, description="重排序分数（0-1，越大越相关）")
    original_rank: Optional[int] = Field(None, description="原始排名（重排序前）")
    reranked: Optional[bool] = Field(False, description="是否经过重排序")

    # 引用溯源信息
    citation: Optional[Dict[str, Any]] = Field(None, description="引用信息（source_id, source_type, highlights 等）")


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
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

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
