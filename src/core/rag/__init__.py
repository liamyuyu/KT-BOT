"""
RAG (Retrieval-Augmented Generation) Module
RAG 模块：文档索引和检索增强生成

本模块提供完整的 RAG 流程支持：
1. 文档分块（Chunking）
2. 文档索引（Indexing）
3. 向量检索（Retrieval）
"""

# Models
from .models import (
    Chunk,
    IndexResult,
    RetrievalResult,
    ChunkingConfig,
    RetrievalConfig,
    BM25Config,
    HybridConfig,
    RerankerConfig,
    RerankerResult
)

# Exceptions
from .exceptions import (
    RAGError,
    ChunkingError,
    IndexingError,
    RetrievalError,
    DocumentProcessingError,
    EmbeddingError,
    InvalidConfigError
)

# Chunker
from .chunker import TextChunker

# Indexer
from .indexer import DocumentIndexer, get_document_indexer

# Retriever
from .retriever import (
    BaseRetriever,
    VectorRetriever,
    get_vector_retriever,
    BM25Retriever,
    get_bm25_retriever,
    HybridRetriever,
    get_hybrid_retriever
)

# Reranker
from .reranker import (
    CrossEncoderReranker,
    get_reranker
)

__all__ = [
    # Models
    "Chunk",
    "IndexResult",
    "RetrievalResult",
    "ChunkingConfig",
    "RetrievalConfig",
    "BM25Config",
    "HybridConfig",
    "RerankerConfig",
    "RerankerResult",

    # Exceptions
    "RAGError",
    "ChunkingError",
    "IndexingError",
    "RetrievalError",
    "DocumentProcessingError",
    "EmbeddingError",
    "InvalidConfigError",

    # Chunker
    "TextChunker",

    # Indexer
    "DocumentIndexer",
    "get_document_indexer",

    # Retriever
    "BaseRetriever",
    "VectorRetriever",
    "get_vector_retriever",
    "BM25Retriever",
    "get_bm25_retriever",
    "HybridRetriever",
    "get_hybrid_retriever",

    # Reranker
    "CrossEncoderReranker",
    "get_reranker",
]
