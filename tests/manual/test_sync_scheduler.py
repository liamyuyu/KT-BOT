"""
同步调度器手动测试脚本

用于快速验证 SyncScheduler 的基本功能。

运行方式:
    python tests/manual/test_sync_scheduler.py
"""

import asyncio
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_scheduler_basic():
    """测试调度器基本功能"""
    print("\n" + "="*60)
    print("测试 1: 调度器基本功能")
    print("="*60 + "\n")

    from src.services.sync import get_sync_scheduler, SyncSource, SyncType

    # 获取调度器实例
    scheduler = get_sync_scheduler()
    logger.info("✅ 调度器实例创建成功")

    # 启动调度器
    await scheduler.start()
    logger.info("✅ 调度器启动成功")

    # 检查状态
    assert scheduler.is_running(), "调度器应该处于运行状态"
    logger.info("✅ 调度器运行状态正常")

    # 查看配置
    jira_config = await scheduler.get_config(SyncSource.JIRA)
    if jira_config:
        logger.info(f"✅ Jira 配置加载成功: enabled={jira_config.enabled}, schedule={jira_config.schedule_value}")

    confluence_config = await scheduler.get_config(SyncSource.CONFLUENCE)
    if confluence_config:
        logger.info(f"✅ Confluence 配置加载成功: enabled={confluence_config.enabled}, schedule={confluence_config.schedule_value}")

    # 关闭调度器
    await scheduler.shutdown(wait=False)
    logger.info("✅ 调度器关闭成功")

    print("\n✅ 测试 1 通过！\n")


async def test_manual_trigger():
    """测试手动触发同步"""
    print("\n" + "="*60)
    print("测试 2: 手动触发同步")
    print("="*60 + "\n")

    from src.services.sync import get_sync_scheduler, SyncSource, SyncType, SyncStatus

    scheduler = get_sync_scheduler()
    await scheduler.start()

    try:
        # 手动触发 Jira 增量同步
        logger.info("触发 Jira 增量同步...")
        task_id = await scheduler.trigger_sync(
            source=SyncSource.JIRA,
            sync_type=SyncType.INCREMENTAL,
            created_by="test_script"
        )
        logger.info(f"✅ 同步任务已创建: task_id={task_id}")

        # 等待一会儿让任务开始执行
        await asyncio.sleep(2)

        # 查询任务状态
        task = await scheduler.get_task(task_id)
        if task:
            logger.info(
                f"✅ 任务状态查询成功: "
                f"status={task.status}, "
                f"synced={task.synced_items}/{task.total_items}"
            )
        else:
            logger.error("❌ 任务未找到")

        # 获取所有运行中的任务
        running_tasks = await scheduler.get_running_tasks()
        logger.info(f"✅ 运行中的任务数量: {len(running_tasks)}")

        # 等待任务完成
        logger.info("等待任务完成...")
        await asyncio.sleep(5)

        # 再次查询状态
        task = await scheduler.get_task(task_id)
        if task:
            logger.info(
                f"✅ 最终任务状态: "
                f"status={task.status}, "
                f"duration={task.duration_seconds}s"
            )

        print("\n✅ 测试 2 通过！\n")

    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        raise

    finally:
        await scheduler.shutdown(wait=False)


async def test_next_run_time():
    """测试下次运行时间查询"""
    print("\n" + "="*60)
    print("测试 3: 下次运行时间查询")
    print("="*60 + "\n")

    from src.services.sync import get_sync_scheduler, SyncSource

    scheduler = get_sync_scheduler()
    await scheduler.start()

    try:
        # 查询 Jira 下次运行时间
        jira_next_run = scheduler.get_next_run_time(SyncSource.JIRA)
        if jira_next_run:
            logger.info(f"✅ Jira 下次同步时间: {jira_next_run}")
        else:
            logger.warning("⚠️  Jira 自动同步未启用")

        # 查询 Confluence 下次运行时间
        confluence_next_run = scheduler.get_next_run_time(SyncSource.CONFLUENCE)
        if confluence_next_run:
            logger.info(f"✅ Confluence 下次同步时间: {confluence_next_run}")
        else:
            logger.warning("⚠️  Confluence 自动同步未启用")

        print("\n✅ 测试 3 通过！\n")

    finally:
        await scheduler.shutdown(wait=False)


async def test_config_update():
    """测试配置更新"""
    print("\n" + "="*60)
    print("测试 4: 配置更新")
    print("="*60 + "\n")

    from src.services.sync import get_sync_scheduler, SyncSource

    scheduler = get_sync_scheduler()
    await scheduler.start()

    try:
        # 获取原始配置
        config = await scheduler.get_config(SyncSource.JIRA)
        original_batch_size = config.batch_size if config else None
        logger.info(f"原始批量大小: {original_batch_size}")

        # 更新配置
        await scheduler.update_config(
            SyncSource.JIRA,
            {"batch_size": 100}
        )
        logger.info("✅ 配置更新成功")

        # 验证更新
        updated_config = await scheduler.get_config(SyncSource.JIRA)
        assert updated_config.batch_size == 100, "批量大小应该更新为 100"
        logger.info(f"✅ 验证配置更新成功: batch_size={updated_config.batch_size}")

        # 恢复原始配置
        if original_batch_size:
            await scheduler.update_config(
                SyncSource.JIRA,
                {"batch_size": original_batch_size}
            )
            logger.info(f"✅ 恢复原始配置: batch_size={original_batch_size}")

        print("\n✅ 测试 4 通过！\n")

    finally:
        await scheduler.shutdown(wait=False)


async def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("🚀 同步调度器测试套件")
    print("="*60)

    tests = [
        ("基本功能", test_scheduler_basic),
        ("手动触发", test_manual_trigger),
        ("运行时间查询", test_next_run_time),
        ("配置更新", test_config_update),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            await test_func()
            passed += 1
        except Exception as e:
            logger.error(f"❌ 测试失败: {name} - {e}")
            failed += 1

    # 汇总结果
    print("\n" + "="*60)
    print("📊 测试结果汇总")
    print("="*60)
    print(f"✅ 通过: {passed}/{len(tests)}")
    print(f"❌ 失败: {failed}/{len(tests)}")
    print("="*60 + "\n")

    if failed == 0:
        print("🎉 所有测试通过！")
    else:
        print(f"⚠️  有 {failed} 个测试失败")


if __name__ == "__main__":
    asyncio.run(main())
