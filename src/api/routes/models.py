"""
模型管理路由
"""
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.core.llm.manager import get_llm_manager
from src.constants import SUPPORTED_LLM_MODELS, SUPPORTED_EMBEDDING_MODELS

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/models", tags=["models"])


# ============ 请求模型 ============

class SwitchLLMRequest(BaseModel):
    """切换 LLM 模型请求"""
    model_name: str


class SwitchEmbeddingRequest(BaseModel):
    """切换 Embedding 模型请求"""
    model_name: str


@router.get("/list")
async def list_models() -> Dict[str, Any]:
    """
    获取支持的模型列表和当前模型
    """
    manager = get_llm_manager()

    return {
        "data": {
            "models": {
                "llm": SUPPORTED_LLM_MODELS,
                "embedding": SUPPORTED_EMBEDDING_MODELS
            },
            "current": {
                "llm": manager.get_current_llm_model(),
                "embedding": manager.get_current_embedding_model()
            }
        },
        "message": "Models listed successfully"
    }


@router.get("/status")
async def get_model_status() -> Dict[str, Any]:
    """
    获取当前模型状态（包括健康检查）
    """
    manager = get_llm_manager()

    # 获取当前已加载的模型
    llm_models = list(manager._llm_cache.keys()) if hasattr(manager, '_llm_cache') else []
    embedding_models = list(manager._embedding_cache.keys()) if hasattr(manager, '_embedding_cache') else []

    # 获取当前激活的模型
    current_llm = manager.get_current_llm_model()
    current_embedding = manager.get_current_embedding_model()

    # 执行健康检查
    health_status = {}
    try:
        if current_llm:
            health_status["llm"] = await manager.check_model_health(current_llm, "llm")
        if current_embedding:
            health_status["embedding"] = await manager.check_model_health(current_embedding, "embedding")
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        health_status["error"] = str(e)

    return {
        "data": {
            "current_models": {
                "llm": current_llm,
                "embedding": current_embedding
            },
            "loaded_models": {
                "llm": llm_models,
                "embedding": embedding_models
            },
            "health": health_status,
            "cache_size": {
                "llm": len(llm_models),
                "embedding": len(embedding_models)
            }
        },
        "message": "Model status retrieved successfully"
    }


@router.post("/switch-llm")
async def switch_llm_model(request: SwitchLLMRequest) -> Dict[str, Any]:
    """
    切换 LLM 对话模型

    Args:
        request: 切换请求，包含目标模型名称

    Returns:
        切换结果和新模型信息
    """
    manager = get_llm_manager()

    try:
        # 检查模型是否支持
        if request.model_name not in SUPPORTED_LLM_MODELS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported model: {request.model_name}. "
                       f"Supported models: {SUPPORTED_LLM_MODELS}"
            )

        # 切换模型
        llm = manager.switch_llm_model(request.model_name)

        # 健康检查
        is_healthy = await manager.check_model_health(request.model_name, "llm")

        logger.info(f"LLM model switched to {request.model_name}")

        return {
            "data": {
                "model_name": request.model_name,
                "model_type": "llm",
                "status": "healthy" if is_healthy else "unhealthy",
                "previous_model": manager.get_current_llm_model()
            },
            "message": f"LLM model switched to {request.model_name} successfully"
        }

    except ValueError as e:
        logger.error(f"Invalid model switch request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to switch LLM model: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to switch model: {str(e)}")


@router.post("/switch-embedding")
async def switch_embedding_model(request: SwitchEmbeddingRequest) -> Dict[str, Any]:
    """
    切换 Embedding 模型

    ⚠️ 警告：切换 Embedding 模型需要重建向量索引，否则检索结果可能不准确

    Args:
        request: 切换请求，包含目标模型名称

    Returns:
        切换结果和警告信息
    """
    manager = get_llm_manager()

    try:
        # 检查模型是否支持
        if request.model_name not in SUPPORTED_EMBEDDING_MODELS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported embedding model: {request.model_name}. "
                       f"Supported models: {SUPPORTED_EMBEDDING_MODELS}"
            )

        previous_model = manager.get_current_embedding_model()

        # 切换模型
        embedding = manager.switch_embedding_model(request.model_name)

        # 健康检查
        is_healthy = await manager.check_model_health(request.model_name, "embedding")

        logger.info(f"Embedding model switched to {request.model_name}")

        return {
            "data": {
                "model_name": request.model_name,
                "model_type": "embedding",
                "status": "healthy" if is_healthy else "unhealthy",
                "previous_model": previous_model,
                "warning": "Switching embedding model requires rebuilding the vector index. "
                           "Please rebuild your indexes or search results may be inaccurate."
            },
            "message": f"Embedding model switched to {request.model_name}. "
                      f"⚠️ Index rebuild required!"
        }

    except ValueError as e:
        logger.error(f"Invalid embedding model switch request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to switch embedding model: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to switch model: {str(e)}")
