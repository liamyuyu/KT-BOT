"""
健康检查路由
"""
import logging
from fastapi import APIRouter
from datetime import datetime

from ..schemas.common import SuccessResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=SuccessResponse)
async def health_check():
    """
    健康检查端点
    """
    return SuccessResponse(
        success=True,
        message="API is healthy",
        data={
            "timestamp": datetime.now().isoformat(),
            "status": "running"
        }
    )
