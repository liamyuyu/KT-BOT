"""
文档搜索引擎
Story 4.5 Phase 1: 文档搜索引擎实现
"""

import logging
import re
import time
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from src.core.rag.retriever import VectorRetriever, BM25Retriever, HybridRetriever
from src.core.rag.models import FilterConfig, TimeRange, RetrievalResult
from .models import (
    SearchQuery,
    SearchResult,
    SearchResponse,
    SearchMethod,
    HighlightMatch
)

logger = logging.getLogger(__name__)


class DocumentSearchEngine:
    """
    文档搜索引擎
    支持向量搜索、BM25搜索和混合搜索
    """

    def __init__(
        self,
        vector_retriever: VectorRetriever,
        bm25_retriever: Optional[BM25Retriever] = None,
        hybrid_retriever: Optional[HybridRetriever] = None
    ):
        """
        初始化搜索引擎

        Args:
            vector_retriever: 向量检索器
            bm25_retriever: BM25 检索器（可选）
            hybrid_retriever: 混合检索器（可选）
        """
        self.vector_retriever = vector_retriever
        self.bm25_retriever = bm25_retriever
        self.hybrid_retriever = hybrid_retriever
        logger.info("DocumentSearchEngine initialized")

    async def search(self, query: SearchQuery) -> SearchResponse:
        """
        执行文档搜索

        Args:
            query: 搜索查询

        Returns:
            SearchResponse: 搜索响应
        """
        start_time = time.time()

        # 构建过滤配置
        filter_config = self._build_filter_config(query)

        # 执行搜索
        if query.method == SearchMethod.VECTOR:
            results = await self._vector_search(query.query, query.top_k, filter_config)
        elif query.method == SearchMethod.BM25:
            results = await self._bm25_search(query.query, query.top_k, filter_config)
        elif query.method == SearchMethod.HYBRID:
            results = await self._hybrid_search(query.query, query.top_k, filter_config)
        else:
            raise ValueError(f"Unsupported search method: {query.method}")

        # 转换为搜索结果
        search_results = []
        for result in results:
            search_result = self._convert_to_search_result(
                result,
                query.method.value,
                enable_highlight=query.enable_highlight,
                query_text=query.query,
                highlight_fields=query.highlight_fields
            )
            search_results.append(search_result)

        # 应用分页
        total = len(search_results)
        start_idx = (query.page - 1) * query.page_size
        end_idx = start_idx + query.page_size
        paginated_results = search_results[start_idx:end_idx]

        # 计算总页数
        total_pages = (total + query.page_size - 1) // query.page_size

        # 计算搜索耗时
        search_time_ms = int((time.time() - start_time) * 1000)

        logger.info(
            f"Search completed: query='{query.query}', method={query.method}, "
            f"total={total}, time={search_time_ms}ms"
        )

        return SearchResponse(
            query=query.query,
            total=total,
            results=paginated_results,
            page=query.page,
            page_size=query.page_size,
            total_pages=total_pages,
            search_time_ms=search_time_ms,
            method=query.method.value
        )

    async def _vector_search(
        self,
        query: str,
        top_k: int,
        filter_config: Optional[FilterConfig]
    ) -> List[RetrievalResult]:
        """
        向量语义搜索

        Args:
            query: 查询文本
            top_k: 返回数量
            filter_config: 过滤配置

        Returns:
            检索结果列表
        """
        logger.debug(f"Vector search: query='{query}', top_k={top_k}")
        return await self.vector_retriever.retrieve(
            query=query,
            top_k=top_k,
            filters=filter_config
        )

    async def _bm25_search(
        self,
        query: str,
        top_k: int,
        filter_config: Optional[FilterConfig]
    ) -> List[RetrievalResult]:
        """
        BM25 全文搜索

        Args:
            query: 查询文本
            top_k: 返回数量
            filter_config: 过滤配置

        Returns:
            检索结果列表
        """
        if self.bm25_retriever is None:
            logger.warning("BM25 retriever not available, falling back to vector search")
            return await self._vector_search(query, top_k, filter_config)

        logger.debug(f"BM25 search: query='{query}', top_k={top_k}")
        return await self.bm25_retriever.retrieve(
            query=query,
            top_k=top_k
        )

    async def _hybrid_search(
        self,
        query: str,
        top_k: int,
        filter_config: Optional[FilterConfig]
    ) -> List[RetrievalResult]:
        """
        混合搜索（向量 + BM25）

        Args:
            query: 查询文本
            top_k: 返回数量
            filter_config: 过滤配置

        Returns:
            检索结果列表
        """
        if self.hybrid_retriever is None:
            logger.warning("Hybrid retriever not available, falling back to vector search")
            return await self._vector_search(query, top_k, filter_config)

        logger.debug(f"Hybrid search: query='{query}', top_k={top_k}")
        return await self.hybrid_retriever.retrieve(
            query=query,
            top_k=top_k,
            filters=filter_config
        )

    def _build_filter_config(self, query: SearchQuery) -> Optional[FilterConfig]:
        """
        构建过滤配置

        Args:
            query: 搜索查询

        Returns:
            FilterConfig 或 None
        """
        if not any([query.sources, query.doc_types, query.time_range]):
            return None

        time_range = None
        if query.time_range:
            time_range = TimeRange(preset=query.time_range)

        return FilterConfig(
            sources=query.sources,
            doc_types=query.doc_types,
            time_range=time_range,
            logic="AND"
        )

    def _convert_to_search_result(
        self,
        result: RetrievalResult,
        search_method: str,
        enable_highlight: bool = True,
        query_text: str = "",
        highlight_fields: List[str] = None
    ) -> SearchResult:
        """
        将 RetrievalResult 转换为 SearchResult

        Args:
            result: 检索结果
            search_method: 搜索方法
            enable_highlight: 是否启用高亮
            query_text: 查询文本
            highlight_fields: 高亮字段

        Returns:
            SearchResult
        """
        metadata = result.metadata or {}

        # 提取基本信息
        title = metadata.get("title", metadata.get("issue_key", "未命名文档"))
        source = metadata.get("source", "unknown")
        doc_type = metadata.get("doc_type", "unknown")

        # 提取时间戳
        created_at = None
        updated_at = None
        if "created_at" in metadata:
            try:
                created_at = datetime.fromisoformat(metadata["created_at"].replace("Z", "+00:00"))
            except Exception:
                pass
        if "updated_at" in metadata:
            try:
                updated_at = datetime.fromisoformat(metadata["updated_at"].replace("Z", "+00:00"))
            except Exception:
                pass

        # 生成内容摘要（前200字符）
        content_summary = result.content[:200]
        if len(result.content) > 200:
            content_summary += "..."

        # 生成高亮
        highlights = None
        if enable_highlight and query_text:
            highlights = self._generate_highlights(
                content=result.content,
                title=title,
                query_text=query_text,
                highlight_fields=highlight_fields or ["title", "content"]
            )

        return SearchResult(
            doc_id=result.chunk_id,
            parent_id=result.parent_id,
            title=title,
            content=content_summary,
            source=source,
            doc_type=doc_type,
            score=result.score,
            metadata=metadata,
            created_at=created_at,
            updated_at=updated_at,
            highlights=highlights,
            search_method=search_method
        )

    def _generate_highlights(
        self,
        content: str,
        title: str,
        query_text: str,
        highlight_fields: List[str]
    ) -> List[HighlightMatch]:
        """
        生成关键词高亮

        Args:
            content: 内容文本
            title: 标题
            query_text: 查询文本
            highlight_fields: 高亮字段

        Returns:
            高亮匹配列表
        """
        highlights = []

        # 分词（简单按空格分词）
        keywords = query_text.split()

        # 在标题中查找
        if "title" in highlight_fields:
            for keyword in keywords:
                matches = self._find_keyword_matches(title, keyword)
                highlights.extend(matches)

        # 在内容中查找（限制前500字符）
        if "content" in highlight_fields:
            content_preview = content[:500]
            for keyword in keywords:
                matches = self._find_keyword_matches(content_preview, keyword)
                highlights.extend(matches[:3])  # 每个关键词最多3个匹配

        return highlights[:10]  # 总共最多10个高亮

    def _find_keyword_matches(self, text: str, keyword: str) -> List[HighlightMatch]:
        """
        在文本中查找关键词匹配

        Args:
            text: 待搜索文本
            keyword: 关键词

        Returns:
            匹配列表
        """
        matches = []
        # 不区分大小写搜索
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)

        for match in pattern.finditer(text):
            start = match.start()
            end = match.end()

            # 提取匹配片段（前后各20个字符）
            context_start = max(0, start - 20)
            context_end = min(len(text), end + 20)
            snippet = text[context_start:context_end]

            # 添加省略号
            if context_start > 0:
                snippet = "..." + snippet
            if context_end < len(text):
                snippet = snippet + "..."

            matches.append(HighlightMatch(
                text=snippet,
                start=start - context_start + (3 if context_start > 0 else 0),
                end=end - context_start + (3 if context_start > 0 else 0)
            ))

        return matches
