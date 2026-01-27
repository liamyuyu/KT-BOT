"""
搜索服务数据模型
Story 4.5: 搜索功能
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class SearchMethod(str, Enum):
    """搜索方法枚举"""
    VECTOR = "vector"  # 向量语义搜索
    BM25 = "bm25"      # BM25 全文搜索
    HYBRID = "hybrid"  # 混合搜索


class HighlightMatch(BaseModel):
    """关键词匹配高亮"""
    text: str = Field(..., description="匹配的文本片段")
    start: int = Field(..., description="匹配开始位置")
    end: int = Field(..., description="匹配结束位置")


class SearchQuery(BaseModel):
    """搜索查询请求"""
    query: str = Field(..., min_length=1, description="搜索关键词")
    method: SearchMethod = Field(
        SearchMethod.HYBRID,
        description="搜索方法"
    )
    top_k: int = Field(10, ge=1, le=100, description="返回结果数量")
    page: int = Field(1, ge=1, description="页码（从1开始）")
    page_size: int = Field(10, ge=1, le=50, description="每页结果数")

    # 过滤条件
    sources: Optional[List[str]] = Field(None, description="来源过滤")
    doc_types: Optional[List[str]] = Field(None, description="文档类型过滤")
    time_range: Optional[str] = Field(None, description="时间范围（1d/7d/30d/90d）")

    # 高级选项
    enable_highlight: bool = Field(True, description="是否启用关键词高亮")
    highlight_fields: List[str] = Field(
        default_factory=lambda: ["title", "content"],
        description="高亮字段"
    )


class SearchResult(BaseModel):
    """单条搜索结果"""
    doc_id: str = Field(..., description="文档ID")
    parent_id: str = Field(..., description="父文档ID")
    title: str = Field(..., description="文档标题")
    content: str = Field(..., description="内容摘要")
    source: str = Field(..., description="来源（jira/confluence/local）")
    doc_type: str = Field(..., description="文档类型")
    score: float = Field(..., description="相关度分数")

    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    # 高亮
    highlights: Optional[List[HighlightMatch]] = Field(
        None,
        description="关键词高亮匹配"
    )

    # 搜索方法
    search_method: Optional[str] = Field(None, description="使用的搜索方法")


class SearchResponse(BaseModel):
    """搜索响应"""
    query: str = Field(..., description="搜索查询")
    total: int = Field(..., description="总结果数")
    results: List[SearchResult] = Field(..., description="搜索结果列表")

    # 分页信息
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    total_pages: int = Field(..., description="总页数")

    # 搜索统计
    search_time_ms: int = Field(..., description="搜索耗时（毫秒）")
    method: str = Field(..., description="使用的搜索方法")


class SearchHistoryItem(BaseModel):
    """搜索历史条目"""
    query: str = Field(..., description="搜索查询")
    timestamp: datetime = Field(default_factory=datetime.now, description="搜索时间")
    results_count: int = Field(..., description="结果数量")
    method: str = Field(..., description="搜索方法")
