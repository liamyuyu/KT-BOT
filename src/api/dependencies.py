"""
FastAPI 依赖注入
"""
from typing import Optional
from fastapi import Header, HTTPException

from src.core.llm.manager import get_llm_manager, LLMManager
from src.core.rag.retriever.vector import get_vector_retriever, VectorRetriever


def get_current_session_id(
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
) -> Optional[str]:
    """
    从请求头获取会话 ID
    """
    return x_session_id


def get_llm_manager_dependency() -> LLMManager:
    """
    获取 LLM 管理器依赖
    """
    return get_llm_manager()


def get_retriever_dependency() -> VectorRetriever:
    """
    获取向量检索器依赖
    """
    return get_vector_retriever()
