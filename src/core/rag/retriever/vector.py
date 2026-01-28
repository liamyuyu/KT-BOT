"""
Vector Retriever
向量检索器：基于向量相似度的检索实现
"""

import logging
from typing import List, Optional, Dict, Any, Union

from src.core.vectordb.chroma_client import ChromaDBClient, get_chroma_client
from src.core.vectordb.models import SearchResult
from src.core.llm.manager import get_llm_manager, LLMManager
from src.core.llm.base import BaseEmbedding

from .base import BaseRetriever
from ..models import RetrievalResult, RetrievalConfig, FilterConfig
from ..filters.base import BaseFilter
from ..exceptions import RetrievalError, EmbeddingError

logger = logging.getLogger(__name__)


class VectorRetriever(BaseRetriever):
    """
    向量检索器
    使用向量相似度进行检索
    """

    def __init__(
        self,
        chroma_client: Optional[ChromaDBClient] = None,
        llm_manager: Optional[LLMManager] = None,
        collection_name: str = "jira_knowledge",
        config: Optional[RetrievalConfig] = None
    ):
        """
        初始化向量检索器

        Args:
            chroma_client: ChromaDB 客户端（默认使用全局实例）
            llm_manager: LLM 管理器（默认使用全局实例）
            collection_name: ChromaDB Collection 名称
            config: 检索配置
        """
        super().__init__(config)
        self.chroma_client = chroma_client or get_chroma_client()
        self.llm_manager = llm_manager or get_llm_manager()
        self.collection_name = collection_name

        # Embedding 模型（懒加载）
        self.embedding_model: Optional[BaseEmbedding] = None

        logger.info(
            f"VectorRetriever initialized: collection={collection_name}, "
            f"top_k={self.config.top_k}, min_score={self.config.min_score}"
        )

    def _get_embedding_model(self) -> BaseEmbedding:
        """获取或创建 Embedding 模型实例（懒加载）"""
        if self.embedding_model is None:
            self.embedding_model = self.llm_manager.create_embedding()
            logger.info(f"Embedding model created: {self.embedding_model.model_name}")
        return self.embedding_model

    async def retrieve(
        self,
        query: str,
        top_k: int = None,
        filters: Optional[Union[Dict[str, Any], FilterConfig, BaseFilter]] = None,
        **kwargs
    ) -> List[RetrievalResult]:
        """
        检索相关文档

        Args:
            query: 查询文本
            top_k: 返回结果数量（覆盖配置，默认使用配置中的 top_k）
            filters: 过滤条件，支持三种格式：
                1. Dict: ChromaDB where 子句字典（如 {"project_key": "PROJ"}）
                2. FilterConfig: 过滤配置对象
                3. BaseFilter: 过滤器对象（SourceFilter, TimeRangeFilter等）
            **kwargs: 其他检索参数

        Returns:
            RetrievalResult 列表

        Raises:
            RetrievalError: 检索失败时抛出
        """
        if not query or not query.strip():
            raise RetrievalError("Query cannot be empty")

        try:
            # 1. 生成查询的 Embedding
            embedding_model = self._get_embedding_model()
            response = await embedding_model.embed(query)
            query_embedding = response.embedding

            if not query_embedding:
                raise EmbeddingError("Failed to generate query embedding")

            # 2. 处理过滤条件
            where_clause = self._build_where_clause(filters)

            # 3. 在 ChromaDB 中搜索
            n_results = top_k or self.config.top_k
            search_results = self.chroma_client.search(
                query_embeddings=[query_embedding],
                n_results=n_results,
                collection_name=self.collection_name,
                where=where_clause
            )

            # 4. 转换为 RetrievalResult
            results = self._convert_search_results(search_results)

            # 5. 应用分数过滤
            if self.config.min_score is not None:
                results = [r for r in results if r.score >= self.config.min_score]

            # 6. 如果使用 BaseFilter，应用后置过滤（Post-filtering）
            if isinstance(filters, BaseFilter):
                results = filters.apply(results)

            logger.info(
                f"Retrieved {len(results)} results for query (top_k={n_results}, "
                f"filters={type(filters).__name__ if filters else None})"
            )

            return results

        except Exception as e:
            raise RetrievalError(f"Retrieval failed: {e}")

    def _build_where_clause(
        self,
        filters: Optional[Union[Dict[str, Any], FilterConfig, BaseFilter]]
    ) -> Optional[Dict[str, Any]]:
        """
        构建 ChromaDB where 子句

        Args:
            filters: 过滤条件（Dict/FilterConfig/BaseFilter）

        Returns:
            ChromaDB where 子句字典，如果没有过滤条件则返回 None
        """
        if filters is None:
            return None

        # 如果是字典，直接返回
        if isinstance(filters, dict):
            return filters

        # 如果是 FilterConfig，转换为 where 子句
        if isinstance(filters, FilterConfig):
            return filters.to_chroma_where()

        # 如果是 BaseFilter，转换为 where 子句
        if isinstance(filters, BaseFilter):
            return filters.to_chroma_where()

        # 未知类型，记录警告
        logger.warning(f"Unknown filter type: {type(filters)}, ignoring filters")
        return None

    async def batch_retrieve(
        self,
        queries: List[str],
        top_k: int = None,
        filters: Optional[Union[Dict[str, Any], FilterConfig, BaseFilter]] = None,
        **kwargs
    ) -> List[List[RetrievalResult]]:
        """
        批量检索

        Args:
            queries: 查询文本列表
            top_k: 每个查询返回的结果数量
            filters: 元数据过滤条件
            **kwargs: 其他检索参数

        Returns:
            嵌套的 RetrievalResult 列表

        Raises:
            RetrievalError: 检索失败时抛出
        """
        if not queries:
            return []

        try:
            # 逐个查询（可以优化为批量 embedding + 批量搜索）
            results = []
            for query in queries:
                result = await self.retrieve(query, top_k, filters, **kwargs)
                results.append(result)

            logger.info(f"Batch retrieved {len(queries)} queries")

            return results

        except Exception as e:
            raise RetrievalError(f"Batch retrieval failed: {e}")

    def _convert_search_results(
        self,
        search_results: Any
    ) -> List[RetrievalResult]:
        """
        将 ChromaDB SearchResults 转换为 RetrievalResult 列表

        Args:
            search_results: ChromaDB 搜索结果

        Returns:
            RetrievalResult 列表
        """
        results = []

        # ChromaDB 返回的结果格式
        if not hasattr(search_results, 'results') or not search_results.results:
            return results

        for search_result in search_results.results:
            # 提取元数据
            metadata = search_result.metadata if self.config.include_metadata else {}

            # 计算 score（距离越小，score 越大）
            # score = 1 / (1 + distance)
            score = 1.0 / (1.0 + search_result.distance)

            result = RetrievalResult(
                chunk_id=search_result.id,
                parent_id=metadata.get("parent_id", ""),
                content=search_result.content,
                metadata=metadata,
                score=score,
                distance=search_result.distance,
                chunk_index=metadata.get("chunk_index", 0)
            )
            results.append(result)

        return results


# 全局单例
_retriever: Optional[VectorRetriever] = None


def get_vector_retriever() -> VectorRetriever:
    """
    获取全局向量检索器实例

    Returns:
        VectorRetriever: 检索器实例
    """
    global _retriever
    if _retriever is None:
        _retriever = VectorRetriever()
    return _retriever
