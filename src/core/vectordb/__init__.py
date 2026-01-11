"""
Vector Database Module
向量数据库模块 - 提供 ChromaDB 向量存储和检索

主要功能:
- ChromaDB 连接和管理
- 文档向量化存储
- 向量相似度搜索
- Collection 管理
- 批量操作
- 健康检查

Usage:
    from src.core.vectordb import get_chroma_client, ChromaDBClient, Document

    # 使用全局单例
    client = get_chroma_client()
    health = client.health_check()

    # 添加文档
    doc = Document(
        id="doc_1",
        content="这是一个测试文档",
        metadata={"source": "test"}
    )
    client.add_document(doc)

    # 搜索
    results = client.search("测试", n_results=5)
    for result in results.results:
        print(f"{result.id}: {result.content} (score: {result.score})")
"""

from src.core.vectordb.chroma_client import ChromaDBClient, get_chroma_client
from src.core.vectordb.models import (
    Document,
    SearchResult,
    SearchResults,
    CollectionInfo,
    HealthStatus,
    BatchInsertResult
)
from src.core.vectordb.exceptions import (
    VectorDBError,
    VectorDBConnectionError,
    VectorDBCollectionError,
    VectorDBQueryError,
    VectorDBInsertError,
    VectorDBNotFoundError
)

__all__ = [
    # Client
    "ChromaDBClient",
    "get_chroma_client",

    # Models
    "Document",
    "SearchResult",
    "SearchResults",
    "CollectionInfo",
    "HealthStatus",
    "BatchInsertResult",

    # Exceptions
    "VectorDBError",
    "VectorDBConnectionError",
    "VectorDBCollectionError",
    "VectorDBQueryError",
    "VectorDBInsertError",
    "VectorDBNotFoundError",
]
