"""
手动测试脚本：验证流式响应功能
运行方式：
1. 启动 FastAPI: uvicorn src.api.main:app --reload --port 7860
2. 运行此脚本: python tests/manual/test_streaming.py
"""
import asyncio
import httpx
import json


async def test_streaming_chat():
    """测试流式对话"""
    url = "http://localhost:7860/api/v1/chat/stream"

    # 测试请求
    request_data = {
        "message": "什么是 Python？请简单介绍一下。",
        "enable_rag": False,  # 先测试不带 RAG 的情况
        "temperature": 0.7
    }

    print("=" * 60)
    print("测试流式对话 API")
    print("=" * 60)
    print(f"\n请求: {json.dumps(request_data, ensure_ascii=False, indent=2)}\n")
    print("响应事件流:\n")

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                url,
                json=request_data,
                headers={"Accept": "text/event-stream"}
            ) as response:
                if response.status_code != 200:
                    print(f"❌ 错误: HTTP {response.status_code}")
                    print(await response.aread())
                    return

                session_id = None
                full_message = ""

                async for line in response.aiter_lines():
                    if not line:
                        continue

                    # 解析 SSE 事件
                    if line.startswith("event:"):
                        event_type = line[6:].strip()
                        print(f"\n📡 事件: {event_type}")

                    elif line.startswith("data:"):
                        data_str = line[5:].strip()
                        try:
                            data = json.loads(data_str)

                            if event_type == "start":
                                session_id = data.get("session_id")
                                print(f"   会话 ID: {session_id}")

                            elif event_type == "context":
                                contexts = data.get("contexts", [])
                                print(f"   检索到 {len(contexts)} 个上下文")

                            elif event_type == "token":
                                content = data.get("content", "")
                                full_message += content
                                print(content, end="", flush=True)

                            elif event_type == "end":
                                print(f"\n\n✅ 完成")
                                print(f"   模型: {data.get('model')}")
                                print(f"   Token 数: {data.get('token_count')}")
                                print(f"   耗时: {data.get('duration_ms')}ms")

                            elif event_type == "error":
                                print(f"❌ 错误: {data.get('message')}")

                        except json.JSONDecodeError:
                            print(f"   (无法解析 JSON: {data_str})")

                print("\n" + "=" * 60)
                print(f"完整响应:\n{full_message}")
                print("=" * 60)

    except httpx.ConnectError:
        print("❌ 无法连接到 FastAPI 服务器")
        print("   请确保已启动: uvicorn src.api.main:app --reload --port 7860")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


async def test_streaming_with_rag():
    """测试带 RAG 的流式对话"""
    url = "http://localhost:7860/api/v1/chat/stream"

    request_data = {
        "message": "JIRA 中如何创建新的工作项？",
        "enable_rag": True,
        "rag_top_k": 3,
        "temperature": 0.7
    }

    print("\n\n" + "=" * 60)
    print("测试流式对话 + RAG")
    print("=" * 60)
    print(f"\n请求: {json.dumps(request_data, ensure_ascii=False, indent=2)}\n")
    print("响应事件流:\n")

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                url,
                json=request_data,
                headers={"Accept": "text/event-stream"}
            ) as response:
                if response.status_code != 200:
                    print(f"❌ 错误: HTTP {response.status_code}")
                    return

                full_message = ""
                event_type = None

                async for line in response.aiter_lines():
                    if not line:
                        continue

                    if line.startswith("event:"):
                        event_type = line[6:].strip()
                        print(f"\n📡 {event_type}")

                    elif line.startswith("data:"):
                        data_str = line[5:].strip()
                        try:
                            data = json.loads(data_str)

                            if event_type == "start":
                                print(f"   会话: {data.get('session_id')}")

                            elif event_type == "context":
                                contexts = data.get("contexts", [])
                                print(f"   检索到 {len(contexts)} 个相关文档:")
                                for i, ctx in enumerate(contexts, 1):
                                    print(f"   [{i}] {ctx.get('source', {}).get('issue_key', 'N/A')} "
                                          f"(分数: {ctx.get('score', 0):.3f})")

                            elif event_type == "token":
                                content = data.get("content", "")
                                full_message += content
                                print(content, end="", flush=True)

                            elif event_type == "end":
                                print(f"\n\n✅ 完成 ({data.get('duration_ms')}ms)")

                            elif event_type == "error":
                                print(f"❌ {data.get('message')}")

                        except json.JSONDecodeError:
                            pass

                print("\n" + "=" * 60)

    except Exception as e:
        print(f"❌ 测试失败: {e}")


if __name__ == "__main__":
    print("开始测试流式响应功能...\n")

    # 运行测试
    asyncio.run(test_streaming_chat())

    # 如果上一个测试成功，继续测试 RAG
    print("\n\n继续测试 RAG 功能？(Enter 继续, Ctrl+C 退出)")
    try:
        input()
        asyncio.run(test_streaming_with_rag())
    except KeyboardInterrupt:
        print("\n\n测试结束")
