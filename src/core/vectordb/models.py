"""
Vector Database Data Models
向量数据库数据模型定义（使用 Pydantic）
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict


class Document(BaseModel):
    """
    文档模型
    用于存储到向量数据库的文档
    """
    id: str = Field(..., description="文档唯一 ID")
    content: str = Field(..., description="文档文本内容")
    embedding: Optional[List[float]] = Field(None, description="文档向量（可选，会自动生成）")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="文档元数据")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "doc_123",
                "content": "这是一个测试文档",
                "metadata": {
                    "source": "confluence",
                    "page_id": "123456",
                    "title": "测试页面",
                    "created_at": "2024-01-01T00:00:00"
                }
            }
        }
    )


class SearchResult(BaseModel):
    """
    搜索结果模型
    """
    id: str = Field(..., description="文档 ID")
    content: str = Field(..., description="文档内容")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="文档元数据")
    distance: float = Field(..., description="向量距离（越小越相似）")
    score: Optional[float] = Field(None, description="相似度分数（0-1，越大越相似）")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "doc_123",
                "content": "相关文档内容",
                "metadata": {"source": "confluence", "title": "相关页面"},
                "distance": 0.15,
                "score": 0.85
            }
        }
    )


class SearchResults(BaseModel):
    """
    搜索结果列表
    """
    results: List[SearchResult] = Field(default_factory=list, description="搜索结果列表")
    total: int = Field(..., description="总结果数")
    query: str = Field(..., description="查询文本")
    limit: int = Field(..., description="返回数量限制")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "results": [],
                "total": 10,
                "query": "如何使用 Jira",
                "limit": 5
            }
        }
    )


class CollectionInfo(BaseModel):
    """
    Collection 信息模型
    """
    name: str = Field(..., description="Collection 名称")
    count: int = Field(default=0, description="文档数量")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Collection 元数据")
    embedding_function: Optional[str] = Field(None, description="Embedding 函数名称")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "kt_bot_documents",
                "count": 1500,
                "metadata": {"description": "KT-BOT 知识库文档"},
                "embedding_function": "bge-large-zh"
            }
        }
    )


class HealthStatus(BaseModel):
    """
    向量数据库健康状态
    """
    is_connected: bool = Field(..., description="是否连接成功")
    version: Optional[str] = Field(None, description="ChromaDB 版本")
    collections: List[str] = Field(default_factory=list, description="可用的 Collection 列表")
    total_documents: int = Field(default=0, description="总文档数")
    error_message: Optional[str] = Field(None, description="错误信息")
    checked_at: datetime = Field(default_factory=datetime.now, description="检查时间")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "is_connected": True,
                "version": "0.4.22",
                "collections": ["kt_bot_documents", "jira_issues"],
                "total_documents": 2500,
                "error_message": None,
                "checked_at": "2024-01-12T00:00:00"
            }
        }
    )


class BatchInsertResult(BaseModel):
    """
    批量插入结果
    """
    success: bool = Field(..., description="是否成功")
    inserted_count: int = Field(default=0, description="成功插入的文档数")
    failed_count: int = Field(default=0, description="失败的文档数")
    failed_ids: List[str] = Field(default_factory=list, description="失败的文档 ID 列表")
    error_message: Optional[str] = Field(None, description="错误信息")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "inserted_count": 100,
                "failed_count": 0,
                "failed_ids": [],
                "error_message": None
            }
        }
    )
