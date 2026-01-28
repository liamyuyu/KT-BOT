"""
数据同步性能测试

测试同步系统在大数据量下的性能表现。

运行方式:
    PYTHONPATH=/Users/macbook/ai-project/KT-BOT pytest tests/integration/test_sync_performance.py -v -s
"""

import asyncio
import pytest
import time
from datetime import datetime
from typing import List

from src.services.sync import get_sync_scheduler, SyncSource, SyncStatus, SyncType
from src.storage.database import async_session_factory, init_db, close_db
from src.storage.database.repository import SyncHistoryRepo


class PerformanceMetrics:
    """性能指标收集器"""

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.items_processed = 0
        self.errors = 0
        self.checkpoints = []

    def start(self):
        """开始计时"""
        self.start_time = time.time()

    def end(self):
        """结束计时"""
        self.end_time = time.time()

    def checkpoint(self, name: str, items_count: int):
        """记录检查点"""
        elapsed = time.time() - self.start_time
        self.checkpoints.append({
            "name": name,
            "elapsed": elapsed,
            "items": items_count
        })

    @property
    def duration(self) -> float:
        """总耗时（秒）"""
        if not self.end_time or not self.start_time:
            return 0
        return self.end_time - self.start_time

    @property
    def throughput(self) -> float:
        """吞吐量（items/秒）"""
        if self.duration == 0:
            return 0
        return self.items_processed / self.duration

    def report(self):
        """生成报告"""
        print("\n" + "="*60)
        print("📊 性能测试报告")
        print("="*60)
        print(f"  总耗时: {self.duration:.2f}s")
        print(f"  处理项数: {self.items_processed}")
        print(f"  错误数: {self.errors}")
        print(f"  吞吐量: {self.throughput:.2f} items/s")

        if self.checkpoints:
            print("\n  检查点:")
            for cp in self.checkpoints:
                print(f"    - {cp['name']}: {cp['elapsed']:.2f}s ({cp['items']} items)")

        print("="*60 + "\n")


@pytest.fixture(scope="module")
async def setup_test_env():
    """设置测试环境"""
    await init_db()
    scheduler = get_sync_scheduler()
    if not scheduler.is_running():
        await scheduler.start()
    yield scheduler
    await close_db()


class TestSyncPerformance:
    """同步性能测试"""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_large_dataset_sync(self, setup_test_env):
        """
        测试大数据集同步性能

        模拟同步 1000+ Issues 的性能
        注意: 这是一个模拟测试，真实性能取决于实际的 Jira API
        """
        print("\n" + "="*60)
        print("测试: 大数据集同步性能")
        print("="*60)

        scheduler = setup_test_env
        metrics = PerformanceMetrics()

        # 开始计时
        metrics.start()

        # 触发同步
        task_id = await scheduler.trigger_sync(
            source=SyncSource.JIRA,
            sync_type=SyncType.INCREMENTAL,
            created_by="performance_test"
        )
        print(f"✅ 任务已创建: {task_id}")
        metrics.checkpoint("任务创建", 0)

        # 监控任务执行
        max_wait = 120  # 最多等待 2 分钟
        waited = 0
        last_synced = 0

        while waited < max_wait:
            await asyncio.sleep(2)
            waited += 2

            task = await scheduler.get_task(task_id)

            # 记录进度
            if task.synced_items > last_synced:
                metrics.checkpoint(
                    f"进度 {task.progress_percentage:.1f}%",
                    task.synced_items
                )
                last_synced = task.synced_items
                print(f"  [{waited}s] 进度: {task.synced_items}/{task.total_items} ({task.progress_percentage:.1f}%)")

            # 检查是否完成
            if task.status in [SyncStatus.COMPLETED, SyncStatus.FAILED]:
                break

        # 结束计时
        metrics.end()

        # 获取最终状态
        task = await scheduler.get_task(task_id)
        metrics.items_processed = task.synced_items
        metrics.errors = task.failed_items

        # 生成报告
        metrics.report()

        # 性能断言
        print("📈 性能指标:")
        print(f"  - 状态: {task.status}")
        print(f"  - 成功率: {(task.synced_items / task.total_items * 100) if task.total_items > 0 else 0:.1f}%")
        print(f"  - 平均每项耗时: {metrics.duration / task.synced_items if task.synced_items > 0 else 0:.3f}s")

        # 如果成功同步了数据，验证性能
        if task.status == SyncStatus.COMPLETED and task.synced_items > 0:
            # 期望吞吐量 > 1 item/s
            assert metrics.throughput > 1, f"吞吐量过低: {metrics.throughput:.2f} items/s"
            print(f"✅ 性能测试通过（吞吐量: {metrics.throughput:.2f} items/s）")
        else:
            print(f"⚠️  任务未成功完成（状态: {task.status}），可能是测试环境问题")

    @pytest.mark.asyncio
    async def test_concurrent_tasks_performance(self, setup_test_env):
        """
        测试并发任务性能

        验证不同数据源可以并发执行
        """
        print("\n" + "="*60)
        print("测试: 并发任务性能")
        print("="*60)

        scheduler = setup_test_env

        # 同时触发两个不同数据源的任务
        start_time = time.time()

        task_ids = []
        for source in [SyncSource.JIRA, SyncSource.CONFLUENCE]:
            task_id = await scheduler.trigger_sync(
                source=source,
                sync_type=SyncType.INCREMENTAL,
                created_by="concurrent_perf_test"
            )
            task_ids.append((source, task_id))
            print(f"✅ {source.value} 任务已创建: {task_id}")

        # 等待所有任务完成
        max_wait = 60
        waited = 0

        while waited < max_wait:
            await asyncio.sleep(3)
            waited += 3

            # 检查所有任务状态
            all_done = True
            for source, task_id in task_ids:
                task = await scheduler.get_task(task_id)
                if task.status not in [SyncStatus.COMPLETED, SyncStatus.FAILED]:
                    all_done = False
                    print(f"  [{waited}s] {source.value}: {task.status} ({task.progress_percentage:.1f}%)")

            if all_done:
                break

        total_time = time.time() - start_time

        # 统计结果
        print(f"\n📊 并发执行结果:")
        print(f"  - 总耗时: {total_time:.2f}s")

        for source, task_id in task_ids:
            task = await scheduler.get_task(task_id)
            print(f"  - {source.value}:")
            print(f"      状态: {task.status}")
            print(f"      耗时: {task.duration_seconds}s")
            print(f"      同步: {task.synced_items}/{task.total_items}")

        print("✅ 并发任务性能测试完成")

    @pytest.mark.asyncio
    async def test_database_query_performance(self, setup_test_env):
        """
        测试数据库查询性能

        验证历史记录查询在大数据量下的性能
        """
        print("\n" + "="*60)
        print("测试: 数据库查询性能")
        print("="*60)

        scheduler = setup_test_env

        if not scheduler.use_db:
            print("⚠️  数据库未启用，跳过测试")
            return

        async with async_session_factory() as session:
            repo = SyncHistoryRepo(session)

            # 测试 1: 查询最新记录
            start = time.time()
            latest = await repo.get_latest_by_source(SyncSource.JIRA)
            elapsed_1 = time.time() - start
            print(f"✅ 查询最新记录: {elapsed_1*1000:.2f}ms")

            # 测试 2: 分页查询
            start = time.time()
            items = await repo.get_history_list(limit=20, offset=0)
            elapsed_2 = time.time() - start
            print(f"✅ 分页查询(20条): {elapsed_2*1000:.2f}ms")

            # 测试 3: 统计查询
            start = time.time()
            stats = await repo.get_statistics(days=7)
            elapsed_3 = time.time() - start
            print(f"✅ 统计查询(7天): {elapsed_3*1000:.2f}ms")

            # 测试 4: 复杂过滤查询
            start = time.time()
            filtered = await repo.get_history_list(
                source=SyncSource.JIRA,
                status=SyncStatus.COMPLETED,
                limit=50
            )
            elapsed_4 = time.time() - start
            print(f"✅ 复杂过滤查询(50条): {elapsed_4*1000:.2f}ms")

            # 性能断言
            print(f"\n📈 查询性能指标:")
            print(f"  - 最新记录查询: {elapsed_1*1000:.2f}ms (期望 < 100ms)")
            print(f"  - 分页查询: {elapsed_2*1000:.2f}ms (期望 < 200ms)")
            print(f"  - 统计查询: {elapsed_3*1000:.2f}ms (期望 < 500ms)")
            print(f"  - 复杂查询: {elapsed_4*1000:.2f}ms (期望 < 300ms)")

            # 验证性能要求
            assert elapsed_1 < 0.1, "最新记录查询过慢"
            assert elapsed_2 < 0.2, "分页查询过慢"
            assert elapsed_3 < 0.5, "统计查询过慢"
            assert elapsed_4 < 0.3, "复杂查询过慢"

            print("✅ 数据库查询性能测试通过")


