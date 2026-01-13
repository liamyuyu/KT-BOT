"""
模型管理路由
"""
import logging
from typing import List, Dict, Any
from fastapi import APIRouter

from src.core.llm.manager import get_llm_manager
from src.constants import SUPPORTED_LLM_MODELS, SUPPORTED_EMBEDDING_MODELS

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/models", tags=["models"])


@router.get("/list")
async def list_models() -> Dict[str, Any]:
    """
    获取支持的模型列表
    """
    return {
        "llm_models": SUPPORTED_LLM_MODELS,
        "embedding_models": SUPPORTED_EMBEDDING_MODELS
    }


@router.get("/status")
async def get_model_status() -> Dict[str, Any]:
    """
    获取当前模型状态
    """
    manager = get_llm_manager()

    # 获取当前已加载的模型
    llm_models = list(manager._llm_cache.keys()) if hasattr(manager, '_llm_cache') else []
    embedding_models = list(manager._embedding_cache.keys()) if hasattr(manager, '_embedding_cache') else []

    return {
        "loaded_llm_models": llm_models,
        "loaded_embedding_models": embedding_models,
        "total_llm_models": len(llm_models),
        "total_embedding_models": len(embedding_models)
    }
