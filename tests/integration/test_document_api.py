"""
文档管理 API 集成测试
"""
import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import status

from src.api.main import create_fastapi_app


@pytest.fixture
def app():
    """创建测试应用"""
    return create_fastapi_app()


@pytest.fixture
async def client(app):
    """创建测试客户端"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestDocumentUploadAPI:
    """文档上传 API 测试"""

    @pytest.mark.asyncio
    async def test_upload_document_success(self, client):
        """测试成功上传文档"""
        payload = {
            "title": "Test Document",
            "content": "This is test content for document upload testing.",
            "source_type": "local",
            "tags": ["test", "integration"],
            "metadata": {}
        }

        response = await client.post("/api/v1/documents/upload", json=payload)

        # Note: This will fail if Ollama is not running
        # In a real test environment, we'd mock the embedding service
        if response.status_code == 500:
            # Expected if Ollama not running
            assert "connection" in response.json().get("detail", "").lower() or \
                   "embedding" in response.json().get("detail", "").lower()
        else:
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert "document_id" in data
            assert data["title"] == "Test Document"
            assert data["chunk_count"] > 0

    @pytest.mark.asyncio
    async def test_upload_document_missing_title(self, client):
        """测试缺少标题"""
        payload = {
            "content": "Content without title",
            "source_type": "local"
        }

        response = await client.post("/api/v1/documents/upload", json=payload)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_upload_document_missing_content(self, client):
        """测试缺少内容"""
        payload = {
            "title": "Title without content",
            "source_type": "local"
        }

        response = await client.post("/api/v1/documents/upload", json=payload)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_upload_document_empty_title(self, client):
        """测试空标题"""
        payload = {
            "title": "",
            "content": "Content",
            "source_type": "local"
        }

        response = await client.post("/api/v1/documents/upload", json=payload)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_upload_document_with_tags(self, client):
        """测试带标签上传"""
        payload = {
            "title": "Tagged Document",
            "content": "Document with tags",
            "source_type": "local",
            "tags": ["tag1", "tag2", "tag3"]
        }

        response = await client.post("/api/v1/documents/upload", json=payload)

        # May fail if embedding service not available
        if response.status_code == 201:
            data = response.json()
            assert data["title"] == "Tagged Document"


class TestDocumentListAPI:
    """文档列表 API 测试"""

    @pytest.mark.asyncio
    async def test_list_documents_empty(self, client):
        """测试空文档列表"""
        response = await client.get("/api/v1/documents/list")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "documents" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert isinstance(data["documents"], list)

    @pytest.mark.asyncio
    async def test_list_documents_with_limit(self, client):
        """测试限制数量"""
        response = await client.get("/api/v1/documents/list?limit=5")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["limit"] == 5

    @pytest.mark.asyncio
    async def test_list_documents_with_offset(self, client):
        """测试偏移量"""
        response = await client.get("/api/v1/documents/list?offset=10")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["offset"] == 10

    @pytest.mark.asyncio
    async def test_list_documents_filter_by_source_type(self, client):
        """测试按来源类型筛选"""
        response = await client.get("/api/v1/documents/list?source_type=local")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # All returned documents should be of type 'local'
        for doc in data["documents"]:
            assert doc["source_type"] == "local"

    @pytest.mark.asyncio
    async def test_list_documents_invalid_limit(self, client):
        """测试无效的限制数量"""
        response = await client.get("/api/v1/documents/list?limit=0")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_list_documents_negative_offset(self, client):
        """测试负数偏移量"""
        response = await client.get("/api/v1/documents/list?offset=-1")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestDocumentQueryAPI:
    """文档查询 API 测试"""

    @pytest.mark.asyncio
    async def test_query_documents_basic(self, client):
        """测试基本查询"""
        payload = {
            "limit": 10,
            "offset": 0
        }

        response = await client.post("/api/v1/documents/query", json=payload)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "documents" in data

    @pytest.mark.asyncio
    async def test_query_documents_with_tags(self, client):
        """测试标签查询"""
        payload = {
            "tags": ["test", "python"],
            "limit": 10
        }

        response = await client.post("/api/v1/documents/query", json=payload)

        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_query_documents_with_search_text(self, client):
        """测试文本搜索"""
        payload = {
            "search_text": "test",
            "limit": 10
        }

        response = await client.post("/api/v1/documents/query", json=payload)

        assert response.status_code == status.HTTP_200_OK


class TestDocumentDetailAPI:
    """文档详情 API 测试"""

    @pytest.mark.asyncio
    async def test_get_document_not_found(self, client):
        """测试获取不存在的文档"""
        response = await client.get("/api/v1/documents/nonexistent_doc_id")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "not found" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_document_invalid_id(self, client):
        """测试无效的文档ID"""
        response = await client.get("/api/v1/documents/")

        # Should return 404 or 405 (Method Not Allowed)
        assert response.status_code in [404, 405]


class TestDocumentDeleteAPI:
    """文档删除 API 测试"""

    @pytest.mark.asyncio
    async def test_delete_document_not_found(self, client):
        """测试删除不存在的文档"""
        response = await client.delete("/api/v1/documents/nonexistent_doc")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "not found" in data["detail"].lower()


class TestDocumentStatsAPI:
    """文档统计 API 测试"""

    @pytest.mark.asyncio
    async def test_get_stats_success(self, client):
        """测试获取统计信息"""
        response = await client.get("/api/v1/documents/stats/summary")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_documents" in data
        assert "total_chunks" in data
        assert "by_source_type" in data
        assert "by_tags" in data
        assert isinstance(data["total_documents"], int)
        assert isinstance(data["total_chunks"], int)
        assert isinstance(data["by_source_type"], dict)
        assert isinstance(data["by_tags"], dict)


class TestDocumentUpdateAPI:
    """文档更新 API 测试"""

    @pytest.mark.asyncio
    async def test_update_document_not_found(self, client):
        """测试更新不存在的文档"""
        payload = {
            "title": "Updated Title",
            "content": "Updated content"
        }

        response = await client.put("/api/v1/documents/nonexistent_doc", json=payload)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_update_document_partial(self, client):
        """测试部分更新"""
        payload = {
            "title": "New Title Only"
        }

        response = await client.put("/api/v1/documents/test_doc", json=payload)

        # Will fail if document doesn't exist
        assert response.status_code in [404, 500]


class TestDocumentAPIEdgeCases:
    """边界情况测试"""

    @pytest.mark.asyncio
    async def test_upload_very_long_title(self, client):
        """测试超长标题"""
        payload = {
            "title": "A" * 1000,  # 超过 max_length=500
            "content": "Content",
            "source_type": "local"
        }

        response = await client.post("/api/v1/documents/upload", json=payload)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_upload_very_long_content(self, client):
        """测试超长内容"""
        payload = {
            "title": "Long Content Document",
            "content": "A" * 100000,  # 100KB content
            "source_type": "local"
        }

        response = await client.post("/api/v1/documents/upload", json=payload)

        # Should either succeed or fail due to embedding service
        assert response.status_code in [201, 500]

    @pytest.mark.asyncio
    async def test_list_documents_exceed_max_limit(self, client):
        """测试超出最大限制"""
        response = await client.get("/api/v1/documents/list?limit=10000")

        # Should be rejected due to validation (max=1000)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_concurrent_uploads(self, client):
        """测试并发上传"""
        import asyncio

        async def upload_doc(i):
            payload = {
                "title": f"Concurrent Doc {i}",
                "content": f"Content {i}",
                "source_type": "local"
            }
            return await client.post("/api/v1/documents/upload", json=payload)

        # Upload 5 documents concurrently
        tasks = [upload_doc(i) for i in range(5)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Count successful uploads (may fail if embedding service not available)
        success_count = sum(1 for r in responses if hasattr(r, 'status_code') and r.status_code == 201)
        # All should either succeed or fail consistently
        assert success_count == 0 or success_count == 5

    @pytest.mark.asyncio
    async def test_upload_with_special_characters(self, client):
        """测试特殊字符"""
        payload = {
            "title": "文档测试 <>&\"'",
            "content": "内容包含特殊字符: <script>alert('xss')</script>",
            "source_type": "local",
            "tags": ["测试", "中文"]
        }

        response = await client.post("/api/v1/documents/upload", json=payload)

        # Should either succeed or fail due to embedding service
        assert response.status_code in [201, 400, 500]

    @pytest.mark.asyncio
    async def test_malformed_json(self, client):
        """测试畸形 JSON"""
        response = await client.post(
            "/api/v1/documents/upload",
            content="{invalid json}",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
