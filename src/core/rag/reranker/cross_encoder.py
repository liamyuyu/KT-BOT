"""
Cross-Encoder Reranker
基于 Cross-Encoder 模型的重排序器
"""

import logging
import time
from typing import List, Optional, Tuple
import asyncio

import torch
from sentence_transformers import CrossEncoder

from ..models import RetrievalResult, RerankerConfig, RerankerResult
from ..exceptions import RetrievalError

logger = logging.getLogger(__name__)


class CrossEncoderReranker:
    """
    Cross-Encoder 重排序器

    使用预训练的 Cross-Encoder 模型对检索结果进行重排序，
    提升结果相关性和准确度。
    """

    def __init__(self, config: Optional[RerankerConfig] = None):
        """
        初始化 Cross-Encoder 重排序器

        Args:
            config: 重排序配置
        """
        self.config = config or RerankerConfig()
        self.model: Optional[CrossEncoder] = None
        self._model_loaded = False

        logger.info(f"CrossEncoderReranker initialized with config: {self.config.model_name}")

    def _load_model(self) -> None:
        """加载 Cross-Encoder 模型（延迟加载）"""
        if self._model_loaded:
            return

        try:
            start_time = time.time()
            logger.info(f"Loading Cross-Encoder model: {self.config.model_name}")

            # 确定设备
            device = self._get_device()
            logger.info(f"Using device: {device}")

            # 加载模型
            self.model = CrossEncoder(
                self.config.model_name,
                max_length=self.config.max_length,
                device=device,
            )

            # FP16 优化（仅在 CUDA 上可用）
            if self.config.use_fp16 and device == "cuda":
                logger.info("Enabling FP16 acceleration")
                # Cross-Encoder 会自动使用混合精度

            self._model_loaded = True
            duration = time.time() - start_time
            logger.info(f"Model loaded successfully in {duration:.2f}s")

        except Exception as e:
            logger.error(f"Failed to load Cross-Encoder model: {e}", exc_info=True)
            raise RetrievalError(f"Failed to load reranker model: {e}")

    def _get_device(self) -> str:
        """获取运行设备"""
        if self.config.device:
            return self.config.device

        # 自动检测设备
        if torch.cuda.is_available():
            return "cuda"
        elif torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"

    async def rerank(
        self,
        query: str,
        documents: List[RetrievalResult],
        top_k: Optional[int] = None
    ) -> List[RerankerResult]:
        """
        重排序检索结果

        Args:
            query: 查询文本
            documents: 检索结果列表
            top_k: 返回的结果数量（默认返回全部）

        Returns:
            重排序后的结果列表
        """
        if not documents:
            logger.warning("No documents to rerank")
            return []

        try:
            # 延迟加载模型
            if not self._model_loaded:
                self._load_model()

            start_time = time.time()

            # 批量打分
            scores = await self._batch_score(query, documents)

            # 归一化分数
            if self.config.normalize_scores:
                scores = self._normalize_scores(scores)

            # 构建重排序结果
            reranked_results = self._build_reranker_results(
                documents, scores, top_k
            )

            duration_ms = int((time.time() - start_time) * 1000)
            logger.info(
                f"Reranked {len(documents)} documents in {duration_ms}ms, "
                f"returned top {len(reranked_results)}"
            )

            return reranked_results

        except Exception as e:
            logger.error(f"Reranking failed: {e}", exc_info=True)
            raise RetrievalError(f"Reranking failed: {e}")

    async def _batch_score(
        self,
        query: str,
        documents: List[RetrievalResult]
    ) -> List[float]:
        """
        批量计算相关性分数

        Args:
            query: 查询文本
            documents: 文档列表

        Returns:
            分数列表
        """
        # 构建句子对
        sentence_pairs = [[query, doc.content] for doc in documents]

        # 批量推理
        scores = []
        batch_size = self.config.batch_size

        for i in range(0, len(sentence_pairs), batch_size):
            batch = sentence_pairs[i:i + batch_size]

            # 在线程池中运行 CPU/GPU 密集型操作
            batch_scores = await asyncio.to_thread(
                self.model.predict,
                batch,
                show_progress_bar=False
            )
            scores.extend(batch_scores.tolist())

        return scores

    def _normalize_scores(self, scores: List[float]) -> List[float]:
        """
        归一化分数到 0-1 区间

        使用 sigmoid 函数进行归一化：
        normalized_score = 1 / (1 + exp(-score))

        Args:
            scores: 原始分数列表

        Returns:
            归一化后的分数列表
        """
        import math

        normalized = []
        for score in scores:
            # Sigmoid 归一化
            normalized_score = 1.0 / (1.0 + math.exp(-score))
            normalized.append(normalized_score)

        return normalized

    def _build_reranker_results(
        self,
        documents: List[RetrievalResult],
        scores: List[float],
        top_k: Optional[int] = None
    ) -> List[RerankerResult]:
        """
        构建重排序结果

        Args:
            documents: 原始文档列表
            scores: 重排序分数列表
            top_k: 返回的结果数量

        Returns:
            重排序结果列表
        """
        # 创建 (分数, 原始排名, 文档) 三元组
        scored_docs = [
            (score, idx, doc)
            for idx, (score, doc) in enumerate(zip(scores, documents))
        ]

        # 按重排序分数降序排序
        scored_docs.sort(key=lambda x: x[0], reverse=True)

        # 截取 top_k
        if top_k is not None:
            scored_docs = scored_docs[:top_k]

        # 构建 RerankerResult
        results = []
        for new_rank, (rerank_score, original_rank, doc) in enumerate(scored_docs):
            result = RerankerResult(
                chunk_id=doc.chunk_id,
                parent_id=doc.parent_id,
                content=doc.content,
                metadata=doc.metadata,
                original_score=doc.score,
                rerank_score=rerank_score,
                original_rank=original_rank,
                new_rank=new_rank,
                chunk_index=doc.chunk_index
            )
            results.append(result)

        return results

    def get_model_info(self) -> dict:
        """获取模型信息"""
        return {
            "model_name": self.config.model_name,
            "device": self._get_device(),
            "batch_size": self.config.batch_size,
            "max_length": self.config.max_length,
            "loaded": self._model_loaded
        }


# 全局单例
_reranker: Optional[CrossEncoderReranker] = None


def get_reranker(config: Optional[RerankerConfig] = None) -> CrossEncoderReranker:
    """
    获取 Cross-Encoder 重排序器单例

    Args:
        config: 重排序配置（仅在首次调用时生效）

    Returns:
        CrossEncoderReranker 实例
    """
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoderReranker(config)
    return _reranker
