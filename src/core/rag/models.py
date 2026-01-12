"""
RAG Data Models
RAG（检索增强生成）数据模型定义（使用 Pydantic）
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class Chunk(BaseModel):
    """
    文档块模型
    表示从原始文档分割出的一个文本块
    """
    chunk_id: str = Field(..., description="块唯一 ID（格式：parent_id_chunk_index）")
    parent_id: str = Field(..., description="父文档 ID（如 Jira Issue Key）")
    content: str = Field(..., description="块的文本内容")
    embedding: Optional[List[float]] = Field(None, description="文本向量（可选，会自动生成）")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="块元数据")
    chunk_index: int = Field(..., description="块在原文档中的序号（从 0 开始）")
    start_index: int = Field(..., description="在原文档中的起始字符位置")
    end_index: int = Field(..., description="在原文档中的结束字符位置")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "chunk_id": "PROJ-123_chunk_0",
                "parent_id": "PROJ-123",
                "content": "这是一个 Jira Issue 的描述内容...",
                "chunk_index": 0,
                "start_index": 0,
                "end_index": 500,
                "metadata": {
                    "source_type": "jira",
                    "issue_type": "Story",
                    "project_key": "PROJ",
                    "created_at": "2024-01-01T00:00:00"
                }
            }
        }
    )


class IndexResult(BaseModel):
    """
    索引结果模型
    表示一次索引操作的结果统计
    """
    total_documents: int = Field(..., description="处理的文档总数")
    total_chunks: int = Field(..., description="生成的块总数")
    success_count: int = Field(..., description="成功索引的块数")
    failed_count: int = Field(0, description="失败的块数")
    errors: List[str] = Field(default_factory=list, description="错误信息列表")
    duration_seconds: Optional[float] = Field(None, description="索引耗时（秒）")
    indexed_at: datetime = Field(default_factory=datetime.now, description="索引时间")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_documents": 10,
                "total_chunks": 45,
                "success_count": 45,
                "failed_count": 0,
                "errors": [],
                "duration_seconds": 12.5,
                "indexed_at": "2024-01-01T00:00:00"
            }
        }
    )


class RetrievalResult(BaseModel):
    """
    检索结果模型
    表示一个检索到的文档块及其相关性信息
    """
    chunk_id: str = Field(..., description="块 ID")
    parent_id: str = Field(..., description="父文档 ID")
    content: str = Field(..., description="块内容")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="块元数据")
    score: float = Field(..., description="相似度分数（0-1，越大越相似）")
    distance: float = Field(..., description="向量距离（越小越相似）")
    chunk_index: int = Field(..., description="块在原文档中的序号")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "chunk_id": "PROJ-123_chunk_0",
                "parent_id": "PROJ-123",
                "content": "这是一个 Jira Issue 的描述内容...",
                "chunk_index": 0,
                "metadata": {
                    "source_type": "jira",
                    "issue_type": "Story",
                    "project_key": "PROJ"
                },
                "score": 0.85,
                "distance": 0.15
            }
        }
    )


class ChunkingConfig(BaseModel):
    """
    文档分块配置模型
    """
    chunk_size: int = Field(800, description="块大小（字符数）", ge=100, le=5000)
    chunk_overlap: int = Field(150, description="块重叠大小（字符数）", ge=0, le=1000)
    min_chunk_size: int = Field(50, description="最小块大小（字符数）", ge=10, le=500)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "chunk_size": 800,
                "chunk_overlap": 150,
                "min_chunk_size": 50
            }
        }
    )

    def validate_config(self) -> None:
        """验证配置的合理性"""
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
        if self.min_chunk_size > self.chunk_size:
            raise ValueError("min_chunk_size must be less than or equal to chunk_size")


class RetrievalConfig(BaseModel):
    """
    检索配置模型
    """
    top_k: int = Field(5, description="返回的结果数量", ge=1, le=100)
    min_score: Optional[float] = Field(None, description="最小相似度分数阈值（0-1）", ge=0.0, le=1.0)
    include_metadata: bool = Field(True, description="是否包含元数据")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "top_k": 5,
                "min_score": 0.7,
                "include_metadata": True
            }
        }
    )
