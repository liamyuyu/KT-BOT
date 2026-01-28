"""
数据同步模块 - 自定义异常

本模块定义同步过程中可能出现的各类异常。
"""


class SyncError(Exception):
    """同步模块基础异常"""

    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class SyncConfigError(SyncError):
    """同步配置错误"""
    pass


class SyncSchedulerError(SyncError):
    """调度器错误"""
    pass


class SyncTaskError(SyncError):
    """同步任务执行错误"""
    pass


class SyncTaskNotFoundError(SyncError):
    """任务不存在"""
    pass


class SyncTaskAlreadyRunningError(SyncError):
    """任务已在运行中"""
    pass


class SyncTaskCancelledError(SyncError):
    """任务已取消"""
    pass


class SyncDataSourceError(SyncError):
    """数据源错误"""
    pass


class SyncRepositoryError(SyncError):
    """数据访问层错误"""
    pass
