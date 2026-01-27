"""
数据同步 API 路由

提供同步配置管理、任务触发、状态查询和历史记录查询接口。
"""

import logging
import asyncio
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends, Path
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import json

from src.services.sync import get_sync_scheduler, SyncSource, SyncStatus, SyncType
from src.services.sync.exceptions import (
    SyncSchedulerError,
    SyncTaskNotFoundError,
    SyncTaskAlreadyRunningError,
    SyncConfigError,
)
from src.storage.database import get_db
from src.storage.database.repository import SyncHistoryRepo
from src.api.schemas.sync import (
    SyncConfigResponse,
    SyncConfigUpdateRequest,
    EnableSyncRequest,
    SyncTaskResponse,
    TriggerSyncRequest,
    TriggerSyncResponse,
    SyncHistoryResponse,
    SyncHistoryListResponse,
    SyncStatisticsResponse,
    NextRunTimeResponse,
    RunningTasksResponse,
    SchedulerStatusResponse,
    SyncResponse,
)
from src.api.schemas.common import SuccessResponse, ErrorResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sync", tags=["同步管理"])


# ============================================================================
# 辅助函数
# ============================================================================

def _task_to_response(task) -> SyncTaskResponse:
    """将 SyncTask 转换为响应模型"""
    return SyncTaskResponse(
        task_id=task.task_id,
        source=task.source,
        sync_type=task.sync_type,
        status=task.status,
        start_time=task.start_time,
        end_time=task.end_time,
        duration_seconds=task.duration_seconds,
        total_items=task.total_items,
        synced_items=task.synced_items,
        failed_items=task.failed_items,
        progress_percentage=task.progress_percentage,
        error_message=task.error_message,
        error_code=task.error_code,
        created_by=task.created_by,
        metadata=task.metadata,
    )


async def _config_to_response(source: SyncSource, config, scheduler) -> SyncConfigResponse:
    """将配置对象转换为响应模型"""
    next_run_time = scheduler.get_next_run_time(source) if scheduler.is_running() else None

    return SyncConfigResponse(
        source=source,
        enabled=config.enabled,
        schedule_type=config.schedule_type,
        schedule_value=config.schedule_value,
        incremental=config.incremental,
        batch_size=config.batch_size,
        retry_attempts=config.retry_attempts,
        retry_delay=config.retry_delay,
        extra_params=config.extra_params,
        last_sync_time=await scheduler.get_last_sync_time(source) if scheduler.use_db else None,
        next_run_time=next_run_time,
    )


# ============================================================================
# 配置管理 API (5个)
# ============================================================================

