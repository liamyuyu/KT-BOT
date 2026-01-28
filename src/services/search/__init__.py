"""
搜索服务模块
Story 4.5: 搜索功能
"""

from .document_search import DocumentSearchEngine
from .models import (
    SearchQuery,
    SearchResult,
    SearchResponse,
    SearchMethod,
    HighlightMatch
)

__all__ = [
    "DocumentSearchEngine",
    "SearchQuery",
    "SearchResult",
    "SearchResponse",
    "SearchMethod",
    "HighlightMatch",
]
