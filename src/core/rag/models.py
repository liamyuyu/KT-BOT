"""
RAG Data Models
RAG（检索增强生成）数据模型定义（使用 Pydantic）
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
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


class CitationInfo(BaseModel):
    """
    引用信息模型
    用于标识检索结果的来源和高亮关键词
    """
    source_id: str = Field(..., description="来源 ID（如 issue_key 或 document_id）")
    source_type: str = Field(..., description="来源类型（jira, confluence, local）")
    source_url: Optional[str] = Field(None, description="来源链接")
    chunk_index: int = Field(..., description="块在原文档中的序号")
    start_index: int = Field(..., description="在原文档中的起始位置")
    end_index: int = Field(..., description="在原文档中的结束位置")
    relevance_score: float = Field(..., description="相关性评分")
    highlights: List[Tuple[int, int]] = Field(default_factory=list, description="高亮位置列表（起始，结束）")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source_id": "PROJ-123",
                "source_type": "jira",
                "source_url": "https://jira.example.com/browse/PROJ-123",
                "chunk_index": 0,
                "start_index": 0,
                "end_index": 500,
                "relevance_score": 0.85,
                "highlights": [(10, 15), (50, 60)]
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
    citation: Optional[CitationInfo] = Field(None, description="引用信息")

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

    @classmethod
    def from_chunk_with_citation(
        cls,
        chunk: "Chunk",
        score: float,
        distance: float,
        query: str
    ) -> "RetrievalResult":
        """
        从 Chunk 构建带引用信息的检索结果

        Args:
            chunk: 文档块
            score: 相似度分数
            distance: 向量距离
            query: 查询文本

        Returns:
            RetrievalResult: 带引用信息的检索结果
        """
        citation = CitationInfo(
            source_id=chunk.metadata.get("issue_key") or chunk.metadata.get("document_id", "unknown"),
            source_type=chunk.metadata.get("source_type", "unknown"),
            source_url=chunk.metadata.get("url"),
            chunk_index=chunk.chunk_index,
            start_index=chunk.start_index,
            end_index=chunk.end_index,
            relevance_score=score,
            highlights=extract_highlights(chunk.content, query)
        )

        return cls(
            chunk_id=chunk.chunk_id,
            parent_id=chunk.parent_id,
            content=chunk.content,
            metadata=chunk.metadata,
            score=score,
            distance=distance,
            chunk_index=chunk.chunk_index,
            citation=citation
        )


def extract_highlights(content: str, query: str) -> List[Tuple[int, int]]:
    """
    提取查询关键词在内容中的位置

    Args:
        content: 文本内容
        query: 查询关键词

    Returns:
        List[Tuple[int, int]]: 高亮位置列表（起始，结束）
    """
    try:
        import jieba

        query_tokens = set(jieba.lcut(query.lower()))
        highlights = []
        content_lower = content.lower()

        for token in query_tokens:
            if len(token) < 2:
                continue
            start = 0
            while True:
                pos = content_lower.find(token, start)
                if pos == -1:
                    break
                highlights.append((pos, pos + len(token)))
                start = pos + 1

        return highlights
    except Exception:
        # jieba 可能未安装，返回空列表
        return []


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


class BM25Config(BaseModel):
    """
    BM25 检索配置模型
    """
    k1: float = Field(1.5, description="BM25 k1 参数（词频饱和度）", ge=0.0, le=3.0)
    b: float = Field(0.75, description="BM25 b 参数（文档长度归一化）", ge=0.0, le=1.0)
    use_idf: bool = Field(True, description="是否使用 IDF（逆文档频率）")
    enable_cache: bool = Field(True, description="是否启用索引缓存")
    cache_dir: str = Field("./data/bm25_cache", description="缓存目录")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "k1": 1.5,
                "b": 0.75,
                "use_idf": True,
                "enable_cache": True,
                "cache_dir": "./data/bm25_cache"
            }
        }
    )


class HybridConfig(BaseModel):
    """
    混合检索配置模型
    """
    fusion_method: str = Field(
        "rrf",
        description="融合方法：rrf (Reciprocal Rank Fusion), weighted (加权平均), linear (线性组合)"
    )
    rrf_k: int = Field(60, description="RRF 参数 k（默认 60）", ge=1, le=1000)
    vector_weight: float = Field(
        0.5,
        description="向量检索权重（0-1，weighted/linear 方法使用）",
        ge=0.0,
        le=1.0
    )
    bm25_weight: float = Field(
        0.5,
        description="BM25 检索权重（0-1，weighted/linear 方法使用）",
        ge=0.0,
        le=1.0
    )
    deduplicate: bool = Field(True, description="是否去重（基于 chunk_id）")
    normalize_scores: bool = Field(True, description="是否归一化分数到 0-1 区间")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "fusion_method": "rrf",
                "rrf_k": 60,
                "vector_weight": 0.5,
                "bm25_weight": 0.5,
                "deduplicate": True,
                "normalize_scores": True
            }
        }
    )

    def validate_weights(self) -> None:
        """验证权重配置的合理性"""
        if self.fusion_method in ["weighted", "linear"]:
            total_weight = self.vector_weight + self.bm25_weight
            if not (0.99 <= total_weight <= 1.01):  # 允许浮点误差
                raise ValueError(
                    f"vector_weight + bm25_weight must equal 1.0, got {total_weight}"
                )


class RerankerConfig(BaseModel):
    """
    重排序配置模型
    """
    model_name: str = Field(
        "BAAI/bge-reranker-large",
        description="Reranker 模型名称"
    )
    batch_size: int = Field(4, description="批量处理大小", ge=1, le=32)
    max_length: int = Field(512, description="最大序列长度", ge=128, le=1024)
    normalize_scores: bool = Field(True, description="是否归一化分数到 0-1 区间")
    use_fp16: bool = Field(False, description="是否使用 FP16 加速（需要 GPU）")
    device: Optional[str] = Field(None, description="运行设备（cpu/cuda/mps）")
    cache_dir: Optional[str] = Field(None, description="模型缓存目录")
    timeout_seconds: float = Field(30.0, description="超时时间（秒）", ge=1.0, le=300.0)

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra={
            "example": {
                "model_name": "BAAI/bge-reranker-large",
                "batch_size": 4,
                "max_length": 512,
                "normalize_scores": True,
                "use_fp16": False,
                "device": "cpu",
                "timeout_seconds": 30.0
            }
        }
    )


class RerankerResult(BaseModel):
    """
    重排序结果模型
    """
    chunk_id: str = Field(..., description="块 ID")
    parent_id: str = Field(..., description="父文档 ID")
    content: str = Field(..., description="块内容")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="块元数据")
    original_score: float = Field(..., description="原始检索分数")
    rerank_score: float = Field(..., description="重排序分数（0-1，越大越相关）")
    original_rank: int = Field(..., description="原始排名（从 0 开始）")
    new_rank: int = Field(..., description="重排序后排名（从 0 开始）")
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
                "original_score": 0.75,
                "rerank_score": 0.92,
                "original_rank": 5,
                "new_rank": 1
            }
        }
    )
