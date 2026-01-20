"""
文档服务单元测试
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import List

from src.api.services.document_service import DocumentService, get_document_service
from src.api.schemas.document import (
    DocumentUploadRequest, DocumentQueryRequest, DocumentUpdateRequest,
    DocumentMetadata, DocumentDetail, DocumentListResponse,
    DocumentUploadResponse, DocumentDeleteResponse, DocumentStatsResponse
)
from src.core.rag import TextChunker, ChunkingConfig, Chunk


class TestDocumentService:
    """文档服务测试类"""

    @pytest.fixture
    def mock_chunker(self):
        """Mock 文本分块器"""
        chunker = Mock(spec=TextChunker)
        chunker.chunk_text = Mock(return_value=[
            Chunk(
                chunk_id="test_doc_chunk_0",
                parent_id="test_doc",
                content="This is chunk 0 content",
                chunk_index=0,
                start_index=0,
                end_index=50,
                metadata={}
            ),
            Chunk(
                chunk_id="test_doc_chunk_1",
                parent_id="test_doc",
                content="This is chunk 1 content",
                chunk_index=1,
                start_index=40,
                end_index=90,
                metadata={}
            )
        ])
        return chunker

    @pytest.fixture
    def mock_vectordb(self):
        """Mock 向量数据库客户端"""
        vectordb = Mock()
        vectordb.collection_name = "test_collection"

        # Mock collection
        mock_collection = Mock()
        mock_collection.get = Mock(return_value={"ids": [], "metadatas": []})
        mock_collection.add = Mock()
        mock_collection.delete = Mock()

        vectordb.get_or_create_collection = Mock(return_value=mock_collection)
        return vectordb

    @pytest.fixture
    def mock_llm_manager(self):
        """Mock LLM 管理器"""
        manager = Mock()

        # Mock embedding model
        mock_embedding = AsyncMock()
        mock_embedding.model_name = "test-embedding-model"
        mock_embedding.embed_batch = AsyncMock(return_value=[
            [0.1] * 768,  # Mock embedding vector
            [0.2] * 768
        ])

        manager.create_embedding = Mock(return_value=mock_embedding)
        return manager

    @pytest.fixture
    def service(self, mock_chunker, mock_vectordb, mock_llm_manager):
        """创建文档服务实例"""
        with patch('src.api.services.document_service.get_llm_manager', return_value=mock_llm_manager):
            service = DocumentService(
                chunker=mock_chunker,
                vectordb_client=mock_vectordb
            )
            return service

    @pytest.mark.asyncio
    async def test_upload_document_success(self, service, mock_chunker, mock_vectordb):
        """测试成功上传文档"""
        request = DocumentUploadRequest(
            title="Test Document",
            content="This is a test document content for testing the upload functionality.",
            source_type="local",
            tags=["test", "upload"]
        )

        response = await service.upload_document(request)

        # 验证返回结果
        assert isinstance(response, DocumentUploadResponse)
        assert response.title == "Test Document"
        assert response.chunk_count == 2
        assert "test" in response.document_id or "local" in response.document_id
        assert "uploaded and indexed successfully" in response.message

        # 验证 chunker 被调用
        mock_chunker.chunk_text.assert_called_once()

        # 验证 vectordb 被调用
        collection = mock_vectordb.get_or_create_collection.return_value
        collection.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_document_with_source_id(self, service):
        """测试使用 source_id 上传文档"""
        request = DocumentUploadRequest(
            title="Jira Issue",
            content="Issue content",
            source_type="jira",
            source_id="PROJ-123",
            tags=["bug"]
        )

        response = await service.upload_document(request)

        assert response.document_id == "jira_PROJ-123"

    @pytest.mark.asyncio
    async def test_upload_document_empty_content(self, service):
        """测试上传空内容文档"""
        from pydantic import ValidationError

        # Pydantic 在创建 request 时就会抛出验证错误
        with pytest.raises(ValidationError):
            request = DocumentUploadRequest(
                title="Empty Doc",
                content="",
                source_type="local"
            )

    @pytest.mark.asyncio
    async def test_upload_document_duplicate(self, service, mock_vectordb):
        """测试上传重复文档（覆盖）"""
        # Mock existing document
        mock_collection = mock_vectordb.get_or_create_collection.return_value
        mock_collection.get.return_value = {
            "ids": ["local_test_chunk_0"],
            "metadatas": [{"document_id": "local_test", "title": "Old Title"}],
            "documents": ["Old content"]
        }

        request = DocumentUploadRequest(
            title="Test Doc",
            content="New content",
            source_type="local",
            source_id="test"
        )

        response = await service.upload_document(request)

        # 验证旧文档被删除
        mock_collection.delete.assert_called()
        # 验证新文档被添加
        mock_collection.add.assert_called()

    @pytest.mark.asyncio
    async def test_get_document_list_empty(self, service, mock_vectordb):
        """测试获取空文档列表"""
        mock_collection = mock_vectordb.get_or_create_collection.return_value
        mock_collection.get.return_value = {"metadatas": []}

        query = DocumentQueryRequest()
        response = await service.get_document_list(query)

        assert isinstance(response, DocumentListResponse)
        assert len(response.documents) == 0
        assert response.total == 0

    @pytest.mark.asyncio
    async def test_get_document_list_with_results(self, service, mock_vectordb):
        """测试获取文档列表"""
        # Mock data
        mock_collection = mock_vectordb.get_or_create_collection.return_value
        mock_collection.get.return_value = {
            "metadatas": [
                {
                    "document_id": "doc1",
                    "title": "Document 1",
                    "source_type": "local",
                    "content_preview": "Preview 1",
                    "indexed_at": datetime.now().isoformat(),
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "tags": "test,doc"
                },
                {
                    "document_id": "doc1",  # Same doc, different chunk
                    "title": "Document 1",
                    "source_type": "local",
                    "content_preview": "Preview 1",
                    "indexed_at": datetime.now().isoformat(),
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "tags": "test,doc"
                },
                {
                    "document_id": "doc2",
                    "title": "Document 2",
                    "source_type": "jira",
                    "content_preview": "Preview 2",
                    "indexed_at": datetime.now().isoformat(),
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "tags": "test"
                }
            ]
        }

        query = DocumentQueryRequest()
        response = await service.get_document_list(query)

        assert len(response.documents) == 2  # 2 unique documents
        assert response.total == 2

        # Find doc1 (which has 2 chunks)
        doc1 = next((d for d in response.documents if d.document_id == "doc1"), None)
        assert doc1 is not None
        assert doc1.chunk_count == 2  # doc1 has 2 chunks

    @pytest.mark.asyncio
    async def test_get_document_list_filter_by_source_type(self, service, mock_vectordb):
        """测试按来源类型筛选文档"""
        mock_collection = mock_vectordb.get_or_create_collection.return_value
        mock_collection.get.return_value = {
            "metadatas": [
                {
                    "document_id": "doc1",
                    "title": "Local Doc",
                    "source_type": "local",
                    "content_preview": "Preview",
                    "indexed_at": datetime.now().isoformat(),
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "tags": ""
                },
                {
                    "document_id": "doc2",
                    "title": "Jira Doc",
                    "source_type": "jira",
                    "content_preview": "Preview",
                    "indexed_at": datetime.now().isoformat(),
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "tags": ""
                }
            ]
        }

        query = DocumentQueryRequest(source_type="local")
        response = await service.get_document_list(query)

        assert len(response.documents) == 1
        assert response.documents[0].source_type == "local"

    @pytest.mark.asyncio
    async def test_get_document_list_filter_by_tags(self, service, mock_vectordb):
        """测试按标签筛选文档"""
        mock_collection = mock_vectordb.get_or_create_collection.return_value
        mock_collection.get.return_value = {
            "metadatas": [
                {
                    "document_id": "doc1",
                    "title": "Doc 1",
                    "source_type": "local",
                    "content_preview": "Preview",
                    "indexed_at": datetime.now().isoformat(),
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "tags": "python,backend"
                },
                {
                    "document_id": "doc2",
                    "title": "Doc 2",
                    "source_type": "local",
                    "content_preview": "Preview",
                    "indexed_at": datetime.now().isoformat(),
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "tags": "frontend,react"
                }
            ]
        }

        query = DocumentQueryRequest(tags=["python"])
        response = await service.get_document_list(query)

        assert len(response.documents) == 1
        assert "python" in response.documents[0].tags

    @pytest.mark.asyncio
    async def test_get_document_list_pagination(self, service, mock_vectordb):
        """测试分页功能"""
        # Mock 10 documents
        metadatas = []
        for i in range(10):
            metadatas.append({
                "document_id": f"doc{i}",
                "title": f"Document {i}",
                "source_type": "local",
                "content_preview": f"Preview {i}",
                "indexed_at": datetime.now().isoformat(),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "tags": ""
            })

        mock_collection = mock_vectordb.get_or_create_collection.return_value
        mock_collection.get.return_value = {"metadatas": metadatas}

        # Test first page
        query = DocumentQueryRequest(limit=5, offset=0)
        response = await service.get_document_list(query)
        assert len(response.documents) == 5
        assert response.total == 10

        # Test second page
        query = DocumentQueryRequest(limit=5, offset=5)
        response = await service.get_document_list(query)
        assert len(response.documents) == 5

    @pytest.mark.asyncio
    async def test_get_document_by_id_success(self, service, mock_vectordb):
        """测试成功获取文档详情"""
        mock_collection = mock_vectordb.get_or_create_collection.return_value
        mock_collection.get.return_value = {
            "ids": ["doc1_chunk_0", "doc1_chunk_1"],
            "metadatas": [
                {
                    "document_id": "doc1",
                    "title": "Test Doc",
                    "source_type": "local",
                    "indexed_at": datetime.now().isoformat(),
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "tags": "test,doc"
                },
                {
                    "document_id": "doc1",
                    "title": "Test Doc",
                    "source_type": "local",
                    "indexed_at": datetime.now().isoformat(),
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "tags": "test,doc"
                }
            ],
            "documents": ["Chunk 0 content", "Chunk 1 content"]
        }

        result = await service.get_document_by_id("doc1")

        assert isinstance(result, DocumentDetail)
        assert result.document_id == "doc1"
        assert result.title == "Test Doc"
        assert result.chunk_count == 2
        assert "Chunk 0 content\nChunk 1 content" == result.content
        assert result.tags == ["test", "doc"]

    @pytest.mark.asyncio
    async def test_get_document_by_id_not_found(self, service, mock_vectordb):
        """测试获取不存在的文档"""
        mock_collection = mock_vectordb.get_or_create_collection.return_value
        mock_collection.get.return_value = {"metadatas": []}

        result = await service.get_document_by_id("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_document_success(self, service, mock_vectordb):
        """测试成功删除文档"""
        mock_collection = mock_vectordb.get_or_create_collection.return_value
        mock_collection.get.return_value = {
            "ids": ["doc1_chunk_0", "doc1_chunk_1", "doc1_chunk_2"]
        }

        response = await service.delete_document("doc1")

        assert isinstance(response, DocumentDeleteResponse)
        assert response.document_id == "doc1"
        assert response.deleted_chunks == 3
        assert "deleted successfully" in response.message

        # 验证 delete 被调用
        mock_collection.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_document_not_found(self, service, mock_vectordb):
        """测试删除不存在的文档"""
        mock_collection = mock_vectordb.get_or_create_collection.return_value
        mock_collection.get.return_value = {"ids": []}

        with pytest.raises(ValueError, match="not found"):
            await service.delete_document("nonexistent")

    @pytest.mark.asyncio
    async def test_get_document_stats_empty(self, service, mock_vectordb):
        """测试获取空统计"""
        mock_collection = mock_vectordb.get_or_create_collection.return_value
        mock_collection.get.return_value = {"metadatas": []}

        response = await service.get_document_stats()

        assert isinstance(response, DocumentStatsResponse)
        assert response.total_documents == 0
        assert response.total_chunks == 0
        assert response.by_source_type == {}
        assert response.by_tags == {}

    @pytest.mark.asyncio
    async def test_get_document_stats_with_data(self, service, mock_vectordb):
        """测试获取统计信息"""
        now = datetime.now().isoformat()
        mock_collection = mock_vectordb.get_or_create_collection.return_value
        mock_collection.get.return_value = {
            "metadatas": [
                {
                    "document_id": "doc1",
                    "source_type": "local",
                    "tags": "python,test",
                    "indexed_at": now
                },
                {
                    "document_id": "doc1",
                    "source_type": "local",
                    "tags": "python,test",
                    "indexed_at": now
                },
                {
                    "document_id": "doc2",
                    "source_type": "jira",
                    "tags": "bug,test",
                    "indexed_at": now
                }
            ]
        }

        response = await service.get_document_stats()

        assert response.total_documents == 2  # doc1 and doc2
        assert response.total_chunks == 3
        assert response.by_source_type["local"] == 2
        assert response.by_source_type["jira"] == 1
        assert response.by_tags["python"] == 2
        assert response.by_tags["test"] == 3
        assert response.by_tags["bug"] == 1

    def test_generate_document_id_with_source_id(self, service):
        """测试生成带 source_id 的文档ID"""
        doc_id = service._generate_document_id(
            title="Test",
            source_type="jira",
            source_id="PROJ-123"
        )
        assert doc_id == "jira_PROJ-123"

    def test_generate_document_id_without_source_id(self, service):
        """测试生成不带 source_id 的文档ID"""
        doc_id = service._generate_document_id(
            title="Test Document",
            source_type="local",
            source_id=None
        )
        assert doc_id.startswith("local_")
        assert len(doc_id) > len("local_")


class TestGetDocumentService:
    """测试全局单例函数"""

    def test_get_document_service_singleton(self):
        """测试单例模式"""
        with patch('src.api.services.document_service.get_llm_manager'):
            service1 = get_document_service()
            service2 = get_document_service()

            assert service1 is service2

    def test_get_document_service_with_custom_dependencies(self):
        """测试使用自定义依赖"""
        mock_chunker = Mock(spec=TextChunker)
        mock_vectordb = Mock()

        with patch('src.api.services.document_service.get_llm_manager'):
            # Reset singleton
            import src.api.services.document_service
            src.api.services.document_service._document_service = None

            service = get_document_service(
                chunker=mock_chunker,
                vectordb_client=mock_vectordb
            )

            assert service.chunker is mock_chunker
            assert service.vectordb_client is mock_vectordb
