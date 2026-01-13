"""
对话服务 - 核心业务逻辑
职责：协调 LLM、RAG、会话管理
"""
import logging
import time
import uuid
from typing import Optional, List, AsyncIterator, Dict, Any

from src.core.llm.manager import get_llm_manager, LLMManager
from src.core.llm.base import Message
from src.core.rag.retriever.vector import get_vector_retriever, VectorRetriever
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
        retriever: Optional[VectorRetriever] = None,
        session_manager: Optional[SessionManager] = None
    ):
        self.llm_manager = llm_manager or get_llm_manager()
        self.retriever = retriever or get_vector_retriever()
        self.session_manager = session_manager or get_session_manager()

        logger.info("ChatService initialized")

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
            logger.debug(f"RAG enabled, retrieving top {request.rag_top_k} contexts")
            contexts = await self._retrieve_contexts(
                request.message,
                request.rag_top_k
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
                logger.debug(f"RAG enabled, retrieving top {request.rag_top_k} contexts")
                contexts = await self._retrieve_contexts(
                    request.message,
                    request.rag_top_k
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
        top_k: int
    ) -> List[RetrievedContext]:
        """RAG 检索上下文"""
        try:
            results = await self.retriever.retrieve(query, top_k=top_k)

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
                    }
                )
                for r in results
            ]

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


# 全局单例
_chat_service: Optional[ChatService] = None


def get_chat_service() -> ChatService:
    """获取对话服务单例"""
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service
