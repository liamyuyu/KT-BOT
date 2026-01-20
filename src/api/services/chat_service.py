"""
对话服务 - 核心业务逻辑
职责：协调 LLM、RAG、会话管理
"""
import logging
import time
import uuid
import hashlib
from typing import Optional, List, AsyncIterator, Dict, Any, Union, Tuple

from src.core.llm.manager import get_llm_manager, LLMManager
from src.core.llm.base import Message
from src.core.rag.retriever.vector import get_vector_retriever, VectorRetriever
from src.core.rag.retriever.bm25 import get_bm25_retriever, BM25Retriever
from src.core.rag.retriever.hybrid import get_hybrid_retriever, HybridRetriever
from src.core.rag import RetrievalConfig, BM25Config, HybridConfig, RetrievalResult
from src.core.rag import CrossEncoderReranker, get_reranker, RerankerConfig
from ..schemas.chat import (
    ChatRequest, ChatResponse, ChatMessage,
    RetrievedContext, StreamChunk, ChatHistory
)
from .session_manager import get_session_manager, SessionManager

logger = logging.getLogger(__name__)


class ChatService:
    """对话服务"""

    def __init__(
        self,
        llm_manager: Optional[LLMManager] = None,
        vector_retriever: Optional[VectorRetriever] = None,
        bm25_retriever: Optional[BM25Retriever] = None,
        hybrid_retriever: Optional[HybridRetriever] = None,
        session_manager: Optional[SessionManager] = None,
        reranker: Optional[CrossEncoderReranker] = None
    ):
        self.llm_manager = llm_manager or get_llm_manager()
        self.session_manager = session_manager or get_session_manager()

        # 初始化三种检索器
        self.vector_retriever = vector_retriever or get_vector_retriever()
        self.bm25_retriever = bm25_retriever or get_bm25_retriever()

        # 混合检索器（需要向量和 BM25 检索器）
        if hybrid_retriever:
            self.hybrid_retriever = hybrid_retriever
        else:
            try:
                self.hybrid_retriever = get_hybrid_retriever(
                    vector_retriever=self.vector_retriever,
                    bm25_retriever=self.bm25_retriever,
                    retrieval_config=RetrievalConfig(top_k=10),
                    hybrid_config=HybridConfig(fusion_method="rrf")
                )
            except Exception as e:
                logger.warning(f"Failed to initialize HybridRetriever: {e}")
                self.hybrid_retriever = None

        # 重排序器（Cross-Encoder）
        if reranker:
            self.reranker = reranker
        else:
            try:
                self.reranker = get_reranker(
                    config=RerankerConfig(
                        model_name="BAAI/bge-reranker-large",
                        batch_size=4,
                        normalize_scores=True
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to initialize Reranker: {e}")
                self.reranker = None

        # 重排序结果缓存
        self._rerank_cache: Dict[str, Tuple[List[RetrievedContext], float]] = {}
        self._rerank_cache_size = 64  # 缓存大小
        self._rerank_cache_ttl = 600.0  # 缓存有效期 10 分钟

        logger.info("ChatService initialized with vector, BM25, hybrid retrievers and reranker")

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """非流式对话"""
        start_time = time.time()

        # 1. 获取或创建会话
        session_id = request.session_id or str(uuid.uuid4())
        logger.info(f"Processing chat request for session {session_id}")

        # 2. RAG 检索（如果启用）
        retrieved_contexts = None
        enhanced_prompt = request.message

        if request.enable_rag:
            logger.debug(
                f"RAG enabled with method={request.retrieval_method}, "
                f"retrieving top {request.rag_top_k} contexts, "
                f"reranking={'enabled' if request.enable_reranking else 'disabled'}"
            )
            contexts = await self._retrieve_contexts(
                query=request.message,
                top_k=request.rag_top_k,
                retrieval_method=request.retrieval_method,
                vector_weight=request.vector_weight,
                bm25_weight=request.bm25_weight,
                fusion_method=request.fusion_method,
                enable_reranking=request.enable_reranking,
                rerank_top_k=request.rerank_top_k
            )
            if contexts:
                retrieved_contexts = contexts
                enhanced_prompt = self._build_rag_prompt(
                    request.message,
                    contexts
                )
                logger.info(f"RAG retrieved {len(contexts)} contexts")
            else:
                logger.warning("RAG retrieval returned no contexts")

        # 3. 获取历史消息
        history_messages = await self.session_manager.get_messages(session_id)
        logger.debug(f"Loaded {len(history_messages)} messages from session history")

        # 4. 构建对话上下文
        messages = self._build_chat_messages(
            history_messages,
            enhanced_prompt
        )

        # 5. LLM 生成
        llm = self.llm_manager.create_llm(request.model_name)
        logger.debug(f"Using LLM model: {llm.model_name}")

        response = await llm.chat(
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )

        logger.info(f"LLM generated response: {len(response.content)} chars, {response.eval_count} tokens")

        # 6. 保存对话历史
        await self.session_manager.add_message(
            session_id,
            ChatMessage(role="user", content=request.message)
        )
        await self.session_manager.add_message(
            session_id,
            ChatMessage(role="assistant", content=response.content)
        )

        # 7. 构建响应
        duration_ms = int((time.time() - start_time) * 1000)

        return ChatResponse(
            session_id=session_id,
            message=response.content,
            model=response.model,
            rag_enabled=request.enable_rag,
            retrieved_contexts=retrieved_contexts,
            token_count=response.eval_count,
            duration_ms=duration_ms
        )

    async def chat_stream(
        self,
        request: ChatRequest
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        流式对话（SSE）

        事件流格式：
        - event: start - 开始生成
        - event: context - RAG 检索结果（可选）
        - event: token - 生成的文本片段
        - event: end - 生成结束
        - event: error - 错误信息
        """
        start_time = time.time()
        session_id = None

        try:
            # 1. 获取或创建会话
            session_id = request.session_id or str(uuid.uuid4())
            logger.info(f"Processing streaming chat request for session {session_id}")

            # 发送开始事件
            yield {
                "event": "start",
                "data": {
                    "session_id": session_id,
                    "timestamp": time.time()
                }
            }

            # 2. RAG 检索（如果启用）
            retrieved_contexts = None
            enhanced_prompt = request.message

            if request.enable_rag:
                logger.debug(
                    f"RAG enabled with method={request.retrieval_method}, "
                    f"retrieving top {request.rag_top_k} contexts, "
                    f"reranking={'enabled' if request.enable_reranking else 'disabled'}"
                )
                contexts = await self._retrieve_contexts(
                    query=request.message,
                    top_k=request.rag_top_k,
                    retrieval_method=request.retrieval_method,
                    vector_weight=request.vector_weight,
                    bm25_weight=request.bm25_weight,
                    fusion_method=request.fusion_method,
                    enable_reranking=request.enable_reranking,
                    rerank_top_k=request.rerank_top_k
                )
                if contexts:
                    retrieved_contexts = contexts
                    enhanced_prompt = self._build_rag_prompt(
                        request.message,
                        contexts
                    )
                    logger.info(f"RAG retrieved {len(contexts)} contexts")

                    # 发送上下文事件
                    yield {
                        "event": "context",
                        "data": {
                            "contexts": [
                                {
                                    "chunk_id": ctx.chunk_id,
                                    "content": ctx.content[:200],  # 截断显示
                                    "score": ctx.score,
                                    "source": ctx.source
                                }
                                for ctx in contexts
                            ]
                        }
                    }
                else:
                    logger.warning("RAG retrieval returned no contexts")

            # 3. 获取历史消息
            history_messages = await self.session_manager.get_messages(session_id)
            logger.debug(f"Loaded {len(history_messages)} messages from session history")

            # 4. 构建对话上下文
            messages = self._build_chat_messages(
                history_messages,
                enhanced_prompt
            )

            # 5. LLM 流式生成
            llm = self.llm_manager.create_llm(request.model_name)
            logger.debug(f"Using LLM model: {llm.model_name}")

            full_response = ""
            token_count = 0

            async for chunk in llm.chat_stream(
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            ):
                full_response += chunk.content
                token_count = chunk.eval_count or token_count

                # 发送 token 事件
                yield {
                    "event": "token",
                    "data": {
                        "content": chunk.content
                    }
                }

            logger.info(f"LLM generated streaming response: {len(full_response)} chars, {token_count} tokens")

            # 6. 保存对话历史
            await self.session_manager.add_message(
                session_id,
                ChatMessage(role="user", content=request.message)
            )
            await self.session_manager.add_message(
                session_id,
                ChatMessage(role="assistant", content=full_response)
            )

            # 7. 发送结束事件
            duration_ms = int((time.time() - start_time) * 1000)

            yield {
                "event": "end",
                "data": {
                    "session_id": session_id,
                    "model": llm.model_name,
                    "token_count": token_count,
                    "duration_ms": duration_ms,
                    "rag_enabled": request.enable_rag
                }
            }

        except Exception as e:
            logger.error(f"Streaming chat error: {e}", exc_info=True)
            yield {
                "event": "error",
                "data": {
                    "message": str(e),
                    "session_id": session_id
                }
            }

    async def _retrieve_contexts(
        self,
        query: str,
        top_k: int,
        retrieval_method: str = "hybrid",
        vector_weight: float = 0.5,
        bm25_weight: float = 0.5,
        fusion_method: str = "rrf",
        enable_reranking: bool = True,
        rerank_top_k: int = 10
    ) -> List[RetrievedContext]:
        """
        RAG 检索上下文（支持多种检索策略和重排序）

        Args:
            query: 查询文本
            top_k: 最终返回结果数量
            retrieval_method: 检索方法（vector/bm25/hybrid）
            vector_weight: 向量检索权重
            bm25_weight: BM25 检索权重
            fusion_method: 融合方法（rrf/weighted/linear）
            enable_reranking: 是否启用重排序
            rerank_top_k: 重排序前的候选数量

        Returns:
            检索到的上下文列表
        """
        try:
            # 确定检索数量：如果启用重排序，先获取更多候选
            retrieve_k = rerank_top_k if enable_reranking else top_k

            # 根据检索方法选择检索器
            if retrieval_method == "vector":
                logger.debug("Using vector retriever")
                results = await self.vector_retriever.retrieve(query, top_k=retrieve_k)

            elif retrieval_method == "bm25":
                logger.debug("Using BM25 retriever")
                results = await self.bm25_retriever.retrieve(query, top_k=retrieve_k)

            elif retrieval_method == "hybrid":
                if self.hybrid_retriever is None:
                    logger.warning("HybridRetriever not available, falling back to vector retriever")
                    results = await self.vector_retriever.retrieve(query, top_k=retrieve_k)
                else:
                    logger.debug(
                        f"Using hybrid retriever with fusion_method={fusion_method}, "
                        f"weights=({vector_weight:.2f}, {bm25_weight:.2f})"
                    )

                    # 动态更新混合检索配置
                    self.hybrid_retriever.hybrid_config.fusion_method = fusion_method
                    self.hybrid_retriever.hybrid_config.vector_weight = vector_weight
                    self.hybrid_retriever.hybrid_config.bm25_weight = bm25_weight

                    results = await self.hybrid_retriever.retrieve(query, top_k=retrieve_k)

            else:
                logger.warning(f"Unknown retrieval_method: {retrieval_method}, using vector")
                results = await self.vector_retriever.retrieve(query, top_k=retrieve_k)

            logger.info(
                f"Retrieved {len(results)} candidates using {retrieval_method} method"
            )

            # 应用重排序（如果启用）
            if enable_reranking and self.reranker is not None and results:
                # 检查重排序缓存
                cache_key = self._get_rerank_cache_key(
                    query, retrieval_method, top_k, rerank_top_k
                )
                cached_contexts = self._get_from_rerank_cache(cache_key)

                if cached_contexts is not None:
                    logger.info(f"Returning {len(cached_contexts)} cached reranked results")
                    return cached_contexts

                logger.debug(f"Applying reranking to {len(results)} candidates")
                rerank_start = time.time()

                # 使用 Reranker 重排序
                reranked_results = await self.reranker.rerank(
                    query=query,
                    documents=results,
                    top_k=top_k
                )

                rerank_time = time.time() - rerank_start
                logger.info(
                    f"Reranking completed: {len(reranked_results)} results, "
                    f"time={rerank_time:.3f}s"
                )

                # 构建带重排序信息的上下文列表
                contexts = [
                    RetrievedContext(
                        chunk_id=r.chunk_id,
                        content=r.content,
                        score=r.rerank_score,  # 使用重排序分数
                        source={
                            "issue_key": r.metadata.get("issue_key", ""),
                            "project_key": r.metadata.get("project_key", ""),
                            "issue_type": r.metadata.get("issue_type", ""),
                            "url": r.metadata.get("url", "")
                        },
                        retrieval_method=retrieval_method,
                        distance=1.0 - r.rerank_score,  # 转换为距离
                        rerank_score=r.rerank_score,
                        original_rank=r.original_rank,
                        reranked=True
                    )
                    for r in reranked_results
                ]

                # 添加到缓存
                self._add_to_rerank_cache(cache_key, contexts)

            else:
                # 不使用重排序，直接构建上下文列表
                if enable_reranking:
                    logger.warning("Reranking requested but reranker not available")

                contexts = [
                    RetrievedContext(
                        chunk_id=r.chunk_id,
                        content=r.content,
                        score=r.score,
                        source={
                            "issue_key": r.metadata.get("issue_key", ""),
                            "project_key": r.metadata.get("project_key", ""),
                            "issue_type": r.metadata.get("issue_type", ""),
                            "url": r.metadata.get("url", "")
                        },
                        retrieval_method=retrieval_method,
                        distance=r.distance,
                        reranked=False
                    )
                    for r in results[:top_k]  # 只取前 top_k
                ]

            logger.info(
                f"Returning {len(contexts)} contexts "
                f"(reranked={enable_reranking and self.reranker is not None})"
            )

            return contexts

        except Exception as e:
            logger.error(f"RAG retrieval error: {e}", exc_info=True)
            return []

    def _build_rag_prompt(
        self,
        query: str,
        contexts: List[RetrievedContext]
    ) -> str:
        """构建 RAG 增强提示词"""
        if not contexts:
            return query

        context_str = "\n\n".join([
            f"[文档 {i+1} - {ctx.source.get('issue_key', 'Unknown')}]\n{ctx.content}"
            for i, ctx in enumerate(contexts)
        ])

        return f"""请基于以下相关文档回答用户问题。如果文档中没有相关信息，请说明"根据现有知识库，我没有找到相关信息"。

相关文档：
{context_str}

用户问题：{query}

请提供准确、简洁的回答，并在回答末尾注明引用的文档来源（如 [文档1], [文档2]）。"""

    def _build_chat_messages(
        self,
        history: List[ChatMessage],
        current_prompt: str
    ) -> List[Message]:
        """构建对话消息列表"""
        messages = []

        # 系统消息
        messages.append(Message(
            role="system",
            content="你是 KT-BOT，一个基于企业知识库的智能助手。请基于提供的上下文准确回答问题。"
        ))

        # 历史消息（限制最近 10 轮，即 20 条消息）
        recent_history = history[-20:] if len(history) > 20 else history
        for msg in recent_history:
            messages.append(Message(
                role=msg.role,
                content=msg.content
            ))

        # 当前用户消息
        messages.append(Message(role="user", content=current_prompt))

        return messages

    async def get_history(self, session_id: str) -> Optional[ChatHistory]:
        """获取历史记录"""
        return await self.session_manager.get_history(session_id)

    async def clear_history(self, session_id: str) -> None:
        """清空历史记录"""
        await self.session_manager.clear_history(session_id)

    def _get_rerank_cache_key(
        self,
        query: str,
        retrieval_method: str,
        top_k: int,
        rerank_top_k: int
    ) -> str:
        """生成重排序缓存键"""
        cache_str = f"{query}|{retrieval_method}|{top_k}|{rerank_top_k}"
        return hashlib.md5(cache_str.encode()).hexdigest()

    def _get_from_rerank_cache(self, cache_key: str) -> Optional[List[RetrievedContext]]:
        """从重排序缓存获取结果"""
        if cache_key in self._rerank_cache:
            contexts, timestamp = self._rerank_cache[cache_key]
            # 检查是否过期
            if time.time() - timestamp < self._rerank_cache_ttl:
                logger.debug(f"Rerank cache hit for key: {cache_key}")
                return contexts
            else:
                # 过期，删除缓存
                del self._rerank_cache[cache_key]
                logger.debug(f"Rerank cache expired for key: {cache_key}")
        return None

    def _add_to_rerank_cache(self, cache_key: str, contexts: List[RetrievedContext]) -> None:
        """添加结果到重排序缓存"""
        # LRU 策略：如果缓存已满，删除最旧的条目
        if len(self._rerank_cache) >= self._rerank_cache_size:
            oldest_key = min(self._rerank_cache.keys(), key=lambda k: self._rerank_cache[k][1])
            del self._rerank_cache[oldest_key]
            logger.debug(f"Rerank cache full, evicted key: {oldest_key}")

        self._rerank_cache[cache_key] = (contexts, time.time())
        logger.debug(f"Added to rerank cache, key: {cache_key}, size: {len(self._rerank_cache)}")


# 全局单例
_chat_service: Optional[ChatService] = None


def get_chat_service() -> ChatService:
    """获取对话服务单例"""
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service
