"""
Upload API Schemas
上传 API 数据模型
"""

from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class BatchUploadRequest(BaseModel):
    """批量上传请求"""
    user_id: str = Field(..., description="用户 ID")
    tags: Optional[List[str]] = Field(None, description="文档标签")


class FileRejection(BaseModel):
    """拒绝的文件信息"""
    file_name: str = Field(..., description="文件名")
    reason: str = Field(..., description="拒绝原因")


class BatchUploadResponse(BaseModel):
    """批量上传响应"""
    batch_id: str = Field(..., description="批次 ID")
    total_files: int = Field(..., description="总文件数")
    accepted_files: int = Field(..., description="接受的文件数")
    rejected_files: List[FileRejection] = Field(default_factory=list, description="拒绝的文件列表")
    task_ids: List[str] = Field(default_factory=list, description="任务 ID 列表")


class UploadTaskResponse(BaseModel):
    """上传任务响应"""
    task_id: str = Field(..., description="任务 ID")
    batch_id: str = Field(..., description="批次 ID")
    file_name: str = Field(..., description="文件名")
    file_size: int = Field(..., description="文件大小（字节）")
    status: str = Field(..., description="任务状态")
    progress_percentage: float = Field(..., description="进度百分比")
    document_id: Optional[str] = Field(None, description="文档 ID（完成后）")
    error_message: Optional[str] = Field(None, description="错误信息")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UploadProgressEvent(BaseModel):
    """上传进度事件（SSE）"""
    task_id: str = Field(..., description="任务 ID")
    status: str = Field(..., description="当前状态")
    progress: float = Field(..., description="进度百分比")
    message: str = Field(..., description="进度消息")
    current_step: str = Field(..., description="当前步骤")


class TaskCancelResponse(BaseModel):
    """任务取消响应"""
    task_id: str = Field(..., description="任务 ID")
    message: str = Field(..., description="响应消息")
    success: bool = Field(..., description="是否成功")