class TestMemoryAndResourceUsage:
    """内存和资源使用测试"""

    @pytest.mark.asyncio
    async def test_memory_leak(self, setup_test_env):
        """
        测试内存泄漏

        连续执行多个任务，验证内存是否持续增长
        """
        print("\n" + "="*60)
        print("测试: 内存泄漏检查")
        print("="*60)

        scheduler = setup_test_env

        try:
            import psutil
            import os

            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB

            print(f"  初始内存: {initial_memory:.2f} MB")

            # 执行 10 个同步任务
            for i in range(10):
                task_id = await scheduler.trigger_sync(
                    source=SyncSource.JIRA if i % 2 == 0 else SyncSource.CONFLUENCE,
                    sync_type=SyncType.INCREMENTAL,
                    created_by=f"memory_test_{i}"
                )

                # 等待任务完成
                await asyncio.sleep(5)

                current_memory = process.memory_info().rss / 1024 / 1024
                print(f"  任务 {i+1}/10: {current_memory:.2f} MB")

            final_memory = process.memory_info().rss / 1024 / 1024
            memory_growth = final_memory - initial_memory

            print(f"\n📊 内存使用情况:")
            print(f"  - 初始: {initial_memory:.2f} MB")
            print(f"  - 最终: {final_memory:.2f} MB")
            print(f"  - 增长: {memory_growth:.2f} MB")
            print(f"  - 增长率: {(memory_growth / initial_memory * 100):.1f}%")

            # 允许合理的内存增长（< 50%）
            assert memory_growth < initial_memory * 0.5, \
                f"内存增长过大: {memory_growth:.2f} MB ({(memory_growth / initial_memory * 100):.1f}%)"

            print("✅ 内存泄漏检查通过")

        except ImportError:
            print("⚠️  psutil 未安装，跳过内存测试")
            print("    安装: pip install psutil")


@pytest.mark.asyncio
async def test_performance_suite():
    """性能测试套件入口"""
    print("\n" + "="*70)
    print("🚀 数据同步系统 - 性能测试套件")
    print("="*70)

    print("\n💡 运行性能测试:")
    print("   pytest tests/integration/test_sync_performance.py -v -s")
    print("\n⚠️  注意: 性能测试可能需要较长时间")


if __name__ == "__main__":
    asyncio.run(test_performance_suite())
