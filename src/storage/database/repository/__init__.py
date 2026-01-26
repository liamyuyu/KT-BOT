"""
数据仓库模块

提供数据访问接口。
"""

from .sync_repository import SyncHistoryRepo, SyncConfigRepo

__all__ = [
    "SyncHistoryRepo",
    "SyncConfigRepo",
]
