"""
Upload Service Models
上传服务数据模型
"""

from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class UploadStatus(str, Enum):
    """上传状态枚举"""
    PENDING = "pending"
    VALIDATING = "validating"
    PARSING = "parsing"
    INDEXING = "indexing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FileInfo(BaseModel):
    """文件信息"""
    file_name: str = Field(..., description="文件名")
    file_size: int = Field(..., description="文件大小（字节）")
    file_type: str = Field(..., description="文件类型（扩展名）")
    mime_type: Optional[str] = Field(None, description="MIME 类型")


class UploadTask(BaseModel):
    """上传任务模型"""
    task_id: str = Field(..., description="任务 ID")
    batch_id: str = Field(..., description="批次 ID")
    user_id: str = Field(..., description="用户 ID")
    file_info: FileInfo = Field(..., description="文件信息")
    status: UploadStatus = Field(default=UploadStatus.PENDING, description="任务状态")
    progress_percentage: float = Field(default=0.0, ge=0.0, le=100.0, description="进度百分比")
    document_id: Optional[str] = Field(None, description="文档 ID（索引完成后）")
    error_message: Optional[str] = Field(None, description="错误信息")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UploadProgress(BaseModel):
    """上传进度模型（用于 SSE 推送）"""
    task_id: str = Field(..., description="任务 ID")
    status: UploadStatus = Field(..., description="当前状态")
    progress: float = Field(..., ge=0.0, le=100.0, description="进度百分比")
    message: str = Field(..., description="进度消息")
    current_step: str = Field(..., description="当前步骤")


class BatchUploadRequest(BaseModel):
    """批量上传请求"""
    user_id: str = Field(..., description="用户 ID")
    tags: Optional[List[str]] = Field(None, description="文档标签")


class BatchUploadResponse(BaseModel):
    """批量上传响应"""
    batch_id: str = Field(..., description="批次 ID")
    total_files: int = Field(..., description="总文件数")
    accepted_files: int = Field(..., description="接受的文件数")
    rejected_files: List[Dict[str, str]] = Field(default_factory=list, description="拒绝的文件列表")
    task_ids: List[str] = Field(default_factory=list, description="任务 ID 列表")


class UploadTaskResponse(BaseModel):
    """上传任务响应"""
    task_id: str = Field(..., description="任务 ID")
    batch_id: str = Field(..., description="批次 ID")
    file_name: str = Field(..., description="文件名")
    file_size: int = Field(..., description="文件大小")
    status: str = Field(..., description="任务状态")
    progress_percentage: float = Field(..., description="进度百分比")
    document_id: Optional[str] = Field(None, description="文档 ID")
    error_message: Optional[str] = Field(None, description="错误信息")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
