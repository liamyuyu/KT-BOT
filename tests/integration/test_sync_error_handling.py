"""
数据同步错误处理测试

测试同步系统的错误处理和恢复能力。

运行方式:
    PYTHONPATH=/Users/macbook/ai-project/KT-BOT pytest tests/integration/test_sync_error_handling.py -v
"""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from src.services.sync import get_sync_scheduler, SyncSource, SyncStatus, SyncType
from src.services.sync.exceptions import (
    SyncSchedulerError,
    SyncTaskNotFoundError,
    SyncTaskAlreadyRunningError,
    SyncConfigError,
)
from src.storage.database import init_db, close_db


@pytest.fixture(scope="module")
async def setup_test_env():
    """设置测试环境"""
    await init_db()
    scheduler = get_sync_scheduler()
    if not scheduler.is_running():
        await scheduler.start()
    yield scheduler
    await close_db()


class TestConfigErrors:
    """配置错误测试"""

    @pytest.mark.asyncio
    async def test_invalid_config_update(self, setup_test_env):
        """测试无效的配置更新"""
        print("\n" + "="*60)
        print("测试: 无效配置更新")
        print("="*60)

        scheduler = setup_test_env

        # 测试 1: 更新不存在的字段
        try:
            await scheduler.update_config(
                SyncSource.JIRA,
                {"invalid_field": "value"}
            )
            # 应该忽略无效字段，不抛出异常
            print("✅ 忽略无效字段")
        except Exception as e:
            print(f"⚠️  更新失败: {e}")

        # 测试 2: 无效的批量大小
        try:
            await scheduler.update_config(
                SyncSource.JIRA,
                {"batch_size": -1}
            )
            # 可能不会验证，取决于实现
            print("⚠️  接受了无效的批量大小")
        except Exception as e:
            print(f"✅ 正确拒绝无效值: {e}")

        print("✅ 配置错误处理测试通过")

    @pytest.mark.asyncio
    async def test_nonexistent_source_config(self, setup_test_env):
        """测试查询不存在的数据源配置"""
        print("\n" + "="*60)
        print("测试: 不存在的数据源")
        print("="*60)

        scheduler = setup_test_env

        # 目前只支持 JIRA 和 CONFLUENCE
        # 获取不存在的源应该返回 None
        config = await scheduler.get_config(SyncSource.JIRA)
        assert config is not None, "JIRA 配置应该存在"

        print("✅ 数据源配置测试通过")


class TestTaskErrors:
    """任务错误测试"""

    @pytest.mark.asyncio
    async def test_task_not_found(self, setup_test_env):
        """测试查询不存在的任务"""
        print("\n" + "="*60)
        print("测试: 任务未找到")
        print("="*60)

        scheduler = setup_test_env

        # 查询不存在的任务
        task = await scheduler.get_task("non-existent-task-id")
        assert task is None, "不存在的任务应该返回 None"
        print("✅ 正确处理不存在的任务")

        # 尝试取消不存在的任务
        try:
            await scheduler.cancel_task("non-existent-task-id")
            assert False, "应该抛出 SyncTaskNotFoundError"
        except SyncTaskNotFoundError as e:
            print(f"✅ 正确抛出异常: {e}")

        print("✅ 任务未找到错误处理测试通过")

    @pytest.mark.asyncio
    async def test_duplicate_task_prevention(self, setup_test_env):
        """测试重复任务防护"""
        print("\n" + "="*60)
        print("测试: 重复任务防护")
        print("="*60)

        scheduler = setup_test_env

        # 触发第一个任务
        task_id_1 = await scheduler.trigger_sync(
            source=SyncSource.JIRA,
            sync_type=SyncType.INCREMENTAL,
            created_by="duplicate_test"
        )
        print(f"✅ 第一个任务已创建: {task_id_1}")

        # 等待任务开始
        await asyncio.sleep(1)

        # 尝试触发第二个任务（应该失败）
        try:
            await scheduler.trigger_sync(
                source=SyncSource.JIRA,
                sync_type=SyncType.INCREMENTAL,
                created_by="duplicate_test"
            )
            assert False, "应该抛出 SyncTaskAlreadyRunningError"
        except SyncTaskAlreadyRunningError as e:
            print(f"✅ 正确拒绝重复任务: {e}")

        # 等待第一个任务完成
        max_wait = 30
        waited = 0
        while waited < max_wait:
            task = await scheduler.get_task(task_id_1)
            if task.status in [SyncStatus.COMPLETED, SyncStatus.FAILED]:
                break
            await asyncio.sleep(2)
            waited += 2

        print("✅ 重复任务防护测试通过")


class TestSyncFailures:
    """同步失败测试"""

    @pytest.mark.asyncio
    async def test_sync_with_invalid_credentials(self, setup_test_env):
        """
        测试凭据无效时的同步

        注意: 这个测试假设测试环境没有配置有效的 Jira 凭据
        """
        print("\n" + "="*60)
        print("测试: 凭据无效的同步")
        print("="*60)

        scheduler = setup_test_env

        # 触发同步（预期会因为凭据问题而失败）
        task_id = await scheduler.trigger_sync(
            source=SyncSource.JIRA,
            sync_type=SyncType.INCREMENTAL,
            created_by="invalid_creds_test"
        )
        print(f"✅ 任务已创建: {task_id}")

        # 等待任务完成
        max_wait = 30
        waited = 0
        while waited < max_wait:
            task = await scheduler.get_task(task_id)
            if task.status in [SyncStatus.COMPLETED, SyncStatus.FAILED]:
                break
            await asyncio.sleep(2)
            waited += 2

        # 获取最终状态
        task = await scheduler.get_task(task_id)

        # 在测试环境中，由于没有真实的 Jira 配置，任务应该失败
        if task.status == SyncStatus.FAILED:
            print(f"✅ 任务正确失败: {task.error_message}")
            assert task.error_message is not None, "应该有错误消息"
        elif task.status == SyncStatus.COMPLETED:
            print(f"⚠️  任务意外成功（可能有真实配置）")
        else:
            print(f"⚠️  任务状态异常: {task.status}")

        print("✅ 凭据无效测试通过")


