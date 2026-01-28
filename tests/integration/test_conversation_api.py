"""
对话历史 API 集成测试
Story 5.1 Phase 5
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.api.main import create_fastapi_app
from src.storage.database.base import Base


@pytest.fixture
async def test_db_engine():
    """创建测试数据库引擎"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
async def test_db_session(test_db_engine):
    """创建测试数据库会话"""
    async_session_factory = sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session_factory() as session:
        yield session


@pytest.fixture
async def client(test_db_session):
    """创建测试客户端"""
    app = create_fastapi_app()

    # Override database dependency
    from src.storage.database import get_db

    async def override_get_db():
        yield test_db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def test_user_id():
    """测试用户 ID"""
    return "test_user_123"


@pytest.mark.integration
class TestConversationAPI:
    """测试对话历史 API"""

    @pytest.mark.asyncio
    async def test_create_conversation(self, client, test_user_id):
        """测试创建对话"""
        response = await client.post(
            "/api/v1/conversations",
            params={"user_id": test_user_id},
            json={
                "title": "测试对话",
                "metadata": {"test": True}
            }
        )

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["title"] == "测试对话"
        assert data["user_id"] == test_user_id
        assert data["message_count"] == 0

    @pytest.mark.asyncio
    async def test_list_conversations(self, client, test_user_id):
        """测试对话列表"""
        # 创建几个对话
        for i in range(3):
            await client.post(
                "/api/v1/conversations",
                params={"user_id": test_user_id},
                json={"title": f"对话 {i+1}"}
            )

        # 获取列表
        response = await client.get(
            "/api/v1/conversations",
            params={"user_id": test_user_id, "page": 1, "page_size": 10}
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["total"] == 3
        assert len(data["conversations"]) == 3

    @pytest.mark.asyncio
    async def test_search_conversations(self, client, test_user_id):
        """测试搜索对话"""
        # 创建对话
        await client.post(
            "/api/v1/conversations",
            params={"user_id": test_user_id},
            json={"title": "Python 性能优化"}
        )
        await client.post(
            "/api/v1/conversations",
            params={"user_id": test_user_id},
            json={"title": "Docker 部署"}
        )

        # 搜索
        response = await client.get(
            "/api/v1/conversations/search",
            params={"user_id": test_user_id, "keyword": "Python"}
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["total"] == 1
        assert "Python" in data["conversations"][0]["title"]

    @pytest.mark.asyncio
    async def test_get_conversation(self, client, test_user_id):
        """测试获取对话详情"""
        # 创建对话
        create_response = await client.post(
            "/api/v1/conversations",
            params={"user_id": test_user_id},
            json={"title": "测试对话"}
        )
        conversation_id = create_response.json()["data"]["id"]

        # 获取详情
        response = await client.get(
            f"/api/v1/conversations/{conversation_id}",
            params={"include_messages": True}
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["id"] == conversation_id
        assert data["title"] == "测试对话"
        assert "messages" in data

    @pytest.mark.asyncio
    async def test_get_conversation_not_found(self, client):
        """测试获取不存在的对话"""
        response = await client.get(
            "/api/v1/conversations/nonexistent"
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_conversation(self, client, test_user_id):
        """测试更新对话"""
        # 创建对话
        create_response = await client.post(
            "/api/v1/conversations",
            params={"user_id": test_user_id},
            json={"title": "原标题"}
        )
        conversation_id = create_response.json()["data"]["id"]

        # 更新对话
        response = await client.put(
            f"/api/v1/conversations/{conversation_id}",
            json={"title": "新标题"}
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["title"] == "新标题"

    @pytest.mark.asyncio
    async def test_delete_conversation(self, client, test_user_id):
        """测试删除对话"""
        # 创建对话
        create_response = await client.post(
            "/api/v1/conversations",
            params={"user_id": test_user_id},
            json={"title": "待删除对话"}
        )
        conversation_id = create_response.json()["data"]["id"]

        # 删除对话
        response = await client.delete(
            f"/api/v1/conversations/{conversation_id}",
            params={"soft_delete": True}
        )

        assert response.status_code == 200

        # 验证已删除
        get_response = await client.get(
            f"/api/v1/conversations/{conversation_id}"
        )
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_batch_delete_conversations(self, client, test_user_id):
        """测试批量删除对话"""
        # 创建多个对话
        conv_ids = []
        for i in range(3):
            create_response = await client.post(
                "/api/v1/conversations",
                params={"user_id": test_user_id},
                json={"title": f"对话 {i+1}"}
            )
            conv_ids.append(create_response.json()["data"]["id"])

        # 批量删除
        response = await client.post(
            "/api/v1/conversations/batch-delete",
            params={
                "conversation_ids": conv_ids,
                "soft_delete": True
            }
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["deleted"] == 3

    @pytest.mark.asyncio
    async def test_add_message(self, client, test_user_id):
        """测试添加消息"""
        # 创建对话
        create_response = await client.post(
            "/api/v1/conversations",
            params={"user_id": test_user_id},
            json={"title": "测试对话"}
        )
        conversation_id = create_response.json()["data"]["id"]

        # 添加消息
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            json={
                "role": "user",
                "content": "测试消息",
                "model_name": "qwen2.5:14b",
                "token_count": 10
            }
        )

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["content"] == "测试消息"
        assert data["role"] == "user"

    @pytest.mark.asyncio
    async def test_get_messages(self, client, test_user_id):
        """测试获取消息列表"""
        # 创建对话
        create_response = await client.post(
            "/api/v1/conversations",
            params={"user_id": test_user_id},
            json={"title": "测试对话"}
        )
        conversation_id = create_response.json()["data"]["id"]

        # 添加多条消息
        for i in range(3):
            await client.post(
                f"/api/v1/conversations/{conversation_id}/messages",
                json={
                    "role": "user",
                    "content": f"消息 {i+1}"
                }
            )

        # 获取消息列表
        response = await client.get(
            f"/api/v1/conversations/{conversation_id}/messages",
            params={"page": 1, "page_size": 10}
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["count"] == 3
        assert len(data["messages"]) == 3

    @pytest.mark.asyncio
    async def test_delete_message(self, client, test_user_id):
        """测试删除消息"""
        # 创建对话并添加消息
        create_response = await client.post(
            "/api/v1/conversations",
            params={"user_id": test_user_id},
            json={"title": "测试对话"}
        )
        conversation_id = create_response.json()["data"]["id"]

        message_response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            json={
                "role": "user",
                "content": "待删除消息"
            }
        )
        message_id = message_response.json()["data"]["id"]

        # 删除消息
        response = await client.delete(
            f"/api/v1/messages/{message_id}"
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_stats(self, client, test_user_id):
        """测试获取统计信息"""
        # 创建几个对话
        for i in range(5):
            await client.post(
                "/api/v1/conversations",
                params={"user_id": test_user_id},
                json={"title": f"对话 {i+1}"}
            )

        # 获取统计
        response = await client.get(
            "/api/v1/conversations/stats",
            params={"user_id": test_user_id}
        )

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["total"] == 5
        assert "today" in data
        assert "this_week" in data
        assert "this_month" in data

    @pytest.mark.asyncio
    async def test_export_conversation_markdown(self, client, test_user_id):
        """测试导出对话为 Markdown"""
        # 创建对话并添加消息
        create_response = await client.post(
            "/api/v1/conversations",
            params={"user_id": test_user_id},
            json={"title": "测试对话"}
        )
        conversation_id = create_response.json()["data"]["id"]

        await client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            json={"role": "user", "content": "测试消息"}
        )

        # 导出
        response = await client.get(
            f"/api/v1/conversations/{conversation_id}/export",
            params={"format": "markdown"}
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/markdown; charset=utf-8"
        content = response.content.decode("utf-8")
        assert "测试对话" in content
        assert "测试消息" in content

    @pytest.mark.asyncio
    async def test_export_conversation_json(self, client, test_user_id):
        """测试导出对话为 JSON"""
        # 创建对话
        create_response = await client.post(
            "/api/v1/conversations",
            params={"user_id": test_user_id},
            json={"title": "测试对话"}
        )
        conversation_id = create_response.json()["data"]["id"]

        # 导出
        response = await client.get(
            f"/api/v1/conversations/{conversation_id}/export",
            params={"format": "json"}
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

    @pytest.mark.asyncio
    async def test_pagination(self, client, test_user_id):
        """测试分页功能"""
        # 创建 25 个对话
        for i in range(25):
            await client.post(
                "/api/v1/conversations",
                params={"user_id": test_user_id},
                json={"title": f"对话 {i+1}"}
            )

        # 第一页
        response1 = await client.get(
            "/api/v1/conversations",
            params={"user_id": test_user_id, "page": 1, "page_size": 10}
        )
        data1 = response1.json()["data"]
        assert len(data1["conversations"]) == 10

        # 第二页
        response2 = await client.get(
            "/api/v1/conversations",
            params={"user_id": test_user_id, "page": 2, "page_size": 10}
        )
        data2 = response2.json()["data"]
        assert len(data2["conversations"]) == 10

        # 验证不重复
        ids1 = {conv["id"] for conv in data1["conversations"]}
        ids2 = {conv["id"] for conv in data2["conversations"]}
        assert ids1.isdisjoint(ids2)

    @pytest.mark.asyncio
    async def test_concurrent_message_adding(self, client, test_user_id):
        """测试并发添加消息"""
        import asyncio

        # 创建对话
        create_response = await client.post(
            "/api/v1/conversations",
            params={"user_id": test_user_id},
            json={"title": "并发测试"}
        )
        conversation_id = create_response.json()["data"]["id"]

        # 并发添加消息
        tasks = [
            client.post(
                f"/api/v1/conversations/{conversation_id}/messages",
                json={"role": "user", "content": f"消息 {i+1}"}
            )
            for i in range(10)
        ]

        responses = await asyncio.gather(*tasks)

        # 验证所有请求成功
        assert all(r.status_code == 201 for r in responses)

        # 验证消息计数
        get_response = await client.get(
            f"/api/v1/conversations/{conversation_id}"
        )
        data = get_response.json()["data"]
        assert data["message_count"] == 10
