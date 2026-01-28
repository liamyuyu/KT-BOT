"""
数据同步 API 数据模型

定义同步相关的请求和响应模型。
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from src.services.sync.models import SyncSource, SyncStatus, SyncType, ScheduleType


# ============================================================================
# 基础响应模型
# ============================================================================

class SyncResponse(BaseModel):
    """通用同步响应"""
    success: bool = Field(..., description="是否成功")
    message: Optional[str] = Field(None, description="响应消息")
    data: Optional[Any] = Field(None, description="响应数据")


# ============================================================================
# 配置相关模型
# ============================================================================

class SyncConfigResponse(BaseModel):
    """同步配置响应"""
    source: SyncSource = Field(..., description="数据源")
    enabled: bool = Field(..., description="是否启用")
    schedule_type: ScheduleType = Field(..., description="调度类型")
    schedule_value: str = Field(..., description="调度值")
    incremental: bool = Field(..., description="是否增量同步")
    batch_size: int = Field(..., description="批量大小")
    retry_attempts: int = Field(..., description="重试次数")
    retry_delay: int = Field(..., description="重试延迟(秒)")
    extra_params: Optional[Dict[str, Any]] = Field(None, description="额外参数")
    last_sync_time: Optional[datetime] = Field(None, description="上次同步时间")
    next_run_time: Optional[datetime] = Field(None, description="下次运行时间")

    class Config:
        from_attributes = True


class SyncConfigUpdateRequest(BaseModel):
    """更新同步配置请求"""
    enabled: Optional[bool] = Field(None, description="是否启用")
    schedule_type: Optional[ScheduleType] = Field(None, description="调度类型")
    schedule_value: Optional[str] = Field(None, description="调度值")
    incremental: Optional[bool] = Field(None, description="是否增量同步")
    batch_size: Optional[int] = Field(None, ge=1, le=1000, description="批量大小")
    retry_attempts: Optional[int] = Field(None, ge=0, le=10, description="重试次数")
    retry_delay: Optional[int] = Field(None, ge=0, le=3600, description="重试延迟(秒)")
    extra_params: Optional[Dict[str, Any]] = Field(None, description="额外参数")


class EnableSyncRequest(BaseModel):
    """启用/禁用同步请求"""
    enabled: bool = Field(..., description="是否启用")


# ============================================================================
# 任务相关模型
# ============================================================================

class SyncTaskResponse(BaseModel):
    """同步任务响应"""
    task_id: str = Field(..., description="任务ID")
    source: SyncSource = Field(..., description="数据源")
    sync_type: SyncType = Field(..., description="同步类型")
    status: SyncStatus = Field(..., description="任务状态")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    duration_seconds: Optional[int] = Field(None, description="执行时长(秒)")
    total_items: int = Field(0, description="总项目数")
    synced_items: int = Field(0, description="已同步数")
    failed_items: int = Field(0, description="失败数")
    progress_percentage: float = Field(0, description="进度百分比")
    error_message: Optional[str] = Field(None, description="错误消息")
    error_code: Optional[str] = Field(None, description="错误代码")
    created_by: Optional[str] = Field(None, description="创建者")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")

    class Config:
        from_attributes = True


class TriggerSyncRequest(BaseModel):
    """触发同步请求"""
    sync_type: SyncType = Field(
        SyncType.INCREMENTAL,
        description="同步类型"
    )
    created_by: Optional[str] = Field(None, description="创建者")


class TriggerSyncResponse(BaseModel):
    """触发同步响应"""
    success: bool = Field(..., description="是否成功")
    task_id: str = Field(..., description="任务ID")
    message: str = Field(..., description="响应消息")


# ============================================================================
# 历史记录相关模型
# ============================================================================

class SyncHistoryResponse(BaseModel):
    """同步历史记录响应"""
    id: int = Field(..., description="记录ID")
    task_id: str = Field(..., description="任务ID")
    source: SyncSource = Field(..., description="数据源")
    sync_type: SyncType = Field(..., description="同步类型")
    status: SyncStatus = Field(..., description="任务状态")
    start_time: datetime = Field(..., description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    duration_seconds: Optional[int] = Field(None, description="执行时长(秒)")
    total_items: int = Field(0, description="总项目数")
    synced_items: int = Field(0, description="已同步数")
    failed_items: int = Field(0, description="失败数")
    progress_percentage: float = Field(0, description="进度百分比")
    error_message: Optional[str] = Field(None, description="错误消息")
    error_code: Optional[str] = Field(None, description="错误代码")
    created_by: Optional[str] = Field(None, description="创建者")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


class SyncHistoryListResponse(BaseModel):
    """历史记录列表响应"""
    items: List[SyncHistoryResponse] = Field(..., description="历史记录列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页")
    page_size: int = Field(..., description="每页大小")


# ============================================================================
# 统计相关模型
# ============================================================================

class SyncStatisticsResponse(BaseModel):
    """同步统计响应"""
    source: Optional[SyncSource] = Field(None, description="数据源（None表示全部）")
    period_days: int = Field(..., description="统计周期(天)")
    total_syncs: int = Field(0, description="总同步次数")
    successful_syncs: int = Field(0, description="成功次数")
    failed_syncs: int = Field(0, description="失败次数")
    success_rate: float = Field(0, description="成功率(%)")
    total_items_synced: int = Field(0, description="总同步项数")
    avg_duration_seconds: float = Field(0, description="平均耗时(秒)")
    last_sync_time: Optional[datetime] = Field(None, description="最后同步时间")


# ============================================================================
# 状态查询相关模型
# ============================================================================

class NextRunTimeResponse(BaseModel):
    """下次运行时间响应"""
    source: SyncSource = Field(..., description="数据源")
    enabled: bool = Field(..., description="是否启用")
    next_run_time: Optional[datetime] = Field(None, description="下次运行时间")
    schedule_type: ScheduleType = Field(..., description="调度类型")
    schedule_value: str = Field(..., description="调度值")


class RunningTasksResponse(BaseModel):
    """运行中任务响应"""
    count: int = Field(..., description="运行中任务数量")
    tasks: List[SyncTaskResponse] = Field(..., description="任务列表")


class SchedulerStatusResponse(BaseModel):
    """调度器状态响应"""
    is_running: bool = Field(..., description="调度器是否运行")
    total_tasks: int = Field(..., description="总任务数")
    running_tasks: int = Field(..., description="运行中任务数")
    jira_config: Optional[SyncConfigResponse] = Field(None, description="Jira配置")
    confluence_config: Optional[SyncConfigResponse] = Field(None, description="Confluence配置")
