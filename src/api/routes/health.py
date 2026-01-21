"""
健康检查路由
"""
import logging
from fastapi import APIRouter
from datetime import datetime
from dataclasses import asdict

from ..schemas.common import SuccessResponse
from src.core.llm.health import get_health_checker

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=SuccessResponse)
async def health_check():
    """
    基础健康检查端点（快速响应）
    """
    return SuccessResponse(
        success=True,
        message="API is healthy",
        data={
            "timestamp": datetime.now().isoformat(),
            "status": "running"
        }
    )


@router.get("/full", response_model=SuccessResponse)
async def full_health_check():
    """
    完整健康检查（包含模型状态）
    检查 Ollama 服务、LLM 模型、Embedding 模型的健康状态
    """
    checker = get_health_checker()

    # 检查所有组件
    health_results = await checker.check_all()
    overall_status = checker.get_overall_status(health_results)

    # 转换为字典
    details = {
        name: asdict(status)
        for name, status in health_results.items()
    }

    return SuccessResponse(
        success=(overall_status != "unhealthy"),
        message=f"System status: {overall_status}",
        data={
            "timestamp": datetime.now().isoformat(),
            "overall_status": overall_status,
            "components": details
        }
    )