@router.get(
    "/config",
    response_model=List[SyncConfigResponse],
    summary="获取所有同步配置",
    description="获取 Jira 和 Confluence 的所有同步配置信息",
)
async def get_all_configs():
    """获取所有同步配置"""
    try:
        scheduler = get_sync_scheduler()

        configs = []
        for source in [SyncSource.JIRA, SyncSource.CONFLUENCE]:
            config = await scheduler.get_config(source)
            if config:
                config_response = await _config_to_response(source, config, scheduler)
                configs.append(config_response)

        return configs

    except Exception as e:
        logger.error(f"Failed to get configs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/config/{source}",
    response_model=SyncConfigResponse,
    summary="获取指定数据源配置",
    description="获取指定数据源（jira 或 confluence）的同步配置",
)
async def get_config(
    source: SyncSource = Path(..., description="数据源")
):
    """获取指定数据源的配置"""
    try:
        scheduler = get_sync_scheduler()
        config = await scheduler.get_config(source)

        if not config:
            raise HTTPException(status_code=404, detail=f"Config not found for {source}")

        return await _config_to_response(source, config, scheduler)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get config for {source}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/config/{source}",
    response_model=SyncConfigResponse,
    summary="更新同步配置",
    description="更新指定数据源的同步配置",
)
async def update_config(
    source: SyncSource = Path(..., description="数据源"),
    request: SyncConfigUpdateRequest = None,
):
    """更新同步配置"""
    try:
        scheduler = get_sync_scheduler()

        # 构建更新字典（只包含非 None 的字段）
        updates = {}
        if request.enabled is not None:
            updates["enabled"] = request.enabled
        if request.schedule_type is not None:
            updates["schedule_type"] = request.schedule_type
        if request.schedule_value is not None:
            updates["schedule_value"] = request.schedule_value
        if request.incremental is not None:
            updates["incremental"] = request.incremental
        if request.batch_size is not None:
            updates["batch_size"] = request.batch_size
        if request.retry_attempts is not None:
            updates["retry_attempts"] = request.retry_attempts
        if request.retry_delay is not None:
            updates["retry_delay"] = request.retry_delay
        if request.extra_params is not None:
            updates["extra_params"] = request.extra_params

        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        # 更新配置
        await scheduler.update_config(source, updates)

        # 返回更新后的配置
        config = await scheduler.get_config(source)
        return await _config_to_response(source, config, scheduler)

    except SyncConfigError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update config for {source}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/config/{source}/enable",
    response_model=SuccessResponse,
    summary="启用/禁用自动同步",
    description="启用或禁用指定数据源的自动同步",
)
async def enable_sync(
    source: SyncSource = Path(..., description="数据源"),
    request: EnableSyncRequest = None,
):
    """启用/禁用自动同步"""
    try:
        scheduler = get_sync_scheduler()

        # 更新 enabled 状态
        await scheduler.update_config(source, {"enabled": request.enabled})

        action = "启用" if request.enabled else "禁用"
        return SuccessResponse(
            success=True,
            message=f"已{action} {source.value} 自动同步"
        )

    except SyncConfigError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to enable/disable {source}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/config/reload",
    response_model=SuccessResponse,
    summary="重新加载配置",
    description="从配置文件重新加载同步配置并更新调度任务",
)
async def reload_config():
    """重新加载配置"""
    try:
        scheduler = get_sync_scheduler()
        await scheduler.reload_config()

        return SuccessResponse(
            success=True,
            message="配置已重新加载"
        )

    except Exception as e:
        logger.error(f"Failed to reload config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 手动触发同步 API (2个)
# ============================================================================

@router.post(
    "/trigger/{source}",
    response_model=TriggerSyncResponse,
    summary="触发同步",
    description="手动触发指定数据源的同步任务",
)
async def trigger_sync(
    source: SyncSource = Path(..., description="数据源"),
    request: TriggerSyncRequest = TriggerSyncRequest(),
):
    """触发同步"""
    try:
        scheduler = get_sync_scheduler()

        # 触发同步
        task_id = await scheduler.trigger_sync(
            source=source,
            sync_type=request.sync_type,
            created_by=request.created_by or "api",
        )

        return TriggerSyncResponse(
            success=True,
            task_id=task_id,
            message=f"同步任务已创建: {task_id}"
        )

    except SyncTaskAlreadyRunningError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except SyncSchedulerError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to trigger sync for {source}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/cancel/{task_id}",
    response_model=SuccessResponse,
    summary="取消同步任务",
    description="取消正在运行的同步任务",
)
async def cancel_sync(
    task_id: str = Path(..., description="任务ID")
):
    """取消同步任务"""
    try:
        scheduler = get_sync_scheduler()

        # 取消任务
        success = await scheduler.cancel_task(task_id)

        if not success:
            return SuccessResponse(
                success=False,
                message=f"任务 {task_id} 无法取消（可能已完成或不存在）"
            )

        return SuccessResponse(
            success=True,
            message=f"任务 {task_id} 已取消"
        )

    except SyncTaskNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to cancel task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 同步状态查询 API (3个)
# ============================================================================

