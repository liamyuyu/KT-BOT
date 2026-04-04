"""
同步数据仓库

提供同步历史和配置的数据访问接口。
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, and_, desc, case
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import SyncHistory, SyncConfig as SyncConfigModel
from src.services.sync.models import (
    SyncTask,
    SyncSource,
    SyncStatus,
    SyncType,
    ScheduleType,
)


class SyncHistoryRepo:
    """
    同步历史记录仓库

    负责：
    - 保存和更新同步任务记录
    - 查询历史记录
    - 统计同步性能
    - 获取上次同步时间
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    # ========================================================================
    # 创建和更新
    # ========================================================================

    async def create(self, task: SyncTask) -> SyncHistory:
        """
        创建同步历史记录

        Args:
            task: 同步任务对象

        Returns:
            创建的数据库记录
        """
        history = SyncHistory(
            task_id=task.task_id,
            source=task.source.value,
            sync_type=task.sync_type.value,
            status=task.status.value,
            start_time=task.start_time or datetime.now(),
            end_time=task.end_time,
            duration_seconds=task.duration_seconds,
            total_items=task.total_items,
            synced_items=task.synced_items,
            failed_items=task.failed_items,
            progress_percentage=task.progress_percentage,
            error_message=task.error_message,
            error_code=task.error_code,
            created_by=task.created_by,
            metadata_json=task.metadata,
        )

        self.session.add(history)
        await self.session.commit()
        await self.session.refresh(history)

        return history

    async def update(self, task: SyncTask) -> Optional[SyncHistory]:
        """
        更新同步历史记录

        Args:
            task: 同步任务对象

        Returns:
            更新后的数据库记录
        """
        stmt = select(SyncHistory).where(SyncHistory.task_id == task.task_id)
        result = await self.session.execute(stmt)
        history = result.scalar_one_or_none()

        if not history:
            return None

        # 更新字段
        history.status = task.status.value
        history.end_time = task.end_time
        history.duration_seconds = task.duration_seconds
        history.total_items = task.total_items
        history.synced_items = task.synced_items
        history.failed_items = task.failed_items
        history.progress_percentage = task.progress_percentage
        history.error_message = task.error_message
        history.error_code = task.error_code
        history.metadata_json = task.metadata

        await self.session.commit()
        await self.session.refresh(history)

        return history

    async def upsert(self, task: SyncTask) -> SyncHistory:
        """
        创建或更新同步历史记录

        Args:
            task: 同步任务对象

        Returns:
            数据库记录
        """
        stmt = select(SyncHistory).where(SyncHistory.task_id == task.task_id)
        result = await self.session.execute(stmt)
        history = result.scalar_one_or_none()

        if history:
            return await self.update(task)
        else:
            return await self.create(task)

    # ========================================================================
    # 查询
    # ========================================================================

    async def get_by_task_id(self, task_id: str) -> Optional[SyncHistory]:
        """根据任务ID查询记录"""
        stmt = select(SyncHistory).where(SyncHistory.task_id == task_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_latest_by_source(
        self,
        source: SyncSource,
        status: Optional[SyncStatus] = None
    ) -> Optional[SyncHistory]:
        """
        获取指定数据源的最新记录

        Args:
            source: 数据源
            status: 可选的状态过滤

        Returns:
            最新的记录
        """
        stmt = select(SyncHistory).where(SyncHistory.source == source.value)

        if status:
            stmt = stmt.where(SyncHistory.status == status.value)

        stmt = stmt.order_by(desc(SyncHistory.start_time)).limit(1)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_last_success_time(self, source: SyncSource) -> Optional[datetime]:
        """
        获取指定数据源上次成功同步的时间

        Args:
            source: 数据源

        Returns:
            上次成功同步时间
        """
        history = await self.get_latest_by_source(source, SyncStatus.COMPLETED)
        return history.end_time if history else None

    async def get_history_list(
        self,
        source: Optional[SyncSource] = None,
        status: Optional[SyncStatus] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[SyncHistory]:
        """
        查询历史记录列表

        Args:
            source: 数据源过滤
            status: 状态过滤
            start_time: 开始时间过滤
            end_time: 结束时间过滤
            limit: 返回数量
            offset: 偏移量

        Returns:
            历史记录列表
        """
        stmt = select(SyncHistory)

        # 应用过滤条件
        if source:
            stmt = stmt.where(SyncHistory.source == source.value)

        if status:
            stmt = stmt.where(SyncHistory.status == status.value)

        if start_time:
            stmt = stmt.where(SyncHistory.start_time >= start_time)

        if end_time:
            stmt = stmt.where(SyncHistory.start_time <= end_time)

        # 排序和分页
        stmt = stmt.order_by(desc(SyncHistory.start_time)).limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_filters(
        self,
        source: Optional[SyncSource] = None,
        status: Optional[SyncStatus] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> int:
        """统计符合条件的记录数量"""
        stmt = select(func.count(SyncHistory.id))

        if source:
            stmt = stmt.where(SyncHistory.source == source.value)

        if status:
            stmt = stmt.where(SyncHistory.status == status.value)

        if start_time:
            stmt = stmt.where(SyncHistory.start_time >= start_time)

        if end_time:
            stmt = stmt.where(SyncHistory.start_time <= end_time)

        result = await self.session.execute(stmt)
        return result.scalar_one()

    # ========================================================================
    # 统计
    # ========================================================================

    async def get_statistics(
        self,
        source: Optional[SyncSource] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        获取同步统计信息

        Args:
            source: 数据源（None 表示所有数据源）
            days: 统计最近N天的数据

        Returns:
            统计信息字典
        """
        since = datetime.now() - timedelta(days=days)

        stmt = select(
            func.count(SyncHistory.id).label('total_syncs'),
            func.sum(
                case((SyncHistory.status == SyncStatus.COMPLETED.value, 1), else_=0)
            ).label('successful_syncs'),
            func.sum(
                case((SyncHistory.status == SyncStatus.FAILED.value, 1), else_=0)
            ).label('failed_syncs'),
            func.sum(SyncHistory.synced_items).label('total_items_synced'),
            func.avg(SyncHistory.duration_seconds).label('avg_duration'),
            func.max(SyncHistory.start_time).label('last_sync_time'),
        ).where(SyncHistory.start_time >= since)

        if source:
            stmt = stmt.where(SyncHistory.source == source.value)

        result = await self.session.execute(stmt)
        row = result.one()

        return {
            "total_syncs": row.total_syncs or 0,
            "successful_syncs": row.successful_syncs or 0,
            "failed_syncs": row.failed_syncs or 0,
            "success_rate": (
                round(row.successful_syncs / row.total_syncs * 100, 2)
                if row.total_syncs and row.successful_syncs
                else 0.0
            ),
            "total_items_synced": row.total_items_synced or 0,
            "avg_duration_seconds": (
                round(float(row.avg_duration), 2)
                if row.avg_duration
                else 0.0
            ),
            "last_sync_time": row.last_sync_time,
            "period_days": days,
        }

    async def get_recent_failures(
        self,
        source: Optional[SyncSource] = None,
        limit: int = 10
    ) -> List[SyncHistory]:
        """
        获取最近的失败记录

        Args:
            source: 数据源过滤
            limit: 返回数量

        Returns:
            失败记录列表
        """
        return await self.get_history_list(
            source=source,
            status=SyncStatus.FAILED,
            limit=limit
        )


class SyncConfigRepo:
    """
    同步配置仓库

    负责：
    - 保存和更新配置
    - 查询配置
    - 更新上次同步时间
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    # ========================================================================
    # 创建和更新
    # ========================================================================

    async def create_or_update(
        self,
        source: SyncSource,
        enabled: bool,
        schedule_type: ScheduleType,
        schedule_value: str,
        incremental: bool,
        batch_size: int,
        retry_attempts: int,
        retry_delay: int,
        extra_params: Optional[Dict] = None,
    ) -> SyncConfigModel:
        """
        创建或更新配置

        Args:
            source: 数据源
            enabled: 是否启用
            schedule_type: 调度类型
            schedule_value: 调度值
            incremental: 是否增量同步
            batch_size: 批量大小
            retry_attempts: 重试次数
            retry_delay: 重试延迟
            extra_params: 额外参数

        Returns:
            配置记录
        """
        stmt = select(SyncConfigModel).where(SyncConfigModel.source == source.value)
        result = await self.session.execute(stmt)
        config = result.scalar_one_or_none()

        if config:
            # 更新现有配置
            config.enabled = enabled
            config.schedule_type = schedule_type.value
            config.schedule_value = schedule_value
            config.incremental = incremental
            config.batch_size = batch_size
            config.retry_attempts = retry_attempts
            config.retry_delay = retry_delay
            config.extra_params = extra_params
        else:
            # 创建新配置
            config = SyncConfigModel(
                source=source.value,
                enabled=enabled,
                schedule_type=schedule_type.value,
                schedule_value=schedule_value,
                incremental=incremental,
                batch_size=batch_size,
                retry_attempts=retry_attempts,
                retry_delay=retry_delay,
                extra_params=extra_params,
            )
            self.session.add(config)

        await self.session.commit()
        await self.session.refresh(config)

        return config

    async def update_last_sync(
        self,
        source: SyncSource,
        sync_time: datetime,
        task_id: str
    ) -> Optional[SyncConfigModel]:
        """
        更新上次同步时间

        Args:
            source: 数据源
            sync_time: 同步时间
            task_id: 任务ID

        Returns:
            更新后的配置记录
        """
        stmt = select(SyncConfigModel).where(SyncConfigModel.source == source.value)
        result = await self.session.execute(stmt)
        config = result.scalar_one_or_none()

        if not config:
            return None

        config.last_sync_time = sync_time
        config.last_sync_task_id = task_id

        await self.session.commit()
        await self.session.refresh(config)

        return config

    # ========================================================================
    # 查询
    # ========================================================================

    async def get_by_source(self, source: SyncSource) -> Optional[SyncConfigModel]:
        """根据数据源查询配置"""
        stmt = select(SyncConfigModel).where(SyncConfigModel.source == source.value)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self) -> List[SyncConfigModel]:
        """获取所有配置"""
        stmt = select(SyncConfigModel)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_enabled_sources(self) -> List[SyncSource]:
        """获取所有启用的数据源"""
        stmt = select(SyncConfigModel).where(SyncConfigModel.enabled == True)
        result = await self.session.execute(stmt)
        configs = result.scalars().all()
        return [SyncSource(config.source) for config in configs]
