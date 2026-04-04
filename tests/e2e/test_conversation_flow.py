"""
对话历史端到端测试
Story 5.1 Phase 5
"""

import pytest
from httpx import AsyncClient


@pytest.fixture
def test_user_id():
    """测试用户 ID"""
    return "e2e_test_user"


@pytest.mark.e2e
class TestConversationFlow:
    """测试完整的对话流程"""

    @pytest.mark.asyncio
    async def test_complete_conversation_lifecycle(self, test_user_id):
        """测试完整的对话生命周期"""
        # 注意：此测试需要 FastAPI 服务器运行在 localhost:7860
        base_url = "http://localhost:7860"

        async with AsyncClient(base_url=base_url, timeout=30.0) as client:
            # 1. 创建对话
            create_response = await client.post(
                "/api/v1/conversations",
                params={"user_id": test_user_id},
                json={
                    "title": "Python 性能优化讨论",
                    "metadata": {"tag": "performance"}
                }
            )

            assert create_response.status_code == 201
            conversation_id = create_response.json()["data"]["id"]
            print(f"✅ 创建对话成功: {conversation_id}")

            # 2. 添加用户消息
            user_message_response = await client.post(
                f"/api/v1/conversations/{conversation_id}/messages",
                json={
                    "role": "user",
                    "content": "如何优化 Python 性能？"
                }
            )

            assert user_message_response.status_code == 201
            print("✅ 添加用户消息成功")

            # 3. 添加助手回复
            assistant_message_response = await client.post(
                f"/api/v1/conversations/{conversation_id}/messages",
                json={
                    "role": "assistant",
                    "content": "这里有几个 Python 性能优化建议：\\n1. 使用内置函数\\n2. 使用生成器\\n3. 使用 Cython",
                    "model_name": "qwen2.5:14b",
                    "token_count": 250
                }
            )

            assert assistant_message_response.status_code == 201
            print("✅ 添加助手回复成功")

            # 4. 获取对话详情
            detail_response = await client.get(
                f"/api/v1/conversations/{conversation_id}",
                params={"include_messages": True}
            )

            assert detail_response.status_code == 200
            detail_data = detail_response.json()["data"]
            assert detail_data["message_count"] == 2
            assert len(detail_data["messages"]) == 2
            print("✅ 获取对话详情成功")

            # 5. 搜索对话
            search_response = await client.get(
                "/api/v1/conversations/search",
                params={"user_id": test_user_id, "keyword": "Python"}
            )

            assert search_response.status_code == 200
            search_data = search_response.json()["data"]
            assert search_data["total"] >= 1
            print("✅ 搜索对话成功")

            # 6. 导出对话为 Markdown
            export_response = await client.get(
                f"/api/v1/conversations/{conversation_id}/export",
                params={"format": "markdown"}
            )

            assert export_response.status_code == 200
            markdown_content = export_response.content.decode("utf-8")
            assert "Python 性能优化讨论" in markdown_content
            assert "如何优化 Python 性能" in markdown_content
            print("✅ 导出 Markdown 成功")

            # 7. 获取统计信息
            stats_response = await client.get(
                "/api/v1/conversations/stats",
                params={"user_id": test_user_id}
            )

            assert stats_response.status_code == 200
            stats_data = stats_response.json()["data"]
            assert stats_data["total"] >= 1
            print("✅ 获取统计信息成功")

            # 8. 更新对话标题
            update_response = await client.put(
                f"/api/v1/conversations/{conversation_id}",
                json={"title": "Python 性能优化最佳实践"}
            )

            assert update_response.status_code == 200
            print("✅ 更新对话标题成功")

            # 9. 删除对话
            delete_response = await client.delete(
                f"/api/v1/conversations/{conversation_id}",
                params={"soft_delete": True}
            )

            assert delete_response.status_code == 200
            print("✅ 删除对话成功")

            # 10. 验证已删除
            get_deleted_response = await client.get(
                f"/api/v1/conversations/{conversation_id}"
            )

            assert get_deleted_response.status_code == 404
            print("✅ 验证删除成功")

            print("\\n🎉 完整对话流程测试通过！")

    @pytest.mark.asyncio
    async def test_multi_conversation_workflow(self, test_user_id):
        """测试多对话工作流"""
        base_url = "http://localhost:7860"

        async with AsyncClient(base_url=base_url, timeout=30.0) as client:
            conversation_ids = []

            # 1. 创建多个对话
            topics = ["Python", "Docker", "Kubernetes"]
            for topic in topics:
                response = await client.post(
                    "/api/v1/conversations",
                    params={"user_id": test_user_id},
                    json={"title": f"{topic} 学习笔记"}
                )
                assert response.status_code == 201
                conversation_ids.append(response.json()["data"]["id"])

            print(f"✅ 创建 {len(conversation_ids)} 个对话")

            # 2. 为每个对话添加消息
            for conv_id in conversation_ids:
                await client.post(
                    f"/api/v1/conversations/{conv_id}/messages",
                    json={
                        "role": "user",
                        "content": f"关于 {conv_id} 的问题"
                    }
                )

            print("✅ 为每个对话添加消息")

            # 3. 列出所有对话
            list_response = await client.get(
                "/api/v1/conversations",
                params={"user_id": test_user_id, "page": 1, "page_size": 20}
            )

            assert list_response.status_code == 200
            list_data = list_response.json()["data"]
            assert list_data["total"] >= len(topics)
            print(f"✅ 列出对话：总共 {list_data['total']} 个")

            # 4. 批量删除
            delete_response = await client.post(
                "/api/v1/conversations/batch-delete",
                params={
                    "conversation_ids": conversation_ids,
                    "soft_delete": True
                }
            )

            assert delete_response.status_code == 200
            assert delete_response.json()["data"]["deleted"] == len(conversation_ids)
            print(f"✅ 批量删除 {len(conversation_ids)} 个对话")

            print("\\n🎉 多对话工作流测试通过！")

    @pytest.mark.asyncio
    async def test_conversation_with_contexts(self, test_user_id):
        """测试带 RAG 上下文的对话"""
        base_url = "http://localhost:7860"

        async with AsyncClient(base_url=base_url, timeout=30.0) as client:
            # 创建对话
            create_response = await client.post(
                "/api/v1/conversations",
                params={"user_id": test_user_id},
                json={"title": "RAG 测试对话"}
            )

            conversation_id = create_response.json()["data"]["id"]

            # 添加带上下文的消息
            message_response = await client.post(
                f"/api/v1/conversations/{conversation_id}/messages",
                json={
                    "role": "assistant",
                    "content": "根据检索到的文档，这里是答案...",
                    "contexts": [
                        {
                            "doc_id": "doc-1",
                            "content": "相关文档内容1",
                            "score": 0.95
                        },
                        {
                            "doc_id": "doc-2",
                            "content": "相关文档内容2",
                            "score": 0.87
                        }
                    ],
                    "citations": [
                        {
                            "title": "Python 官方文档",
                            "url": "https://docs.python.org"
                        }
                    ]
                }
            )

            assert message_response.status_code == 201
            print("✅ 添加带上下文的消息成功")

            # 获取消息验证上下文
            messages_response = await client.get(
                f"/api/v1/conversations/{conversation_id}/messages"
            )

            messages_data = messages_response.json()["data"]["messages"]
            assert len(messages_data[0]["contexts"]) == 2
            assert len(messages_data[0]["citations"]) == 1
            print("✅ 上下文和引用保存成功")

            # 清理
            await client.delete(
                f"/api/v1/conversations/{conversation_id}",
                params={"soft_delete": True}
            )

            print("\\n🎉 带上下文对话测试通过！")


if __name__ == "__main__":
    import asyncio

    async def run_tests():
        """手动运行测试"""
        test = TestConversationFlow()
        test_user_id = "manual_test_user"

        print("=" * 60)
        print("开始端到端测试...")
        print("=" * 60)

        try:
            await test.test_complete_conversation_lifecycle(test_user_id)
            await test.test_multi_conversation_workflow(test_user_id)
            await test.test_conversation_with_contexts(test_user_id)

            print("=" * 60)
            print("✅ 所有测试通过！")
            print("=" * 60)

        except Exception as e:
            print(f"\\n❌ 测试失败: {e}")
            raise

    asyncio.run(run_tests())
