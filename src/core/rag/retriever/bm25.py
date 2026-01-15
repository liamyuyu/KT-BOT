"""
BM25 Retriever
基于 BM25 算法的全文检索器（支持中文）
"""

import logging
import pickle
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import jieba
from rank_bm25 import BM25Okapi

from ..models import RetrievalResult, RetrievalConfig, BM25Config, Chunk
from ..exceptions import RetrievalError, InvalidConfigError
from .base import BaseRetriever

logger = logging.getLogger(__name__)


# 中文停用词列表（基础版本）
CHINESE_STOPWORDS = set([
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也", "很",
    "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这", "那", "来", "个",
    "为", "与", "之", "而", "及", "以", "于", "从", "对", "将", "被", "把", "向", "往", "给", "由"
])


class BM25Retriever(BaseRetriever):
    """
    BM25 全文检索器

    使用 BM25Okapi 算法进行全文检索，支持中文分词
    """

    def __init__(
        self,
        retrieval_config: RetrievalConfig = None,
        bm25_config: BM25Config = None
    ):
        """
        初始化 BM25 检索器

        Args:
            retrieval_config: 检索配置
            bm25_config: BM25 特定配置
        """
        super().__init__(retrieval_config)
        self.bm25_config = bm25_config or BM25Config()

        # BM25 模型和文档数据
        self.bm25_model: Optional[BM25Okapi] = None
        self.documents: List[Chunk] = []
        self.tokenized_corpus: List[List[str]] = []

        # 确保缓存目录存在
        if self.bm25_config.enable_cache:
            Path(self.bm25_config.cache_dir).mkdir(parents=True, exist_ok=True)

        logger.info(
            f"BM25Retriever initialized with k1={self.bm25_config.k1}, "
            f"b={self.bm25_config.b}, cache={self.bm25_config.enable_cache}"
        )

    def _tokenize(self, text: str, remove_stopwords: bool = True) -> List[str]:
        """
        中文分词

        Args:
            text: 输入文本
            remove_stopwords: 是否移除停用词

        Returns:
            分词后的词列表
        """
        if not text or not text.strip():
            return []

        # 使用 jieba 进行中文分词
        tokens = jieba.lcut(text.lower())

        # 过滤停用词和空白
        if remove_stopwords:
            tokens = [
                token for token in tokens
                if token.strip() and token not in CHINESE_STOPWORDS and len(token) > 1
            ]
        else:
            tokens = [token for token in tokens if token.strip()]

        return tokens

    def index_documents(self, documents: List[Chunk]) -> None:
        """
        索引文档

        Args:
            documents: 文档块列表

        Raises:
            RetrievalError: 索引失败时抛出
        """
        if not documents:
            raise InvalidConfigError("Cannot index empty document list")

        try:
            logger.info(f"Indexing {len(documents)} documents with BM25...")

            # 保存文档
            self.documents = documents

            # 分词处理
            self.tokenized_corpus = []
            for doc in documents:
                tokens = self._tokenize(doc.content)
                # BM25 需要至少一个 token，空文档添加占位符
                if not tokens:
                    tokens = ["<empty>"]
                self.tokenized_corpus.append(tokens)

            # 创建 BM25 模型
            self.bm25_model = BM25Okapi(
                self.tokenized_corpus,
                k1=self.bm25_config.k1,
                b=self.bm25_config.b
            )

            logger.info(f"BM25 index created successfully for {len(documents)} documents")

        except Exception as e:
            logger.error(f"Failed to index documents: {e}", exc_info=True)
            raise RetrievalError(f"BM25 indexing failed: {str(e)}")

    def update_index(self, new_documents: List[Chunk], rebuild_threshold: int = 1000) -> None:
        """
        更新索引（增量追加新文档）

        注意：BM25 算法需要重新计算 IDF，因此增量更新实际上会重建索引。
        为了优化性能，可以设置 rebuild_threshold 来延迟重建。

        Args:
            new_documents: 新文档块列表
            rebuild_threshold: 重建阈值（累积文档数超过此值才重建，默认 1000）
        """
        if not new_documents:
            return

        logger.info(f"Updating BM25 index with {len(new_documents)} new documents")
        start_time = time.time()

        # 追加文档
        old_count = len(self.documents)
        self.documents.extend(new_documents)

        # 检查是否需要重建索引
        new_count = len(self.documents)
        if new_count - old_count >= rebuild_threshold or not hasattr(self, '_pending_rebuild'):
            # 重新索引（BM25 不支持真正的增量更新，需要重建）
            self.index_documents(self.documents)
            elapsed = time.time() - start_time
            logger.info(f"BM25 index rebuilt in {elapsed:.3f}s, total documents: {new_count}")
        else:
            # 延迟重建，只添加到文档列表
            logger.info(f"Pending rebuild: {new_count - old_count} new documents added")

    def batch_update(self, document_batches: List[List[Chunk]]) -> None:
        """
        批量更新索引（优化大量文档更新）

        Args:
            document_batches: 文档批次列表
        """
        logger.info(f"Batch updating BM25 index with {len(document_batches)} batches")
        start_time = time.time()

        # 收集所有文档
        all_new_docs = []
        for batch in document_batches:
            all_new_docs.extend(batch)

        # 一次性更新
        self.documents.extend(all_new_docs)
        self.index_documents(self.documents)

        elapsed = time.time() - start_time
        logger.info(
            f"Batch update completed: {len(all_new_docs)} documents added in {elapsed:.3f}s"
        )

    async def retrieve(
        self,
        query: str,
        top_k: int = None,
        **kwargs
    ) -> List[RetrievalResult]:
        """
        检索相关文档（带性能监控）

        Args:
            query: 查询文本
            top_k: 返回结果数量（覆盖配置）
            **kwargs: 其他参数

        Returns:
            检索结果列表

        Raises:
            RetrievalError: 检索失败时抛出
        """
        start_time = time.time()

        if not self.bm25_model:
            raise RetrievalError("BM25 model not initialized. Call index_documents() first.")

        if not query or not query.strip():
            raise InvalidConfigError("Query cannot be empty")

        try:
            # 使用配置的 top_k 或传入的 top_k
            k = top_k if top_k is not None else self.config.top_k

            # 分词查询（记录时间）
            tokenize_start = time.time()
            query_tokens = self._tokenize(query)
            tokenize_time = time.time() - tokenize_start

            if not query_tokens:
                logger.warning(f"Query tokenization resulted in empty tokens: {query}")
                return []

            logger.debug(f"Tokenization: {len(query_tokens)} tokens in {tokenize_time:.3f}s")

            # BM25 打分（记录时间）
            scoring_start = time.time()
            scores = self.bm25_model.get_scores(query_tokens)
            scoring_time = time.time() - scoring_start

            logger.debug(f"BM25 scoring: {len(scores)} documents in {scoring_time:.3f}s")

            # 获取 top-k 结果的索引
            ranking_start = time.time()
            top_indices = sorted(
                range(len(scores)),
                key=lambda i: scores[i],
                reverse=True
            )[:k]
            ranking_time = time.time() - ranking_start

            logger.debug(f"Ranking: top-{k} selection in {ranking_time:.3f}s")

            # 构建检索结果
            build_start = time.time()
            results = []
            for idx in top_indices:
                raw_score = float(scores[idx])

                # 归一化分数到 0-1 区间（使用 sigmoid 函数）
                # score = 1 / (1 + exp(-raw_score/10))
                import math
                normalized_score = 1 / (1 + math.exp(-raw_score / 10))

                # 过滤低分结果
                if self.config.min_score and normalized_score < self.config.min_score:
                    continue

                doc = self.documents[idx]

                result = RetrievalResult(
                    chunk_id=doc.chunk_id,
                    parent_id=doc.parent_id,
                    content=doc.content,
                    metadata=doc.metadata if self.config.include_metadata else {},
                    score=normalized_score,
                    distance=1.0 - normalized_score,  # distance 与 score 相反
                    chunk_index=doc.chunk_index
                )
                results.append(result)

            build_time = time.time() - build_start

            # 记录总耗时
            total_time = time.time() - start_time

            logger.info(
                f"BM25 retrieval completed: {len(results)} results in {total_time:.3f}s "
                f"(tokenize={tokenize_time:.3f}s, score={scoring_time:.3f}s, "
                f"rank={ranking_time:.3f}s, build={build_time:.3f}s)"
            )

            return results

        except Exception as e:
            logger.error(f"BM25 retrieval failed: {e}", exc_info=True)
            raise RetrievalError(f"BM25 retrieval failed: {str(e)}")

    async def batch_retrieve(
        self,
        queries: List[str],
        top_k: int = None,
        **kwargs
    ) -> List[List[RetrievalResult]]:
        """
        批量检索

        Args:
            queries: 查询文本列表
            top_k: 每个查询返回的结果数量
            **kwargs: 其他参数

        Returns:
            嵌套的检索结果列表
        """
        results = []
        for query in queries:
            result = await self.retrieve(query, top_k, **kwargs)
            results.append(result)
        return results

    def save_index(self, filepath: str = None) -> None:
        """
        保存 BM25 索引到文件

        Args:
            filepath: 保存路径（默认使用缓存目录）
        """
        if not self.bm25_model:
            raise RetrievalError("No BM25 model to save")

        try:
            if filepath is None:
                filepath = Path(self.bm25_config.cache_dir) / "bm25_index.pkl"
            else:
                filepath = Path(filepath)

            # 确保目录存在
            filepath.parent.mkdir(parents=True, exist_ok=True)

            # 保存模型和文档
            data = {
                "bm25_model": self.bm25_model,
                "documents": self.documents,
                "tokenized_corpus": self.tokenized_corpus,
                "config": {
                    "k1": self.bm25_config.k1,
                    "b": self.bm25_config.b
                }
            }

            with open(filepath, "wb") as f:
                pickle.dump(data, f)

            logger.info(f"BM25 index saved to {filepath}")

        except Exception as e:
            logger.error(f"Failed to save BM25 index: {e}", exc_info=True)
            raise RetrievalError(f"Failed to save BM25 index: {str(e)}")

    def load_index(self, filepath: str = None) -> None:
        """
        从文件加载 BM25 索引

        Args:
            filepath: 加载路径（默认使用缓存目录）
        """
        try:
            if filepath is None:
                filepath = Path(self.bm25_config.cache_dir) / "bm25_index.pkl"
            else:
                filepath = Path(filepath)

            if not filepath.exists():
                raise FileNotFoundError(f"Index file not found: {filepath}")

            with open(filepath, "rb") as f:
                data = pickle.load(f)

            self.bm25_model = data["bm25_model"]
            self.documents = data["documents"]
            self.tokenized_corpus = data["tokenized_corpus"]

            logger.info(f"BM25 index loaded from {filepath} ({len(self.documents)} documents)")

        except Exception as e:
            logger.error(f"Failed to load BM25 index: {e}", exc_info=True)
            raise RetrievalError(f"Failed to load BM25 index: {str(e)}")

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取索引统计信息

        Returns:
            统计信息字典
        """
        if not self.bm25_model:
            return {
                "indexed": False,
                "document_count": 0
            }

        return {
            "indexed": True,
            "document_count": len(self.documents),
            "average_doc_length": self.bm25_model.avgdl if hasattr(self.bm25_model, 'avgdl') else 0,
            "config": {
                "k1": self.bm25_config.k1,
                "b": self.bm25_config.b
            }
        }


# 全局单例
_bm25_retriever_instance: Optional[BM25Retriever] = None


def get_bm25_retriever(
    retrieval_config: RetrievalConfig = None,
    bm25_config: BM25Config = None,
    force_new: bool = False
) -> BM25Retriever:
    """
    获取 BM25 检索器单例

    Args:
        retrieval_config: 检索配置
        bm25_config: BM25 配置
        force_new: 是否强制创建新实例

    Returns:
        BM25Retriever 实例
    """
    global _bm25_retriever_instance

    if force_new or _bm25_retriever_instance is None:
        _bm25_retriever_instance = BM25Retriever(retrieval_config, bm25_config)

    return _bm25_retriever_instance
