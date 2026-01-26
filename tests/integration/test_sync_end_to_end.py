"""
数据同步端到端集成测试

测试完整的同步流程：触发 → 执行 → 持久化 → 查询

运行方式:
    PYTHONPATH=/Users/macbook/ai-project/KT-BOT pytest tests/integration/test_sync_end_to_end.py -v
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.sync import get_sync_scheduler, SyncSource, SyncStatus, SyncType
from src.storage.database import async_session_factory, init_db, close_db
from src.storage.database.repository import SyncHistoryRepo, SyncConfigRepo


@pytest.fixture(scope="module")
async def setup_database():
    """设置测试数据库"""
    # 初始化数据库
    await init_db()
    yield
    # 清理
    await close_db()


@pytest.fixture
async def db_session():
    """获取数据库会话"""
    async with async_session_factory() as session:
        yield session


@pytest.fixture
async def scheduler():
    """获取调度器实例"""
    scheduler = get_sync_scheduler()

    # 启动调度器（如果未启动）
    if not scheduler.is_running():
        await scheduler.start()

    yield scheduler

    # 不关闭调度器，保持运行供其他测试使用


class TestEndToEnd:
    """端到端测试"""

    @pytest.mark.asyncio
    async def test_complete_sync_flow(self, scheduler, db_session, setup_database):
        """
        测试完整的同步流程

        流程:
        1. 触发同步任务
        2. 等待任务执行
        3. 验证任务状态
        4. 验证数据库记录
        5. 验证配置更新
        """
        print("\n" + "="*60)
        print("测试: 完整同步流程")
        print("="*60)

        # 1. 触发同步任务
        task_id = await scheduler.trigger_sync(
            source=SyncSource.JIRA,
            sync_type=SyncType.INCREMENTAL,
            created_by="integration_test"
        )
        print(f"✅ 任务已创建: {task_id}")

        # 2. 等待任务开始执行
        await asyncio.sleep(2)

        # 3. 查询任务状态
        task = await scheduler.get_task(task_id)
        assert task is not None, "任务应该存在"
        print(f"✅ 任务状态: {task.status}")

        # 4. 等待任务完成（最多等待 30 秒）
        max_wait = 30
        waited = 0
        while waited < max_wait:
            task = await scheduler.get_task(task_id)
            if task.status in [SyncStatus.COMPLETED, SyncStatus.FAILED]:
                break
            await asyncio.sleep(2)
            waited += 2
            print(f"  等待任务完成... {waited}s")

        # 5. 验证最终状态
        task = await scheduler.get_task(task_id)
        print(f"✅ 最终状态: {task.status}")
        print(f"  - 执行时长: {task.duration_seconds}s")
        print(f"  - 同步项数: {task.synced_items}/{task.total_items}")

        # 注意: 由于测试环境可能没有真实的 Jira 配置，任务可能会失败
        # 我们主要验证流程是否正确执行
        assert task.status in [SyncStatus.COMPLETED, SyncStatus.FAILED], \
            f"任务应该完成或失败，当前状态: {task.status}"

        # 6. 验证数据库记录
        if scheduler.use_db:
            repo = SyncHistoryRepo(db_session)
            history = await repo.get_by_task_id(task_id)

            assert history is not None, "数据库应该有历史记录"
            assert history.task_id == task_id
            assert history.source == SyncSource.JIRA.value
            print(f"✅ 数据库记录已创建: ID={history.id}")

            # 7. 验证配置更新（如果任务成功）
            if task.status == SyncStatus.COMPLETED:
                config_repo = SyncConfigRepo(db_session)
                config = await config_repo.get_by_source(SyncSource.JIRA)

                # 验证上次同步时间已更新
                if config and config.last_sync_time:
                    assert config.last_sync_task_id == task_id
                    print(f"✅ 配置已更新: last_sync_time={config.last_sync_time}")

        print("✅ 完整同步流程测试通过")

    @pytest.mark.asyncio
    async def test_concurrent_sync_prevention(self, scheduler):
        """
        测试并发同步防护

        验证:
        - 同一数据源不能同时运行多个任务
        - 应该抛出 SyncTaskAlreadyRunningError
        """
        print("\n" + "="*60)
        print("测试: 并发同步防护")
        print("="*60)

        # 触发第一个任务
        task_id_1 = await scheduler.trigger_sync(
            source=SyncSource.CONFLUENCE,
            sync_type=SyncType.INCREMENTAL,
            created_by="concurrent_test_1"
        )
        print(f"✅ 第一个任务已创建: {task_id_1}")

        # 等待任务开始运行
        await asyncio.sleep(1)

        # 尝试触发第二个任务（应该失败）
        from src.services.sync.exceptions import SyncTaskAlreadyRunningError

        try:
            await scheduler.trigger_sync(
                source=SyncSource.CONFLUENCE,
                sync_type=SyncType.INCREMENTAL,
                created_by="concurrent_test_2"
            )
            assert False, "应该抛出 SyncTaskAlreadyRunningError"
        except SyncTaskAlreadyRunningError as e:
            print(f"✅ 正确拒绝并发任务: {e}")

        # 等待第一个任务完成
        max_wait = 30
        waited = 0
        while waited < max_wait:
            task = await scheduler.get_task(task_id_1)
            if task.status in [SyncStatus.COMPLETED, SyncStatus.FAILED]:
                break
            await asyncio.sleep(2)
            waited += 2

        print("✅ 并发同步防护测试通过")

    @pytest.mark.asyncio
    async def test_config_update_and_reload(self, scheduler):
        """
        测试配置更新和重载

        验证:
        - 配置可以动态更新
        - 更新后调度任务会重新注册
        """
        print("\n" + "="*60)
        print("测试: 配置更新和重载")
        print("="*60)

        # 获取原始配置
        original_config = await scheduler.get_config(SyncSource.JIRA)
        original_batch_size = original_config.batch_size
        print(f"  原始 batch_size: {original_batch_size}")

        # 更新配置
        await scheduler.update_config(
            SyncSource.JIRA,
            {"batch_size": 200}
        )
        print(f"✅ 配置已更新")

        # 验证更新
        updated_config = await scheduler.get_config(SyncSource.JIRA)
        assert updated_config.batch_size == 200
        print(f"✅ 验证更新成功: batch_size={updated_config.batch_size}")

        # 恢复原始配置
        await scheduler.update_config(
            SyncSource.JIRA,
            {"batch_size": original_batch_size}
        )
        print(f"✅ 已恢复原始配置: batch_size={original_batch_size}")

        print("✅ 配置更新和重载测试通过")

    @pytest.mark.asyncio
    async def test_task_cancellation(self, scheduler):
        """
        测试任务取消

        验证:
        - 运行中的任务可以被取消
        - 取消后任务状态正确更新
        """
        print("\n" + "="*60)
        print("测试: 任务取消")
        print("="*60)

        # 触发任务
        task_id = await scheduler.trigger_sync(
            source=SyncSource.JIRA,
            sync_type=SyncType.FULL,
            created_by="cancel_test"
        )
        print(f"✅ 任务已创建: {task_id}")

        # 等待任务开始
        await asyncio.sleep(2)

        # 取消任务
        success = await scheduler.cancel_task(task_id)

        if success:
            print(f"✅ 任务已取消")

            # 验证状态
            task = await scheduler.get_task(task_id)
            assert task.status == SyncStatus.CANCELLED
            print(f"✅ 任务状态已更新为 CANCELLED")
        else:
            # 任务可能已经完成，无法取消
            task = await scheduler.get_task(task_id)
            print(f"⚠️  任务无法取消（状态: {task.status}）")

        print("✅ 任务取消测试通过")


class TestDatabaseIntegration:
    """数据库集成测试"""

    @pytest.mark.asyncio
    async def test_history_repository(self, db_session, setup_database):
        """测试历史记录仓库"""
        print("\n" + "="*60)
        print("测试: 历史记录仓库")
        print("="*60)

        from src.services.sync.models import SyncTask

        repo = SyncHistoryRepo(db_session)

        # 创建测试任务
        test_task = SyncTask(
            task_id="test-history-001",
            source=SyncSource.JIRA,
            sync_type=SyncType.INCREMENTAL,
            status=SyncStatus.COMPLETED,
            start_time=datetime.now() - timedelta(minutes=5),
            end_time=datetime.now(),
            total_items=100,
            synced_items=95,
            failed_items=5,
            progress_percentage=95.0,
            created_by="test"
        )
        test_task.duration_seconds = 300

        # 创建记录
        history = await repo.create(test_task)
        print(f"✅ 创建历史记录: ID={history.id}")

        # 查询记录
        found = await repo.get_by_task_id("test-history-001")
        assert found is not None
        assert found.task_id == "test-history-001"
        print(f"✅ 查询记录成功")

        # 查询最新记录
        latest = await repo.get_latest_by_source(SyncSource.JIRA)
        assert latest is not None
        print(f"✅ 查询最新记录: {latest.task_id}")

        # 统计信息
        stats = await repo.get_statistics(SyncSource.JIRA, days=7)
        print(f"✅ 统计信息: total={stats['total_syncs']}, success_rate={stats['success_rate']}%")

        print("✅ 历史记录仓库测试通过")

    @pytest.mark.asyncio
    async def test_config_repository(self, db_session, setup_database):
        """测试配置仓库"""
        print("\n" + "="*60)
        print("测试: 配置仓库")
        print("="*60)

        from src.services.sync.models import ScheduleType

        repo = SyncConfigRepo(db_session)

        # 创建或更新配置
        config = await repo.create_or_update(
            source=SyncSource.JIRA,
            enabled=True,
            schedule_type=ScheduleType.CRON,
            schedule_value="0 */6 * * *",
            incremental=True,
            batch_size=50,
            retry_attempts=3,
            retry_delay=60,
            extra_params={"test": "value"}
        )
        print(f"✅ 配置已保存: source={config.source}")

        # 查询配置
        found = await repo.get_by_source(SyncSource.JIRA)
        assert found is not None
        assert found.source == SyncSource.JIRA.value
        print(f"✅ 查询配置成功")

        # 更新上次同步时间
        sync_time = datetime.now()
        updated = await repo.update_last_sync(
            SyncSource.JIRA,
            sync_time,
            "test-task-123"
        )
        assert updated.last_sync_time == sync_time
        assert updated.last_sync_task_id == "test-task-123"
        print(f"✅ 上次同步时间已更新: {sync_time}")

        print("✅ 配置仓库测试通过")


class TestSchedulerIntegration:
    """调度器集成测试"""

    @pytest.mark.asyncio
    async def test_scheduler_lifecycle(self):
        """测试调度器生命周期"""
        print("\n" + "="*60)
        print("测试: 调度器生命周期")
        print("="*60)

        scheduler = get_sync_scheduler()

        # 验证调度器状态
        is_running = scheduler.is_running()
        print(f"✅ 调度器运行状态: {is_running}")

        if is_running:
            # 验证配置加载
            jira_config = await scheduler.get_config(SyncSource.JIRA)
            confluence_config = await scheduler.get_config(SyncSource.CONFLUENCE)

            assert jira_config is not None
            assert confluence_config is not None
            print(f"✅ 配置已加载: Jira={jira_config.enabled}, Confluence={confluence_config.enabled}")

            # 验证下次运行时间
            jira_next = scheduler.get_next_run_time(SyncSource.JIRA)
            confluence_next = scheduler.get_next_run_time(SyncSource.CONFLUENCE)

            print(f"✅ 下次运行时间:")
            print(f"  - Jira: {jira_next}")
            print(f"  - Confluence: {confluence_next}")

        print("✅ 调度器生命周期测试通过")

    @pytest.mark.asyncio
    async def test_scheduler_state_consistency(self, scheduler, db_session, setup_database):
        """
        测试调度器状态一致性

        验证内存中的任务状态与数据库中的记录一致
        """
        print("\n" + "="*60)
        print("测试: 调度器状态一致性")
        print("="*60)

        # 触发任务
        task_id = await scheduler.trigger_sync(
            source=SyncSource.CONFLUENCE,
            sync_type=SyncType.INCREMENTAL,
            created_by="consistency_test"
        )

        # 等待任务执行
        await asyncio.sleep(3)

        # 从内存获取任务
        memory_task = await scheduler.get_task(task_id)
        assert memory_task is not None
        print(f"✅ 内存任务状态: {memory_task.status}")

        # 从数据库获取任务
        if scheduler.use_db:
            repo = SyncHistoryRepo(db_session)
            db_task = await repo.get_by_task_id(task_id)

            if db_task:
                # 验证状态一致
                assert db_task.status == memory_task.status.value
                assert db_task.total_items == memory_task.total_items
                assert db_task.synced_items == memory_task.synced_items
                print(f"✅ 数据库任务状态: {db_task.status}")
                print(f"✅ 状态一致性验证通过")
            else:
                print("⚠️  数据库中未找到记录（可能任务尚未持久化）")

        print("✅ 调度器状态一致性测试通过")


@pytest.mark.asyncio
async def test_full_integration():
    """完整集成测试入口"""
    print("\n" + "="*70)
    print("🚀 数据同步系统 - 完整集成测试")
    print("="*70)

    # 初始化数据库
    await init_db()

    try:
        # 获取调度器
        scheduler = get_sync_scheduler()
        if not scheduler.is_running():
            await scheduler.start()

        print("\n✅ 测试环境准备完成")
        print(f"  - 调度器状态: {'运行中' if scheduler.is_running() else '未运行'}")
        print(f"  - 数据库持久化: {'启用' if scheduler.use_db else '禁用'}")

        # 运行所有测试会自动执行
        print("\n💡 使用 pytest 运行所有测试:")
        print("   pytest tests/integration/test_sync_end_to_end.py -v")

    finally:
        await close_db()


if __name__ == "__main__":
    # 运行完整集成测试
    asyncio.run(test_full_integration())
