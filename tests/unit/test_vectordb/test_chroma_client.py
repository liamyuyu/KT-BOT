"""
Unit tests for ChromaDB Client
ChromaDB 客户端单元测试
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from datetime import datetime

from src.core.vectordb.chroma_client import ChromaDBClient, get_chroma_client
from src.core.vectordb.models import (
    Document,
    SearchResult,
    SearchResults,
    CollectionInfo,
    HealthStatus,
    BatchInsertResult
)
from src.core.vectordb.exceptions import (
    VectorDBConnectionError,
    VectorDBCollectionError,
    VectorDBQueryError,
    VectorDBInsertError
)


class TestChromaDBClientInit:
    """测试 ChromaDBClient 初始化"""

    def test_init_with_parameters(self):
        """测试使用参数初始化"""
        client = ChromaDBClient(
            persist_directory="./test_chroma",
            collection_name="test_collection",
            use_persistent=True
        )
        assert client.persist_directory == "./test_chroma"
        assert client.collection_name == "test_collection"
        assert client.use_persistent is True

    @patch('src.core.vectordb.chroma_client.settings')
    def test_init_from_settings(self, mock_settings):
        """测试从配置文件读取初始化参数"""
        mock_settings.chroma_persist_directory = "./data/chroma"
        mock_settings.chroma_collection_name = "kt_bot_documents"

        client = ChromaDBClient()
        assert client.persist_directory == "./data/chroma"
        assert client.collection_name == "kt_bot_documents"


class TestChromaDBClientConnection:
    """测试 ChromaDB 连接"""

    @patch('src.core.vectordb.chroma_client.chromadb.PersistentClient')
    def test_connect_persistent_mode(self, mock_persistent_client):
        """测试持久化模式连接"""
        mock_client_instance = Mock()
        mock_client_instance.heartbeat.return_value = True
        mock_persistent_client.return_value = mock_client_instance

        client = ChromaDBClient(persist_directory="./test", use_persistent=True)
        # 触发连接
        _ = client.client

        assert client._is_connected is True
        mock_persistent_client.assert_called_once()

    @patch('src.core.vectordb.chroma_client.chromadb.EphemeralClient')
    def test_connect_ephemeral_mode(self, mock_ephemeral_client):
        """测试内存模式连接"""
        mock_client_instance = Mock()
        mock_client_instance.heartbeat.return_value = True
        mock_ephemeral_client.return_value = mock_client_instance

        client = ChromaDBClient(use_persistent=False)
        _ = client.client

        assert client._is_connected is True
        mock_ephemeral_client.assert_called_once()

    @patch('src.core.vectordb.chroma_client.chromadb.PersistentClient')
    def test_connect_failure(self, mock_persistent_client):
        """测试连接失败"""
        mock_persistent_client.side_effect = Exception("Connection failed")

        client = ChromaDBClient()

        with pytest.raises(VectorDBConnectionError, match="连接失败"):
            _ = client.client


class TestChromaDBClientCollection:
    """测试 Collection 管理"""

    @patch('src.core.vectordb.chroma_client.chromadb.PersistentClient')
    def test_get_or_create_collection(self, mock_persistent_client):
        """测试获取或创建 Collection"""
        mock_client_instance = Mock()
        mock_client_instance.heartbeat.return_value = True
        mock_collection = Mock()
        mock_collection.name = "test_collection"
        mock_client_instance.get_or_create_collection.return_value = mock_collection
        mock_persistent_client.return_value = mock_client_instance

        client = ChromaDBClient(collection_name="test_collection")
        collection = client.get_or_create_collection()

        assert collection.name == "test_collection"
        mock_client_instance.get_or_create_collection.assert_called_once()

    @patch('src.core.vectordb.chroma_client.chromadb.PersistentClient')
    def test_list_collections(self, mock_persistent_client):
        """测试列出所有 Collections"""
        mock_client_instance = Mock()
        mock_client_instance.heartbeat.return_value = True

        # Mock collections
        mock_col1 = Mock()
        mock_col1.name = "col1"
        mock_col1.count.return_value = 100
        mock_col1.metadata = {"desc": "Collection 1"}

        mock_col2 = Mock()
        mock_col2.name = "col2"
        mock_col2.count.return_value = 200
        mock_col2.metadata = {}

        mock_client_instance.list_collections.return_value = [mock_col1, mock_col2]
        mock_persistent_client.return_value = mock_client_instance

        client = ChromaDBClient()
        collections = client.list_collections()

        assert len(collections) == 2
        assert all(isinstance(c, CollectionInfo) for c in collections)
        assert collections[0].name == "col1"
        assert collections[0].count == 100


class TestChromaDBClientHealthCheck:
    """测试健康检查功能"""

    @pytest.mark.asyncio
    @patch('src.core.vectordb.chroma_client.chromadb.PersistentClient')
    @patch('src.core.vectordb.chroma_client.chromadb.__version__', "0.4.22")
    async def test_health_check_success(self, mock_persistent_client):
        """测试健康检查成功"""
        mock_client_instance = Mock()
        mock_client_instance.heartbeat.return_value = True

        # Mock collections
        mock_col = Mock()
        mock_col.name = "test_col"
        mock_col.count.return_value = 500

        mock_client_instance.list_collections.return_value = [mock_col]
        mock_persistent_client.return_value = mock_client_instance

        client = ChromaDBClient()
        health = client.health_check()

        assert isinstance(health, HealthStatus)
        assert health.is_connected is True
        assert health.version == "0.4.22"
        assert len(health.collections) == 1
        assert health.total_documents == 500
        assert health.error_message is None

    @pytest.mark.asyncio
    @patch('src.core.vectordb.chroma_client.chromadb.PersistentClient')
    async def test_health_check_failure(self, mock_persistent_client):
        """测试健康检查失败"""
        mock_client_instance = Mock()
        mock_client_instance.heartbeat.side_effect = Exception("Connection lost")
        mock_persistent_client.return_value = mock_client_instance

        client = ChromaDBClient()
        health = client.health_check()

        assert health.is_connected is False
        assert health.error_message is not None
        assert "健康检查失败" in health.error_message


class TestChromaDBClientAddDocument:
    """测试添加文档功能"""

    @patch('src.core.vectordb.chroma_client.chromadb.PersistentClient')
    def test_add_document(self, mock_persistent_client):
        """测试添加单个文档"""
        mock_client_instance = Mock()
        mock_client_instance.heartbeat.return_value = True

        mock_collection = Mock()
        mock_collection.add = Mock()
        mock_client_instance.get_or_create_collection.return_value = mock_collection
        mock_persistent_client.return_value = mock_client_instance

        client = ChromaDBClient()

        doc = Document(
            id="doc_1",
            content="测试文档",
            metadata={"source": "test"}
        )

        result = client.add_document(doc)

        assert result is True
        mock_collection.add.assert_called_once()
        # 验证调用参数
        call_args = mock_collection.add.call_args
        assert call_args[1]["ids"] == ["doc_1"]
        assert call_args[1]["documents"] == ["测试文档"]

    @patch('src.core.vectordb.chroma_client.chromadb.PersistentClient')
    def test_add_documents_batch(self, mock_persistent_client):
        """测试批量添加文档"""
        mock_client_instance = Mock()
        mock_client_instance.heartbeat.return_value = True

        mock_collection = Mock()
        mock_collection.add = Mock()
        mock_client_instance.get_or_create_collection.return_value = mock_collection
        mock_persistent_client.return_value = mock_client_instance

        client = ChromaDBClient()

        docs = [
            Document(id=f"doc_{i}", content=f"内容 {i}", metadata={})
            for i in range(5)
        ]

        result = client.add_documents(docs, batch_size=10)

        assert isinstance(result, BatchInsertResult)
        assert result.success is True
        assert result.inserted_count == 5
        assert result.failed_count == 0


class TestChromaDBClientSearch:
    """测试搜索功能"""

    @patch('src.core.vectordb.chroma_client.chromadb.PersistentClient')
    def test_search(self, mock_persistent_client):
        """测试向量搜索"""
        mock_client_instance = Mock()
        mock_client_instance.heartbeat.return_value = True

        mock_collection = Mock()
        # Mock 查询结果
        mock_collection.query.return_value = {
            "ids": [["doc_1", "doc_2"]],
            "documents": [["文档1内容", "文档2内容"]],
            "metadatas": [[{"source": "test"}, {"source": "test"}]],
            "distances": [[0.1, 0.2]]
        }

        mock_client_instance.get_or_create_collection.return_value = mock_collection
        mock_persistent_client.return_value = mock_client_instance

        client = ChromaDBClient()
        results = client.search("测试查询", n_results=5)

        assert isinstance(results, SearchResults)
        assert len(results.results) == 2
        assert results.results[0].id == "doc_1"
        assert results.results[0].distance == 0.1
        assert results.query == "测试查询"

    @patch('src.core.vectordb.chroma_client.chromadb.PersistentClient')
    def test_search_with_filter(self, mock_persistent_client):
        """测试带过滤条件的搜索"""
        mock_client_instance = Mock()
        mock_client_instance.heartbeat.return_value = True

        mock_collection = Mock()
        mock_collection.query.return_value = {
            "ids": [["doc_1"]],
            "documents": [["过滤后的文档"]],
            "metadatas": [[{"source": "confluence"}]],
            "distances": [[0.05]]
        }

        mock_client_instance.get_or_create_collection.return_value = mock_collection
        mock_persistent_client.return_value = mock_client_instance

        client = ChromaDBClient()
        results = client.search(
            "测试",
            n_results=10,
            where={"source": "confluence"}
        )

        assert len(results.results) == 1
        assert results.results[0].metadata["source"] == "confluence"
        # 验证 where 参数被传递
        mock_collection.query.assert_called_once()


class TestChromaDBClientGetDocument:
    """测试获取文档功能"""

    @patch('src.core.vectordb.chroma_client.chromadb.PersistentClient')
    def test_get_document(self, mock_persistent_client):
        """测试根据 ID 获取文档"""
        mock_client_instance = Mock()
        mock_client_instance.heartbeat.return_value = True

        mock_collection = Mock()
        mock_collection.get.return_value = {
            "ids": ["doc_1"],
            "documents": ["文档内容"],
            "metadatas": [{"source": "test"}],
            "embeddings": [[0.1, 0.2, 0.3]]
        }

        mock_client_instance.get_or_create_collection.return_value = mock_collection
        mock_persistent_client.return_value = mock_client_instance

        client = ChromaDBClient()
        doc = client.get_document("doc_1")

        assert isinstance(doc, Document)
        assert doc.id == "doc_1"
        assert doc.content == "文档内容"
        assert doc.metadata["source"] == "test"

    @patch('src.core.vectordb.chroma_client.chromadb.PersistentClient')
    def test_get_document_not_found(self, mock_persistent_client):
        """测试获取不存在的文档"""
        mock_client_instance = Mock()
        mock_client_instance.heartbeat.return_value = True

        mock_collection = Mock()
        mock_collection.get.return_value = {"ids": []}

        mock_client_instance.get_or_create_collection.return_value = mock_collection
        mock_persistent_client.return_value = mock_client_instance

        client = ChromaDBClient()
        doc = client.get_document("not_exist")

        assert doc is None


class TestChromaDBClientDelete:
    """测试删除文档功能"""

    @patch('src.core.vectordb.chroma_client.chromadb.PersistentClient')
    def test_delete_document(self, mock_persistent_client):
        """测试删除单个文档"""
        mock_client_instance = Mock()
        mock_client_instance.heartbeat.return_value = True

        mock_collection = Mock()
        mock_collection.delete = Mock()

        mock_client_instance.get_or_create_collection.return_value = mock_collection
        mock_persistent_client.return_value = mock_client_instance

        client = ChromaDBClient()
        result = client.delete_document("doc_1")

        assert result is True
        mock_collection.delete.assert_called_once_with(ids=["doc_1"])

    @patch('src.core.vectordb.chroma_client.chromadb.PersistentClient')
    def test_delete_documents_batch(self, mock_persistent_client):
        """测试批量删除文档"""
        mock_client_instance = Mock()
        mock_client_instance.heartbeat.return_value = True

        mock_collection = Mock()
        mock_collection.get.return_value = {"ids": ["doc_1", "doc_2", "doc_3"]}
        mock_collection.delete = Mock()

        mock_client_instance.get_or_create_collection.return_value = mock_collection
        mock_persistent_client.return_value = mock_client_instance

        client = ChromaDBClient()
        count = client.delete_documents(where={"source": "test"})

        assert count == 3
        mock_collection.delete.assert_called_once()


class TestChromaDBClientContextManager:
    """测试上下文管理器"""

    @patch('src.core.vectordb.chroma_client.chromadb.PersistentClient')
    def test_context_manager(self, mock_persistent_client):
        """测试上下文管理器正常工作"""
        mock_client_instance = Mock()
        mock_client_instance.heartbeat.return_value = True
        mock_persistent_client.return_value = mock_client_instance

        with ChromaDBClient(persist_directory="./test") as client:
            assert client is not None
            # 触发懒加载
            _ = client.client
            assert client._client is not None

        # 退出后客户端应该被关闭
        assert client._client is None
        assert client._is_connected is False


class TestGetChromaClient:
    """测试全局单例函数"""

    def test_get_chroma_client_singleton(self):
        """测试单例模式"""
        # 重置全局单例
        import src.core.vectordb.chroma_client as client_module
        client_module._global_chroma_client = None

        client1 = get_chroma_client()
        client2 = get_chroma_client()

        assert client1 is client2