@router.get(
    "/status/{task_id}",
    response_model=SyncTaskResponse,
    summary="查询任务状态",
    description="查询指定任务的执行状态和进度",
)
async def get_task_status(
    task_id: str = Path(..., description="任务ID")
):
    """查询任务状态"""
    try:
        scheduler = get_sync_scheduler()
        task = await scheduler.get_task(task_id)

        if not task:
            raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

        return _task_to_response(task)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task status {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/status/running",
    response_model=RunningTasksResponse,
    summary="查询运行中的任务",
    description="查询所有正在运行的同步任务",
)
async def get_running_tasks():
    """查询运行中的任务"""
    try:
        scheduler = get_sync_scheduler()
        tasks = await scheduler.get_running_tasks()

        return RunningTasksResponse(
            count=len(tasks),
            tasks=[_task_to_response(task) for task in tasks]
        )

    except Exception as e:
        logger.error(f"Failed to get running tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/next-run/{source}",
    response_model=NextRunTimeResponse,
    summary="查询下次同步时间",
    description="查询指定数据源的下次自动同步时间",
)
async def get_next_run_time(
    source: SyncSource = Path(..., description="数据源")
):
    """查询下次同步时间"""
    try:
        scheduler = get_sync_scheduler()
        config = await scheduler.get_config(source)

        if not config:
            raise HTTPException(status_code=404, detail=f"Config not found for {source}")

        next_run_time = scheduler.get_next_run_time(source) if scheduler.is_running() else None

        return NextRunTimeResponse(
            source=source,
            enabled=config.enabled,
            next_run_time=next_run_time,
            schedule_type=config.schedule_type,
            schedule_value=config.schedule_value,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get next run time for {source}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 同步历史记录 API (2个)
# ============================================================================

@router.get(
    "/history",
    response_model=SyncHistoryListResponse,
    summary="查询历史记录",
    description="分页查询同步历史记录，支持按数据源、状态、时间范围过滤",
)
async def get_history(
    source: Optional[SyncSource] = Query(None, description="数据源过滤"),
    status: Optional[SyncStatus] = Query(None, description="状态过滤"),
    start_time: Optional[datetime] = Query(None, description="开始时间过滤"),
    end_time: Optional[datetime] = Query(None, description="结束时间过滤"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    db: AsyncSession = Depends(get_db),
):
    """查询历史记录"""
    try:
        repo = SyncHistoryRepo(db)

        # 计算偏移量
        offset = (page - 1) * page_size

        # 查询历史记录
        items = await repo.get_history_list(
            source=source,
            status=status,
            start_time=start_time,
            end_time=end_time,
            limit=page_size,
            offset=offset,
        )

        # 统计总数
        total = await repo.count_by_filters(
            source=source,
            status=status,
            start_time=start_time,
            end_time=end_time,
        )

        # 转换为响应模型
        history_responses = [
            SyncHistoryResponse.model_validate(item)
            for item in items
        ]

        return SyncHistoryListResponse(
            items=history_responses,
            total=total,
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        logger.error(f"Failed to get history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/statistics",
    response_model=SyncStatisticsResponse,
    summary="查询统计信息",
    description="查询同步统计信息，包括成功率、平均耗时等",
)
async def get_statistics(
    source: Optional[SyncSource] = Query(None, description="数据源（不指定则统计所有）"),
    days: int = Query(7, ge=1, le=90, description="统计最近N天"),
    db: AsyncSession = Depends(get_db),
):
    """查询统计信息"""
    try:
        repo = SyncHistoryRepo(db)

        # 获取统计信息
        stats = await repo.get_statistics(source=source, days=days)

        return SyncStatisticsResponse(
            source=source,
            period_days=stats["period_days"],
            total_syncs=stats["total_syncs"],
            successful_syncs=stats["successful_syncs"],
            failed_syncs=stats["failed_syncs"],
            success_rate=stats["success_rate"],
            total_items_synced=stats["total_items_synced"],
            avg_duration_seconds=stats["avg_duration_seconds"],
            last_sync_time=stats["last_sync_time"],
        )

    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 调度器状态 API (额外)
# ============================================================================

@router.get(
    "/scheduler/status",
    response_model=SchedulerStatusResponse,
    summary="查询调度器状态",
    description="查询调度器整体状态和配置概览",
)
async def get_scheduler_status():
    """查询调度器状态"""
    try:
        scheduler = get_sync_scheduler()

        # 获取所有任务
        all_tasks = await scheduler.get_all_tasks()
        running_tasks = await scheduler.get_running_tasks()

        # 获取配置
        jira_config = await scheduler.get_config(SyncSource.JIRA)
        confluence_config = await scheduler.get_config(SyncSource.CONFLUENCE)

        return SchedulerStatusResponse(
            is_running=scheduler.is_running(),
            total_tasks=len(all_tasks),
            running_tasks=len(running_tasks),
            jira_config=await _config_to_response(SyncSource.JIRA, jira_config, scheduler) if jira_config else None,
            confluence_config=await _config_to_response(SyncSource.CONFLUENCE, confluence_config, scheduler) if confluence_config else None,
        )

    except Exception as e:
        logger.error(f"Failed to get scheduler status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 同步进度推送 API (SSE)
# ============================================================================

@router.get(
    "/progress/stream/{task_id}",
    summary="实时同步进度流",
    description="使用 SSE 实时推送指定任务的同步进度",
)
async def stream_task_progress(
    task_id: str = Path(..., description="任务ID")
):
    """
    流式推送任务进度

    Returns:
        SSE stream with progress updates
    """
    async def event_generator():
        """生成 SSE 事件"""
        try:
            scheduler = get_sync_scheduler()

            # 检查任务是否存在
            task = await scheduler.get_task(task_id)
            if not task:
                yield f"event: error\ndata: {json.dumps({'error': 'Task not found'})}\n\n"
                return

            # 持续推送进度直到任务完成
            while True:
                task = await scheduler.get_task(task_id)

                if not task:
                    yield f"event: error\ndata: {json.dumps({'error': 'Task not found'})}\n\n"
                    break

                # 构建进度数据
                progress_data = {
                    "task_id": task.task_id,
                    "status": task.status.value,
                    "progress_percentage": task.progress_percentage,
                    "synced_items": task.synced_items,
                    "total_items": task.total_items,
                    "failed_items": task.failed_items,
                    "current_batch": getattr(task, 'current_batch', 0),
                    "total_batches": getattr(task, 'total_batches', 0),
                    "duration_seconds": task.duration_seconds,
                    "error_message": task.error_message,
                }

                # 发送进度事件
                yield f"event: progress\ndata: {json.dumps(progress_data)}\n\n"

                # 如果任务已完成，发送完成事件并退出
                if task.status in [SyncStatus.COMPLETED, SyncStatus.FAILED, SyncStatus.CANCELLED]:
                    yield f"event: complete\ndata: {json.dumps(progress_data)}\n\n"
                    break

                # 等待一段时间再获取下次进度
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Error streaming progress for task {task_id}: {e}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
        }
    )


@router.get(
    "/progress/stream",
    summary="实时所有任务进度流",
    description="使用 SSE 实时推送所有运行中任务的进度",
)
async def stream_all_progress():
    """
    流式推送所有运行中任务的进度

    Returns:
        SSE stream with progress updates for all running tasks
    """
    async def event_generator():
        """生成 SSE 事件"""
        try:
            scheduler = get_sync_scheduler()

            while True:
                # 获取所有运行中的任务
                running_tasks = await scheduler.get_running_tasks()

                if not running_tasks:
                    # 如果没有运行中的任务，发送空列表
                    yield f"event: progress\ndata: {json.dumps({'tasks': []})}\n\n"
                    await asyncio.sleep(2)
                    continue

                # 构建所有任务的进度数据
                tasks_data = []
                for task in running_tasks:
                    progress_data = {
                        "task_id": task.task_id,
                        "source": task.source.value,
                        "sync_type": task.sync_type.value,
                        "status": task.status.value,
                        "progress_percentage": task.progress_percentage,
                        "synced_items": task.synced_items,
                        "total_items": task.total_items,
                        "failed_items": task.failed_items,
                        "current_batch": getattr(task, 'current_batch', 0),
                        "total_batches": getattr(task, 'total_batches', 0),
                        "duration_seconds": task.duration_seconds,
                        "start_time": task.start_time.isoformat() if task.start_time else None,
                    }
                    tasks_data.append(progress_data)

                # 发送进度事件
                yield f"event: progress\ndata: {json.dumps({'tasks': tasks_data})}\n\n"

                # 等待一段时间再获取下次进度
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Error streaming all progress: {e}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
