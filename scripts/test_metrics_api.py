#!/usr/bin/env python3
"""
快速测试监控 API 端点

启动 FastAPI 服务器后运行此脚本：
python scripts/test_metrics_api.py
"""

import asyncio
import httpx
import json


async def test_metrics_endpoints():
    """测试所有监控端点"""
    base_url = "http://localhost:7860"

    async with httpx.AsyncClient(timeout=10.0) as client:
        print("=" * 60)
        print("测试监控 API 端点")
        print("=" * 60)

        # 1. 测试系统指标
        print("\n1. 系统指标 (/api/v1/metrics/system)")
        try:
            response = await client.get(f"{base_url}/api/v1/metrics/system")
            response.raise_for_status()
            data = response.json()
            print(f"   ✓ 状态码: {response.status_code}")
            print(f"   CPU: {data['data']['cpu_percent']}%")
            print(f"   内存: {data['data']['memory_percent']}%")
            print(f"   磁盘: {data['data']['disk_percent']}%")
        except Exception as e:
            print(f"   ✗ 失败: {e}")

        # 2. 测试数据库指标
        print("\n2. 数据库指标 (/api/v1/metrics/database)")
        try:
            response = await client.get(f"{base_url}/api/v1/metrics/database")
            response.raise_for_status()
            data = response.json()
            print(f"   ✓ 状态码: {response.status_code}")
            print(f"   连接池大小: {data['data']['pool_size']}")
            print(f"   已签出: {data['data']['pool_checked_out']}")
            print(f"   使用率: {data['data']['pool_usage_percent']}%")
        except Exception as e:
            print(f"   ✗ 失败: {e}")

        # 3. 测试 API 指标
        print("\n3. API 性能指标 (/api/v1/metrics/api)")
        try:
            response = await client.get(f"{base_url}/api/v1/metrics/api")
            response.raise_for_status()
            data = response.json()
            print(f"   ✓ 状态码: {response.status_code}")
            print(f"   总请求数: {data['data']['total_requests']}")
            print(f"   平均响应时间: {data['data']['avg_response_time_ms']:.2f}ms")
            print(f"   P95 响应时间: {data['data']['p95_response_time_ms']:.2f}ms")
        except Exception as e:
            print(f"   ✗ 失败: {e}")

        # 4. 测试检索指标
        print("\n4. 检索指标 (/api/v1/metrics/retrieval)")
        try:
            response = await client.get(f"{base_url}/api/v1/metrics/retrieval")
            response.raise_for_status()
            data = response.json()
            print(f"   ✓ 状态码: {response.status_code}")
            print(f"   总搜索次数: {data['data']['total_searches']}")
            print(f"   平均搜索时间: {data['data']['avg_search_time_ms']:.2f}ms")
        except Exception as e:
            print(f"   ✗ 失败: {e}")

        # 5. 测试所有指标
        print("\n5. 所有指标 (/api/v1/metrics/all)")
        try:
            response = await client.get(f"{base_url}/api/v1/metrics/all")
            response.raise_for_status()
            data = response.json()
            print(f"   ✓ 状态码: {response.status_code}")
            print(f"   包含指标: system, database, api, retrieval")
        except Exception as e:
            print(f"   ✗ 失败: {e}")

        print("\n" + "=" * 60)
        print("测试完成!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_metrics_endpoints())
