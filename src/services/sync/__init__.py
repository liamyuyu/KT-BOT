"""
数据同步服务模块

提供 Jira 和 Confluence 数据的自动同步和调度功能。

主要功能：
- 定时自动同步（支持 Cron 表达式和时间间隔）
- 增量同步（只同步变更数据）
- 全量同步（同步所有数据）
- 任务调度和管理
- 同步历史记录
- 统计信息查询

使用示例：
    from src.services.sync import get_sync_scheduler

    # 获取调度器实例
    scheduler = get_sync_scheduler()

    # 启动调度器
    await scheduler.start()

    # 手动触发同步
    task_id = await scheduler.trigger_sync(source="jira", sync_type="incremental")

    # 停止调度器
    await scheduler.shutdown()
"""

from .models import (
    # 枚举
    SyncSource,
    SyncStatus,
    SyncType,
    ScheduleType,

    # 配置
    SyncConfig,
    SyncConfigUpdate,

    # 任务
    SyncTask,
    SyncTaskCreate,
    SyncTaskUpdate,

    # 历史
    SyncHistory,

    # 统计
    SyncStats,
    SyncStatsOverall,

    # 响应
    SyncResponse,
    SyncHistoryListResponse,
)

from .exceptions import (
    SyncError,
    SyncConfigError,
    SyncSchedulerError,
    SyncTaskError,
    SyncTaskNotFoundError,
    SyncTaskAlreadyRunningError,
    SyncTaskCancelledError,
    SyncDataSourceError,
    SyncRepositoryError,
)

# 调度器单例（将在 scheduler.py 中实现）
_scheduler_instance = None


def get_sync_scheduler():
    """
    获取同步调度器单例

    Returns:
        SyncScheduler: 调度器实例
    """
    global _scheduler_instance
    if _scheduler_instance is None:
        from .scheduler import SyncScheduler
        _scheduler_instance = SyncScheduler()
    return _scheduler_instance


__all__ = [
    # 枚举
    "SyncSource",
    "SyncStatus",
    "SyncType",
    "ScheduleType",

    # 配置
    "SyncConfig",
    "SyncConfigUpdate",

    # 任务
    "SyncTask",
    "SyncTaskCreate",
    "SyncTaskUpdate",

    # 历史
    "SyncHistory",

    # 统计
    "SyncStats",
    "SyncStatsOverall",

    # 响应
    "SyncResponse",
    "SyncHistoryListResponse",

    # 异常
    "SyncError",
    "SyncConfigError",
    "SyncSchedulerError",
    "SyncTaskError",
    "SyncTaskNotFoundError",
    "SyncTaskAlreadyRunningError",
    "SyncTaskCancelledError",
    "SyncDataSourceError",
    "SyncRepositoryError",

    # 工具函数
    "get_sync_scheduler",
]
