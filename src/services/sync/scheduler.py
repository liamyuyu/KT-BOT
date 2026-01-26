"""
数据同步调度器

负责管理 Jira 和 Confluence 的自动同步任务调度。
使用 APScheduler 实现定时任务和间隔任务。
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import uuid

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import yaml

from .models import (
    SyncConfig,
    SyncSource,
    SyncStatus,
    SyncTask,
    SyncType,
    ScheduleType,
)
from .exceptions import (
    SyncConfigError,
    SyncSchedulerError,
    SyncTaskNotFoundError,
    SyncTaskAlreadyRunningError,
)
from src.storage.database import async_session_factory
from src.storage.database.repository import SyncHistoryRepo, SyncConfigRepo


logger = logging.getLogger(__name__)


class SyncScheduler:
    """
    同步任务调度器

    负责：
    - 加载和管理同步配置
    - 调度定时同步任务
    - 执行手动同步任务
    - 管理任务状态和生命周期
    - 提供任务查询接口
    """

    def __init__(self, config_path: Optional[str] = None, use_db: bool = True):
        """
        初始化调度器

        Args:
            config_path: 配置文件路径（默认: config/sync_config.yaml）
            use_db: 是否使用数据库持久化（默认: True）
        """
        self.config_path = config_path or "config/sync_config.yaml"
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.configs: Dict[SyncSource, SyncConfig] = {}
        self.tasks: Dict[str, SyncTask] = {}  # task_id -> SyncTask
        self.running_tasks: Dict[SyncSource, str] = {}  # source -> task_id
        self._is_running = False
        self._task_locks: Dict[SyncSource, asyncio.Lock] = {
            SyncSource.JIRA: asyncio.Lock(),
            SyncSource.CONFLUENCE: asyncio.Lock(),
        }
        self.use_db = use_db  # 是否启用数据库持久化

    # ========================================================================
    # 生命周期管理
    # ========================================================================

    async def start(self):
        """启动调度器"""
        if self._is_running:
            logger.warning("Scheduler is already running")
            return

        try:
            # 加载配置
            await self.load_config()

            # 创建调度器
            self.scheduler = AsyncIOScheduler()
            self.scheduler.start()

            # 注册定时任务
            await self._register_scheduled_tasks()

            self._is_running = True
            logger.info("Sync scheduler started successfully")

        except Exception as e:
            logger.error(f"Failed to start sync scheduler: {e}")
            raise SyncSchedulerError(f"Failed to start scheduler: {str(e)}")

    async def shutdown(self, wait: bool = True):
        """
        关闭调度器

        Args:
            wait: 是否等待当前运行的任务完成
        """
        if not self._is_running:
            logger.warning("Scheduler is not running")
            return

        try:
            # 停止调度器
            if self.scheduler:
                self.scheduler.shutdown(wait=wait)

            # 等待运行中的任务（如果需要）
            if wait and self.running_tasks:
                logger.info(f"Waiting for {len(self.running_tasks)} tasks to complete...")
                await asyncio.sleep(1)  # 简化实现

            self._is_running = False
            logger.info("Sync scheduler shut down successfully")

        except Exception as e:
            logger.error(f"Error shutting down scheduler: {e}")
            raise SyncSchedulerError(f"Failed to shutdown scheduler: {str(e)}")

    async def reload_config(self):
        """重新加载配置并更新调度任务"""
        logger.info("Reloading sync configuration...")

        # 移除现有的定时任务
        if self.scheduler:
            for job in self.scheduler.get_jobs():
                job.remove()

        # 重新加载配置
        await self.load_config()

        # 重新注册任务
        if self._is_running:
            await self._register_scheduled_tasks()

        logger.info("Configuration reloaded successfully")

    # ========================================================================
    # 配置管理
    # ========================================================================

    async def load_config(self):
        """从 YAML 文件加载同步配置"""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                raise SyncConfigError(f"Config file not found: {self.config_path}")

            with open(config_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            # 解析 Jira 配置
            if 'jira' in data:
                self.configs[SyncSource.JIRA] = SyncConfig(
                    source=SyncSource.JIRA,
                    **data['jira']
                )
                logger.info(f"Loaded Jira sync config: enabled={self.configs[SyncSource.JIRA].enabled}")

            # 解析 Confluence 配置
            if 'confluence' in data:
                self.configs[SyncSource.CONFLUENCE] = SyncConfig(
                    source=SyncSource.CONFLUENCE,
                    **data['confluence']
                )
                logger.info(f"Loaded Confluence sync config: enabled={self.configs[SyncSource.CONFLUENCE].enabled}")

        except Exception as e:
            logger.error(f"Failed to load sync config: {e}")
            raise SyncConfigError(f"Failed to load config: {str(e)}")

    async def get_config(self, source: SyncSource) -> Optional[SyncConfig]:
        """获取指定数据源的配置"""
        return self.configs.get(source)

    async def update_config(self, source: SyncSource, updates: Dict):
        """更新指定数据源的配置"""
        if source not in self.configs:
            raise SyncConfigError(f"Config not found for source: {source}")

        config = self.configs[source]

        # 更新配置字段
        for key, value in updates.items():
            if hasattr(config, key):
                setattr(config, key, value)

        # 如果调度配置改变，需要重新注册任务
        if any(k in updates for k in ['enabled', 'schedule_type', 'schedule_value']):
            await self._update_scheduled_task(source)

        logger.info(f"Updated config for {source}: {updates}")

    # ========================================================================
    # 任务调度
    # ========================================================================

    async def _register_scheduled_tasks(self):
        """注册所有启用的定时同步任务"""
        for source, config in self.configs.items():
            if config.enabled:
                await self._register_task(source, config)

    async def _register_task(self, source: SyncSource, config: SyncConfig):
        """
        注册单个定时任务

        Args:
            source: 数据源
            config: 同步配置
        """
        try:
            # 创建触发器
            if config.schedule_type == ScheduleType.CRON:
                # Cron 表达式
                parts = config.schedule_value.split()
                if len(parts) != 5:
                    raise SyncConfigError(f"Invalid cron expression: {config.schedule_value}")

                trigger = CronTrigger(
                    minute=parts[0],
                    hour=parts[1],
                    day=parts[2],
                    month=parts[3],
                    day_of_week=parts[4]
                )
            else:
                # 时间间隔（秒）
                seconds = int(config.schedule_value)
                trigger = IntervalTrigger(seconds=seconds)

            # 注册任务
            job_id = f"sync_{source.value}"
            self.scheduler.add_job(
                func=self._execute_scheduled_sync,
                trigger=trigger,
                id=job_id,
                args=[source],
                replace_existing=True,
                misfire_grace_time=300,  # 允许5分钟误差
            )

            logger.info(f"Registered scheduled task: {job_id} with {config.schedule_type}={config.schedule_value}")

        except Exception as e:
            logger.error(f"Failed to register task for {source}: {e}")
            raise SyncSchedulerError(f"Failed to register task: {str(e)}")

    async def _update_scheduled_task(self, source: SyncSource):
        """更新指定数据源的调度任务"""
        job_id = f"sync_{source.value}"

        # 移除现有任务
        job = self.scheduler.get_job(job_id)
        if job:
            job.remove()

        # 重新注册
        config = self.configs.get(source)
        if config and config.enabled:
            await self._register_task(source, config)

    async def _execute_scheduled_sync(self, source: SyncSource):
        """
        执行定时同步任务（内部方法）

        Args:
            source: 数据源
        """
        logger.info(f"Executing scheduled sync for {source}")

        try:
            config = self.configs.get(source)
            if not config:
                logger.error(f"Config not found for {source}")
                return

            # 检查是否已有任务在运行
            if source in self.running_tasks:
                logger.warning(f"Sync task for {source} is already running, skipping...")
                return

            # 确定同步类型
            sync_type = SyncType.INCREMENTAL if config.incremental else SyncType.FULL

            # 触发同步
            task_id = await self.trigger_sync(
                source=source,
                sync_type=sync_type,
                created_by="scheduler"
            )

            logger.info(f"Scheduled sync triggered: task_id={task_id}")

        except Exception as e:
            logger.error(f"Error in scheduled sync for {source}: {e}")

    # ========================================================================
    # 任务管理
    # ========================================================================

    async def trigger_sync(
        self,
        source: SyncSource,
        sync_type: SyncType = SyncType.INCREMENTAL,
        created_by: Optional[str] = None
    ) -> str:
        """
        手动触发同步任务

        Args:
            source: 数据源
            sync_type: 同步类型
            created_by: 创建者

        Returns:
            task_id: 任务ID

        Raises:
            SyncTaskAlreadyRunningError: 如果该数据源已有任务在运行
        """
        # 检查是否已有任务在运行
        async with self._task_locks[source]:
            if source in self.running_tasks:
                running_task_id = self.running_tasks[source]
                raise SyncTaskAlreadyRunningError(
                    f"Sync task for {source} is already running: {running_task_id}"
                )

            # 创建任务
            task_id = str(uuid.uuid4())
            task = SyncTask(
                task_id=task_id,
                source=source,
                sync_type=sync_type,
                status=SyncStatus.PENDING,
                created_by=created_by,
            )

            # 保存任务
            self.tasks[task_id] = task
            self.running_tasks[source] = task_id

        # 异步执行同步任务
        asyncio.create_task(self._execute_sync_task(task_id))

        logger.info(f"Sync task created: task_id={task_id}, source={source}, type={sync_type}")
        return task_id

    async def _execute_sync_task(self, task_id: str):
        """
        执行同步任务（内部方法）

        Args:
            task_id: 任务ID
        """
        task = self.tasks.get(task_id)
        if not task:
            logger.error(f"Task not found: {task_id}")
            return

        try:
            # 持久化任务记录（创建）
            if self.use_db:
                await self._persist_task_start(task)

            # 获取配置
            config_obj = self.configs.get(task.source)
            if not config_obj:
                raise SyncSchedulerError(f"Config not found for source: {task.source}")

            # 获取上次同步时间（用于增量同步）
            last_sync_time = None
            if task.sync_type == SyncType.INCREMENTAL:
                last_sync_time = await self.get_last_sync_time(task.source)
                if last_sync_time:
                    logger.info(f"Last sync time for {task.source}: {last_sync_time}")

            # 准备配置参数
            config_params = {
                "batch_size": config_obj.batch_size,
                "retry_attempts": config_obj.retry_attempts,
                "retry_delay": config_obj.retry_delay,
            }

            # 添加额外参数
            if config_obj.extra_params:
                config_params.update(config_obj.extra_params)

            # 创建同步任务实例
            from .tasks import create_sync_task
            sync_task = create_sync_task(task, config_params, last_sync_time)

            logger.info(f"Executing sync task: {task_id}")

            # 执行同步
            updated_task = await sync_task.execute()

            # 更新任务对象
            self.tasks[task_id] = updated_task

            # 持久化任务记录（更新）
            if self.use_db:
                await self._persist_task_complete(updated_task)

            logger.info(
                f"Sync task finished: {task_id}, "
                f"status={updated_task.status}, "
                f"synced={updated_task.synced_items}/{updated_task.total_items}"
            )

        except Exception as e:
            # 处理错误
            task.status = SyncStatus.FAILED
            task.end_time = datetime.now()
            task.error_message = str(e)
            task.duration_seconds = int((task.end_time - task.start_time).total_seconds()) if task.start_time else 0
            logger.error(f"Sync task failed: {task_id}, error={e}")

            # 持久化失败记录
            if self.use_db:
                await self._persist_task_complete(task)

        finally:
            # 从运行列表中移除
            if task.source in self.running_tasks:
                if self.running_tasks[task.source] == task_id:
                    del self.running_tasks[task.source]

    async def get_task(self, task_id: str) -> Optional[SyncTask]:
        """获取任务详情"""
        return self.tasks.get(task_id)

    async def get_all_tasks(self) -> List[SyncTask]:
        """获取所有任务"""
        return list(self.tasks.values())

    async def get_running_tasks(self) -> List[SyncTask]:
        """获取所有运行中的任务"""
        return [
            task for task in self.tasks.values()
            if task.status == SyncStatus.RUNNING
        ]

    async def cancel_task(self, task_id: str) -> bool:
        """
        取消任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功取消
        """
        task = self.tasks.get(task_id)
        if not task:
            raise SyncTaskNotFoundError(f"Task not found: {task_id}")

        if task.status != SyncStatus.RUNNING:
            logger.warning(f"Cannot cancel task {task_id}: status is {task.status}")
            return False

        # 更新状态
        task.status = SyncStatus.CANCELLED
        task.end_time = datetime.now()

        # 从运行列表中移除
        if task.source in self.running_tasks:
            if self.running_tasks[task.source] == task_id:
                del self.running_tasks[task.source]

        logger.info(f"Task cancelled: {task_id}")
        return True

    # ========================================================================
    # 数据持久化
    # ========================================================================

    async def _persist_task_start(self, task: SyncTask):
        """
        持久化任务开始记录

        Args:
            task: 同步任务
        """
        try:
            async with async_session_factory() as session:
                repo = SyncHistoryRepo(session)
                await repo.create(task)
                logger.debug(f"Persisted task start: {task.task_id}")
        except Exception as e:
            logger.error(f"Failed to persist task start: {e}")
            # 持久化失败不应该影响任务执行

    async def _persist_task_complete(self, task: SyncTask):
        """
        持久化任务完成记录

        Args:
            task: 同步任务
        """
        try:
            async with async_session_factory() as session:
                repo = SyncHistoryRepo(session)
                await repo.update(task)

                # 如果任务成功完成，更新配置表中的上次同步时间
                if task.status == SyncStatus.COMPLETED and task.end_time:
                    config_repo = SyncConfigRepo(session)
                    await config_repo.update_last_sync(
                        task.source,
                        task.end_time,
                        task.task_id
                    )

                logger.debug(f"Persisted task complete: {task.task_id}")
        except Exception as e:
            logger.error(f"Failed to persist task complete: {e}")

    async def get_last_sync_time(self, source: SyncSource) -> Optional[datetime]:
        """
        获取指定数据源的上次同步时间

        Args:
            source: 数据源

        Returns:
            上次同步时间，如果未找到则返回 None
        """
        if not self.use_db:
            return None

        try:
            async with async_session_factory() as session:
                config_repo = SyncConfigRepo(session)
                config = await config_repo.get_by_source(source)
                return config.last_sync_time if config else None
        except Exception as e:
            logger.error(f"Failed to get last sync time: {e}")
            return None

    # ========================================================================
    # 状态查询
    # ========================================================================

    def is_running(self) -> bool:
        """调度器是否正在运行"""
        return self._is_running

    def get_next_run_time(self, source: SyncSource) -> Optional[datetime]:
        """
        获取下次同步时间

        Args:
            source: 数据源

        Returns:
            下次执行时间，如果未启用则返回 None
        """
        if not self.scheduler:
            return None

        job_id = f"sync_{source.value}"
        job = self.scheduler.get_job(job_id)
        if job:
            return job.next_run_time
        return None
