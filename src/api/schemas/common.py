"""
通用响应模型
"""
from typing import Optional, Any
from pydantic import BaseModel, Field


class SuccessResponse(BaseModel):
    """成功响应"""
    success: bool = Field(default=True, description="是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[Any] = Field(default=None, description="额外数据")


class ErrorResponse(BaseModel):
    """错误响应"""
    success: bool = Field(default=False, description="是否成功")
    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误消息")
    details: Optional[Any] = Field(default=None, description="错误详情")
