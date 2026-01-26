#!/usr/bin/env python3
"""
同步 API 手动测试脚本

用于测试同步管理 API 的各个端点。

运行方式:
    # 确保 API 服务器正在运行
    uvicorn src.api.main:app --reload
    
    # 运行测试
    python tests/manual/test_sync_api.py
"""

import asyncio
import httpx
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1/sync"


async def test_get_all_configs():
    """测试获取所有配置"""
    print("\n" + "="*60)
    print("测试 1: 获取所有同步配置")
    print("="*60 + "\n")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/config")
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 获取配置成功，共 {len(data)} 个数据源")
            for config in data:
                print(f"  - {config['source']}: enabled={config['enabled']}, schedule={config['schedule_value']}")
        else:
            print(f"❌ 请求失败: {response.text}")


async def test_get_config_by_source():
    """测试获取指定数据源配置"""
    print("\n" + "="*60)
    print("测试 2: 获取 Jira 配置")
    print("="*60 + "\n")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/config/jira")
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            config = response.json()
            print(f"✅ 获取 Jira 配置成功")
            print(f"  - enabled: {config['enabled']}")
            print(f"  - schedule_type: {config['schedule_type']}")
            print(f"  - schedule_value: {config['schedule_value']}")
            print(f"  - batch_size: {config['batch_size']}")
            print(f"  - last_sync_time: {config.get('last_sync_time', 'N/A')}")
            print(f"  - next_run_time: {config.get('next_run_time', 'N/A')}")
        else:
            print(f"❌ 请求失败: {response.text}")


async def test_trigger_sync():
    """测试触发同步"""
    print("\n" + "="*60)
    print("测试 3: 触发 Jira 增量同步")
    print("="*60 + "\n")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/trigger/jira",
            json={
                "sync_type": "incremental",
                "created_by": "test_api"
            }
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 同步任务已创建")
            print(f"  - task_id: {data['task_id']}")
            print(f"  - message: {data['message']}")
            return data['task_id']
        elif response.status_code == 409:
            print(f"⚠️  任务已在运行中: {response.json()['detail']}")
        else:
            print(f"❌ 请求失败: {response.text}")
        
        return None


async def test_get_task_status(task_id: str):
    """测试查询任务状态"""
    print("\n" + "="*60)
    print("测试 4: 查询任务状态")
    print("="*60 + "\n")
    
    if not task_id:
        print("⚠️  没有任务ID，跳过测试")
        return
    
    async with httpx.AsyncClient() as client:
        # 等待一会儿让任务开始执行
        await asyncio.sleep(2)
        
        response = await client.get(f"{BASE_URL}/status/{task_id}")
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            task = response.json()
            print(f"✅ 查询任务状态成功")
            print(f"  - task_id: {task['task_id']}")
            print(f"  - source: {task['source']}")
            print(f"  - status: {task['status']}")
            print(f"  - progress: {task['progress_percentage']}%")
            print(f"  - synced: {task['synced_items']}/{task['total_items']}")
            
            if task['error_message']:
                print(f"  - error: {task['error_message']}")
        else:
            print(f"❌ 请求失败: {response.text}")


async def test_get_running_tasks():
    """测试查询运行中的任务"""
    print("\n" + "="*60)
    print("测试 5: 查询运行中的任务")
    print("="*60 + "\n")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/status/running")
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 运行中的任务数量: {data['count']}")
            for task in data['tasks']:
                print(f"  - {task['task_id']}: {task['source']} - {task['status']} ({task['progress_percentage']}%)")
        else:
            print(f"❌ 请求失败: {response.text}")


async def test_get_next_run_time():
    """测试查询下次运行时间"""
    print("\n" + "="*60)
    print("测试 6: 查询下次运行时间")
    print("="*60 + "\n")
    
    async with httpx.AsyncClient() as client:
        for source in ["jira", "confluence"]:
            response = await client.get(f"{BASE_URL}/next-run/{source}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {source.capitalize()} 下次同步时间: {data.get('next_run_time', 'N/A')}")
                print(f"  - enabled: {data['enabled']}")
                print(f"  - schedule: {data['schedule_type']} = {data['schedule_value']}")
            else:
                print(f"❌ {source} 请求失败: {response.text}")