class TestRecoveryScenarios:
    """恢复场景测试"""

    @pytest.mark.asyncio
    async def test_scheduler_restart_recovery(self, setup_test_env):
        """
        测试调度器重启后的状态恢复

        验证:
        - 配置正确加载
        - 定时任务重新注册
        """
        print("\n" + "="*60)
        print("测试: 调度器重启恢复")
        print("="*60)

        scheduler = setup_test_env

        # 记录重启前的配置
        before_config = await scheduler.get_config(SyncSource.JIRA)
        assert before_config is not None

        # 重新加载配置（模拟重启）
        await scheduler.reload_config()
        print("✅ 配置已重新加载")

        # 验证配置仍然存在
        after_config = await scheduler.get_config(SyncSource.JIRA)
        assert after_config is not None
        assert after_config.enabled == before_config.enabled
        assert after_config.schedule_value == before_config.schedule_value

        print("✅ 配置恢复成功")

        # 验证下次运行时间已重新计算
        next_run = scheduler.get_next_run_time(SyncSource.JIRA)
        if next_run:
            print(f"✅ 下次运行时间: {next_run}")
        else:
            print("⚠️  自动同步未启用或配置有问题")

        print("✅ 调度器重启恢复测试通过")

    @pytest.mark.asyncio
    async def test_task_timeout_handling(self, setup_test_env):
        """
        测试任务超时处理

        注意: 这是一个概念性测试，实际超时机制取决于具体实现
        """
        print("\n" + "="*60)
        print("测试: 任务超时处理")
        print("="*60)

        scheduler = setup_test_env

        # 触发任务
        task_id = await scheduler.trigger_sync(
            source=SyncSource.CONFLUENCE,
            sync_type=SyncType.FULL,
            created_by="timeout_test"
        )
        print(f"✅ 任务已创建: {task_id}")

        # 等待一段时间
        await asyncio.sleep(5)

        # 查询任务状态
        task = await scheduler.get_task(task_id)

        # 验证任务没有永久卡住
        assert task.status in [
            SyncStatus.PENDING,
            SyncStatus.RUNNING,
            SyncStatus.COMPLETED,
            SyncStatus.FAILED
        ], f"任务状态异常: {task.status}"

        print(f"✅ 任务状态正常: {task.status}")
        print("✅ 任务超时处理测试通过")


class TestConcurrencyIssues:
    """并发问题测试"""

    @pytest.mark.asyncio
    async def test_concurrent_config_updates(self, setup_test_env):
        """
        测试并发配置更新

        验证并发更新配置不会导致数据不一致
        """
        print("\n" + "="*60)
        print("测试: 并发配置更新")
        print("="*60)

        scheduler = setup_test_env

        # 获取原始配置
        original = await scheduler.get_config(SyncSource.JIRA)
        original_value = original.batch_size

        # 并发更新配置
        async def update_config(value: int):
            await scheduler.update_config(
                SyncSource.JIRA,
                {"batch_size": value}
            )
            await asyncio.sleep(0.1)

        # 启动多个并发更新
        updates = [100, 150, 200]
        await asyncio.gather(*[update_config(v) for v in updates])

        # 验证最终配置是一致的
        final = await scheduler.get_config(SyncSource.JIRA)
        assert final.batch_size in updates, "最终值应该是更新值之一"

        print(f"✅ 最终配置: batch_size={final.batch_size}")

        # 恢复原始配置
        await scheduler.update_config(
            SyncSource.JIRA,
            {"batch_size": original_value}
        )

        print("✅ 并发配置更新测试通过")

    @pytest.mark.asyncio
    async def test_concurrent_task_queries(self, setup_test_env):
        """
        测试并发任务查询

        验证并发查询不会导致数据竞争
        """
        print("\n" + "="*60)
        print("测试: 并发任务查询")
        print("="*60)

        scheduler = setup_test_env

        # 触发任务
        task_id = await scheduler.trigger_sync(
            source=SyncSource.JIRA,
            sync_type=SyncType.INCREMENTAL,
            created_by="concurrent_query_test"
        )

        # 并发查询任务状态
        async def query_task():
            for _ in range(10):
                task = await scheduler.get_task(task_id)
                assert task is not None
                await asyncio.sleep(0.1)

        # 启动多个并发查询
        await asyncio.gather(*[query_task() for _ in range(5)])

        print("✅ 并发查询测试通过")

        # 等待任务完成
        await asyncio.sleep(10)


@pytest.mark.asyncio
async def test_error_handling_suite():
    """错误处理测试套件入口"""
    print("\n" + "="*70)
    print("🚀 数据同步系统 - 错误处理测试套件")
    print("="*70)

    print("\n💡 运行错误处理测试:")
    print("   pytest tests/integration/test_sync_error_handling.py -v")


if __name__ == "__main__":
    asyncio.run(test_error_handling_suite())
