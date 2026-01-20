"""
文档管理相关的 Pydantic 数据模型
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# ============ 请求模型 ============

class DocumentUploadRequest(BaseModel):
    """文档上传请求"""
    model_config = ConfigDict(from_attributes=True)

    title: str = Field(..., min_length=1, max_length=500, description="文档标题")
    content: str = Field(..., min_length=1, description="文档内容")
    source_type: str = Field("local", description="来源类型: local/jira/confluence")
    source_id: Optional[str] = Field(None, description="来源ID（issue_key 或 page_id）")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")


class DocumentUpdateRequest(BaseModel):
    """文档更新请求"""
    model_config = ConfigDict(from_attributes=True)

    title: Optional[str] = Field(None, min_length=1, max_length=500, description="文档标题")
    content: Optional[str] = Field(None, min_length=1, description="文档内容")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    metadata: Optional[Dict[str, Any]] = Field(None, description="额外元数据")


class DocumentQueryRequest(BaseModel):
    """文档查询请求"""
    model_config = ConfigDict(from_attributes=True)

    source_type: Optional[str] = Field(None, description="来源类型筛选")
    tags: Optional[List[str]] = Field(None, description="标签筛选（包含任意一个）")
    search_text: Optional[str] = Field(None, description="搜索文本（标题或内容）")
    limit: int = Field(100, ge=1, le=1000, description="返回数量限制")
    offset: int = Field(0, ge=0, description="偏移量")


# ============ 响应模型 ============

class DocumentMetadata(BaseModel):
    """文档元数据"""
    model_config = ConfigDict(from_attributes=True)

    document_id: str = Field(..., description="文档ID（唯一标识）")
    title: str = Field(..., description="文档标题")
    source_type: str = Field(..., description="来源类型: local/jira/confluence")
    source_id: Optional[str] = Field(None, description="来源ID")
    content_preview: str = Field(..., description="内容预览（前200字符）")
    chunk_count: int = Field(..., description="分块数量")
    indexed_at: datetime = Field(..., description="索引时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")


class DocumentDetail(BaseModel):
    """文档详情"""
    model_config = ConfigDict(from_attributes=True)

    document_id: str = Field(..., description="文档ID")
    title: str = Field(..., description="文档标题")
    content: str = Field(..., description="完整文档内容")
    source_type: str = Field(..., description="来源类型")
    source_id: Optional[str] = Field(None, description="来源ID")
    chunk_count: int = Field(..., description="分块数量")
    chunks: List[str] = Field(default_factory=list, description="分块ID列表")
    indexed_at: datetime = Field(..., description="索引时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")


class DocumentListResponse(BaseModel):
    """文档列表响应"""
    model_config = ConfigDict(from_attributes=True)

    documents: List[DocumentMetadata] = Field(..., description="文档列表")
    total: int = Field(..., description="总数量")
    limit: int = Field(..., description="返回数量限制")
    offset: int = Field(..., description="偏移量")


class DocumentUploadResponse(BaseModel):
    """文档上传响应"""
    model_config = ConfigDict(from_attributes=True)

    document_id: str = Field(..., description="文档ID")
    title: str = Field(..., description="文档标题")
    chunk_count: int = Field(..., description="生成的分块数量")
    indexed_at: datetime = Field(..., description="索引时间")
    message: str = Field(..., description="操作消息")


class DocumentDeleteResponse(BaseModel):
    """文档删除响应"""
    model_config = ConfigDict(from_attributes=True)

    document_id: str = Field(..., description="文档ID")
    deleted_chunks: int = Field(..., description="删除的分块数量")
    message: str = Field(..., description="操作消息")


class DocumentStatsResponse(BaseModel):
    """文档统计响应"""
    model_config = ConfigDict(from_attributes=True)

    total_documents: int = Field(..., description="文档总数")
    total_chunks: int = Field(..., description="分块总数")
    by_source_type: Dict[str, int] = Field(..., description="按来源类型统计")
    by_tags: Dict[str, int] = Field(default_factory=dict, description="按标签统计")
    indexed_at_range: Optional[Dict[str, datetime]] = Field(None, description="索引时间范围")