async def test_get_history():
    """测试查询历史记录"""
    print("\n" + "="*60)
    print("测试 7: 查询历史记录")
    print("="*60 + "\n")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/history",
            params={
                "page": 1,
                "page_size": 10
            }
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 历史记录查询成功")
            print(f"  - 总数: {data['total']}")
            print(f"  - 当前页: {data['page']}")
            print(f"  - 每页大小: {data['page_size']}")
            print(f"  - 返回记录数: {len(data['items'])}")
            
            if data['items']:
                print("\n  最近的记录:")
                for item in data['items'][:3]:
                    print(f"    - {item['task_id']}: {item['source']} - {item['status']} - {item['start_time']}")
        else:
            print(f"❌ 请求失败: {response.text}")


async def test_get_statistics():
    """测试查询统计信息"""
    print("\n" + "="*60)
    print("测试 8: 查询统计信息")
    print("="*60 + "\n")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/statistics",
            params={"days": 7}
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ 统计信息查询成功（最近 {stats['period_days']} 天）")
            print(f"  - 总同步次数: {stats['total_syncs']}")
            print(f"  - 成功次数: {stats['successful_syncs']}")
            print(f"  - 失败次数: {stats['failed_syncs']}")
            print(f"  - 成功率: {stats['success_rate']}%")
            print(f"  - 总同步项数: {stats['total_items_synced']}")
            print(f"  - 平均耗时: {stats['avg_duration_seconds']}s")
        else:
            print(f"❌ 请求失败: {response.text}")


async def test_get_scheduler_status():
    """测试查询调度器状态"""
    print("\n" + "="*60)
    print("测试 9: 查询调度器状态")
    print("="*60 + "\n")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/scheduler/status")
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            status = response.json()
            print(f"✅ 调度器状态查询成功")
            print(f"  - 运行中: {status['is_running']}")
            print(f"  - 总任务数: {status['total_tasks']}")
            print(f"  - 运行中任务数: {status['running_tasks']}")
            
            if status.get('jira_config'):
                print(f"  - Jira: enabled={status['jira_config']['enabled']}")
            
            if status.get('confluence_config'):
                print(f"  - Confluence: enabled={status['confluence_config']['enabled']}")
        else:
            print(f"❌ 请求失败: {response.text}")


async def test_update_config():
    """测试更新配置"""
    print("\n" + "="*60)
    print("测试 10: 更新配置（批量大小）")
    print("="*60 + "\n")
    
    async with httpx.AsyncClient() as client:
        # 更新批量大小
        response = await client.put(
            f"{BASE_URL}/config/jira",
            json={"batch_size": 100}
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            config = response.json()
            print(f"✅ 配置更新成功")
            print(f"  - batch_size: {config['batch_size']}")
            
            # 恢复原始值
            await asyncio.sleep(1)
            await client.put(
                f"{BASE_URL}/config/jira",
                json={"batch_size": 50}
            )
            print(f"  - 已恢复原始值 batch_size=50")
        else:
            print(f"❌ 请求失败: {response.text}")


async def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("🚀 同步 API 测试套件")
    print("="*60)
    print("\n💡 注意: 请确保 API 服务器正在运行")
    print("   uvicorn src.api.main:app --reload\n")
    
    try:
        # 测试配置管理 API
        await test_get_all_configs()
        await test_get_config_by_source()
        await test_update_config()
        
        # 测试任务触发 API
        task_id = await test_trigger_sync()
        await test_get_task_status(task_id)
        await test_get_running_tasks()
        
        # 测试状态查询 API
        await test_get_next_run_time()
        await test_get_scheduler_status()
        
        # 测试历史记录 API
        await test_get_history()
        await test_get_statistics()
        
        print("\n" + "="*60)
        print("✨ 测试完成！")
        print("="*60 + "\n")
        
    except httpx.ConnectError:
        print("\n❌ 无法连接到 API 服务器")
        print("   请确保服务器正在运行: uvicorn src.api.main:app --reload\n")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
