"""
数据同步模块 - 数据模型定义

本模块定义同步任务、同步配置和同步历史的数据模型。
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# 枚举类型
# ============================================================================

class SyncSource(str, Enum):
    """同步数据源"""
    JIRA = "jira"
    CONFLUENCE = "confluence"


class SyncStatus(str, Enum):
    """同步状态"""
    PENDING = "pending"          # 等待中
    RUNNING = "running"          # 运行中
    COMPLETED = "completed"      # 已完成
    FAILED = "failed"            # 失败
    CANCELLED = "cancelled"      # 已取消


class SyncType(str, Enum):
    """同步类型"""
    FULL = "full"                # 全量同步
    INCREMENTAL = "incremental"  # 增量同步


class ScheduleType(str, Enum):
    """调度类型"""
    CRON = "cron"                # Cron 表达式
    INTERVAL = "interval"        # 时间间隔（秒）


# ============================================================================
# 配置模型
# ============================================================================

class SyncConfig(BaseModel):
    """同步配置模型"""

    model_config = ConfigDict(protected_namespaces=())

    source: SyncSource = Field(..., description="数据源")
    enabled: bool = Field(default=False, description="是否启用自动同步")
    schedule_type: ScheduleType = Field(default=ScheduleType.INTERVAL, description="调度类型")
    schedule_value: str = Field(..., description="调度值（cron 表达式或秒数）")
    incremental: bool = Field(default=True, description="是否增量同步")
    batch_size: int = Field(default=50, ge=1, le=200, description="批量处理大小")
    retry_attempts: int = Field(default=3, ge=0, le=10, description="重试次数")
    retry_delay: int = Field(default=60, ge=0, description="重试延迟（秒）")

    # 可选配置
    last_sync_time: Optional[datetime] = Field(None, description="上次同步时间")
    extra_params: Optional[Dict[str, Any]] = Field(None, description="额外参数")


class SyncConfigUpdate(BaseModel):
    """同步配置更新模型（所有字段可选）"""

    model_config = ConfigDict(protected_namespaces=())

    enabled: Optional[bool] = None
    schedule_type: Optional[ScheduleType] = None
    schedule_value: Optional[str] = None
    incremental: Optional[bool] = None
    batch_size: Optional[int] = Field(None, ge=1, le=200)
    retry_attempts: Optional[int] = Field(None, ge=0, le=10)
    retry_delay: Optional[int] = Field(None, ge=0)
    extra_params: Optional[Dict[str, Any]] = None


# ============================================================================
# 任务模型
# ============================================================================

class SyncTask(BaseModel):
    """同步任务模型"""

    model_config = ConfigDict(protected_namespaces=())

    task_id: str = Field(..., description="任务唯一ID")
    source: SyncSource = Field(..., description="数据源")
    sync_type: SyncType = Field(..., description="同步类型")
    status: SyncStatus = Field(default=SyncStatus.PENDING, description="任务状态")

    # 时间信息
    start_time: datetime = Field(default_factory=datetime.now, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    duration_seconds: Optional[int] = Field(None, description="执行时长（秒）")

    # 统计信息
    total_items: int = Field(default=0, description="总条目数")
    synced_items: int = Field(default=0, description="已同步条目数")
    failed_items: int = Field(default=0, description="失败条目数")
    skipped_items: int = Field(default=0, description="跳过条目数")

    # 错误信息
    error_message: Optional[str] = Field(None, description="错误消息")
    error_details: Optional[Dict[str, Any]] = Field(None, description="错误详情")

    # 进度信息
    current_batch: int = Field(default=0, description="当前批次")
    total_batches: int = Field(default=0, description="总批次数")
    progress_percentage: float = Field(default=0.0, ge=0, le=100, description="进度百分比")

    # 元数据
    created_by: Optional[str] = Field(None, description="创建者")
    metadata: Optional[Dict[str, Any]] = Field(None, description="额外元数据")


class SyncTaskCreate(BaseModel):
    """创建同步任务请求"""

    model_config = ConfigDict(protected_namespaces=())

    source: SyncSource = Field(..., description="数据源")
    sync_type: SyncType = Field(default=SyncType.INCREMENTAL, description="同步类型")
    created_by: Optional[str] = Field(None, description="创建者")
    metadata: Optional[Dict[str, Any]] = Field(None, description="额外元数据")


class SyncTaskUpdate(BaseModel):
    """更新同步任务"""

    model_config = ConfigDict(protected_namespaces=())

    status: Optional[SyncStatus] = None
    synced_items: Optional[int] = None
    failed_items: Optional[int] = None
    skipped_items: Optional[int] = None
    current_batch: Optional[int] = None
    progress_percentage: Optional[float] = Field(None, ge=0, le=100)
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None


# ============================================================================
# 历史记录模型
# ============================================================================

class SyncHistory(BaseModel):
    """同步历史记录模型"""

    model_config = ConfigDict(protected_namespaces=())

    id: str = Field(..., description="历史记录ID")
    task_id: str = Field(..., description="关联的任务ID")
    source: SyncSource = Field(..., description="数据源")
    sync_type: SyncType = Field(..., description="同步类型")
    status: SyncStatus = Field(..., description="任务状态")

    # 时间信息
    start_time: datetime = Field(..., description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    duration_seconds: int = Field(default=0, description="执行时长（秒）")

    # 统计信息
    items_synced: int = Field(default=0, description="同步条目数")
    items_failed: int = Field(default=0, description="失败条目数")
    items_skipped: int = Field(default=0, description="跳过条目数")

    # 错误信息
    error_message: Optional[str] = Field(None, description="错误消息")

    # 元数据
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    created_by: Optional[str] = Field(None, description="创建者")


# ============================================================================
# 统计模型
# ============================================================================

class SyncStats(BaseModel):
    """同步统计信息"""

    model_config = ConfigDict(protected_namespaces=())

    source: SyncSource = Field(..., description="数据源")

    # 任务统计
    total_tasks: int = Field(default=0, description="总任务数")
    completed_tasks: int = Field(default=0, description="已完成任务数")
    failed_tasks: int = Field(default=0, description="失败任务数")
    running_tasks: int = Field(default=0, description="运行中任务数")

    # 数据统计
    total_items_synced: int = Field(default=0, description="总同步条目数")
    total_items_failed: int = Field(default=0, description="总失败条目数")

    # 时间统计
    last_sync_time: Optional[datetime] = Field(None, description="最近同步时间")
    next_sync_time: Optional[datetime] = Field(None, description="下次同步时间")
    average_duration_seconds: Optional[float] = Field(None, description="平均执行时长（秒）")


class SyncStatsOverall(BaseModel):
    """总体同步统计"""

    model_config = ConfigDict(protected_namespaces=())

    jira: Optional[SyncStats] = Field(None, description="Jira 统计")
    confluence: Optional[SyncStats] = Field(None, description="Confluence 统计")

    # 总体统计
    total_tasks: int = Field(default=0, description="总任务数")
    total_items_synced: int = Field(default=0, description="总同步条目数")


# ============================================================================
# 响应模型
# ============================================================================

class SyncResponse(BaseModel):
    """同步操作响应"""

    model_config = ConfigDict(protected_namespaces=())

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    task_id: Optional[str] = Field(None, description="任务ID")
    data: Optional[Dict[str, Any]] = Field(None, description="额外数据")


class SyncHistoryListResponse(BaseModel):
    """同步历史列表响应"""

    model_config = ConfigDict(protected_namespaces=())

    items: List[SyncHistory] = Field(default_factory=list, description="历史记录列表")
    total: int = Field(default=0, description="总记录数")
    page: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=20, description="每页大小")
    has_more: bool = Field(default=False, description="是否有更多数据")
