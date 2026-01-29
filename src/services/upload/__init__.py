"""
Upload Service Package
上传服务包
"""

from .models import (
    UploadStatus, UploadTask, UploadProgress,
    FileInfo, BatchUploadRequest, BatchUploadResponse,
    UploadTaskResponse
)
from .exceptions import (
    UploadException, ValidationError, ParsingError,
    IndexingError, TaskNotFoundException, TaskCancelledException
)
from .manager import UploadManager


# 全局单例
_upload_manager: UploadManager = None


def get_upload_manager(
    max_concurrent: int = 3,
    max_file_size: int = 50 * 1024 * 1024,
    use_db: bool = False
) -> UploadManager:
    """
    获取全局上传管理器单例

    Args:
        max_concurrent: 最大并发数
        max_file_size: 最大文件大小
        use_db: 是否使用数据库持久化

    Returns:
        UploadManager: 上传管理器实例
    """
    global _upload_manager

    if _upload_manager is None:
        _upload_manager = UploadManager(
            max_concurrent=max_concurrent,
            max_file_size=max_file_size,
            use_db=use_db
        )

    return _upload_manager


__all__ = [
    # Models
    "UploadStatus",
    "UploadTask",
    "UploadProgress",
    "FileInfo",
    "BatchUploadRequest",
    "BatchUploadResponse",
    "UploadTaskResponse",
    # Exceptions
    "UploadException",
    "ValidationError",
    "ParsingError",
    "IndexingError",
    "TaskNotFoundException",
    "TaskCancelledException",
    # Manager
    "UploadManager",
    "get_upload_manager",
]
