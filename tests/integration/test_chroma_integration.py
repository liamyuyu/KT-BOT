"""
ChromaDB Integration Tests
ChromaDB 集成测试（使用实际的 ChromaDB 客户端）

运行方式:
    pytest tests/integration/test_chroma_integration.py -v
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from src.core.vectordb import (
    ChromaDBClient,
    Document,
    SearchResults,
    HealthStatus,
    CollectionInfo
)


@pytest.fixture(scope="function")
def temp_chroma_dir():
    """创建临时 ChromaDB 目录"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # 测试后清理
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="function")
def chroma_client(temp_chroma_dir):
    """创建测试用 ChromaDB 客户端"""
    client = ChromaDBClient(
        persist_directory=temp_chroma_dir,
        collection_name="test_collection",
        use_persistent=True
    )
    yield client
    client.close()


class TestChromaDBIntegration:
    """ChromaDB 集成测试套件"""

    def test_health_check(self, chroma_client):
        """测试健康检查"""
        health = chroma_client.health_check()

        assert isinstance(health, HealthStatus)
        assert health.is_connected is True
        assert health.version is not None
        print(f"\n✓ 健康检查成功")
        print(f"  版本: {health.version}")
        print(f"  Collections 数量: {len(health.collections)}")

    def test_add_and_get_document(self, chroma_client):
        """测试添加和获取文档"""
        # 添加文档
        doc = Document(
            id="doc_1",
            content="这是一个测试文档，用于验证 ChromaDB 功能。",
            metadata={
                "source": "test",
                "title": "测试文档",
                "category": "integration_test"
            }
        )

        result = chroma_client.add_document(doc)
        assert result is True
        print(f"\n✓ 文档添加成功: {doc.id}")

        # 获取文档
        retrieved_doc = chroma_client.get_document("doc_1")
        assert retrieved_doc is not None
        assert retrieved_doc.id == "doc_1"
        assert retrieved_doc.content == doc.content
        assert retrieved_doc.metadata["source"] == "test"
        print(f"✓ 文档获取成功: {retrieved_doc.id}")

    def test_batch_add_documents(self, chroma_client):
        """测试批量添加文档"""
        docs = [
            Document(
                id=f"doc_{i}",
                content=f"文档 {i} 的内容，包含一些测试文本。",
                metadata={"index": i, "source": "batch_test"}
            )
            for i in range(10)
        ]

        result = chroma_client.add_documents(docs, batch_size=5)
        assert result.success is True
        assert result.inserted_count == 10
        assert result.failed_count == 0
        print(f"\n✓ 批量添加成功: {result.inserted_count} 个文档")

    def test_search_documents(self, chroma_client):
        """测试向量搜索"""
        # 先添加一些文档
        docs = [
            Document(
                id="doc_tech_1",
                content="Python 是一种高级编程语言，广泛用于数据科学和机器学习。",
                metadata={"category": "tech", "topic": "python"}
            ),
            Document(
                id="doc_tech_2",
                content="机器学习是人工智能的一个分支，使用算法来学习数据模式。",
                metadata={"category": "tech", "topic": "ml"}
            ),
            Document(
                id="doc_food_1",
                content="火锅是中国的传统美食，深受人们喜爱。",
                metadata={"category": "food", "topic": "chinese"}
            )
        ]

        chroma_client.add_documents(docs)

        # 搜索相关文档
        results = chroma_client.search("Python编程和机器学习", n_results=2)

        assert isinstance(results, SearchResults)
        assert len(results.results) > 0
        print(f"\n✓ 搜索成功，找到 {len(results.results)} 个结果")

        for i, result in enumerate(results.results, 1):
            print(f"  {i}. {result.id}: 分数={result.score:.3f}, 距离={result.distance:.3f}")
            print(f"     内容预览: {result.content[:50]}...")

    def test_search_with_filter(self, chroma_client):
        """测试带过滤条件的搜索"""
        # 添加测试文档
        docs = [
            Document(id="conf_1", content="Confluence 是协作文档平台", metadata={"source": "confluence"}),
            Document(id="jira_1", content="Jira 是项目管理工具", metadata={"source": "jira"}),
            Document(id="conf_2", content="Confluence 支持团队协作", metadata={"source": "confluence"}),
        ]
        chroma_client.add_documents(docs)

        # 只搜索 Confluence 来源的文档
        results = chroma_client.search(
            "协作平台",
            n_results=5,
            where={"source": "confluence"}
        )

        print(f"\n✓ 过滤搜索成功，找到 {len(results.results)} 个 Confluence 文档")
        assert all(r.metadata["source"] == "confluence" for r in results.results)

    def test_delete_document(self, chroma_client):
        """测试删除文档"""
        # 添加文档
        doc = Document(
            id="doc_to_delete",
            content="这个文档将被删除",
            metadata={"temp": True}
        )
        chroma_client.add_document(doc)

        # 确认存在
        assert chroma_client.get_document("doc_to_delete") is not None

        # 删除文档
        result = chroma_client.delete_document("doc_to_delete")
        assert result is True
        print(f"\n✓ 文档删除成功")

        # 确认已删除
        assert chroma_client.get_document("doc_to_delete") is None

    def test_delete_documents_by_filter(self, chroma_client):
        """测试按条件批量删除"""
        # 添加测试文档
        docs = [
            Document(id=f"temp_{i}", content=f"临时文档 {i}", metadata={"temp": True})
            for i in range(5)
        ]
        chroma_client.add_documents(docs)

        # 批量删除
        count = chroma_client.delete_documents(where={"temp": True})
        assert count == 5
        print(f"\n✓ 批量删除成功: {count} 个文档")

    def test_collection_info(self, chroma_client):
        """测试获取 Collection 信息"""
        # 添加一些文档
        docs = [
            Document(id=f"info_{i}", content=f"内容 {i}", metadata={})
            for i in range(3)
        ]
        chroma_client.add_documents(docs)

        # 获取信息
        info = chroma_client.get_collection_info()

        assert isinstance(info, CollectionInfo)
        assert info.name == "test_collection"
        assert info.count >= 3
        print(f"\n✓ Collection 信息:")
        print(f"  名称: {info.name}")
        print(f"  文档数: {info.count}")

    def test_list_collections(self, chroma_client):
        """测试列出所有 Collections"""
        # 创建额外的 Collection
        chroma_client.get_or_create_collection("another_collection")

        # 列出所有 Collections
        collections = chroma_client.list_collections()

        assert len(collections) >= 1
        assert any(c.name == "test_collection" for c in collections)
        print(f"\n✓ 找到 {len(collections)} 个 Collections:")
        for col in collections:
            print(f"  - {col.name} ({col.count} 个文档)")

    def test_context_manager(self, temp_chroma_dir):
        """测试上下文管理器"""
        print("\n✓ 测试上下文管理器")

        with ChromaDBClient(persist_directory=temp_chroma_dir) as client:
            # 在上下文中使用
            doc = Document(id="context_doc", content="上下文测试", metadata={})
            client.add_document(doc)

            # 验证添加成功
            retrieved = client.get_document("context_doc")
            assert retrieved is not None
            print(f"  上下文内操作成功")

        # 退出后客户端应该被关闭
        assert client._client is None
        print(f"  上下文退出后客户端已关闭")


class TestChromaDBPersistence:
    """测试持久化功能"""

    def test_persistence(self, temp_chroma_dir):
        """测试数据持久化"""
        # 第一个客户端：添加数据
        with ChromaDBClient(persist_directory=temp_chroma_dir, collection_name="persist_test") as client1:
            doc = Document(id="persist_1", content="持久化测试文档", metadata={"test": "persistence"})
            client1.add_document(doc)
            print("\n✓ 第一个客户端添加数据")

        # 第二个客户端：读取数据
        with ChromaDBClient(persist_directory=temp_chroma_dir, collection_name="persist_test") as client2:
            doc = client2.get_document("persist_1")
            assert doc is not None
            assert doc.content == "持久化测试文档"
            print("✓ 第二个客户端成功读取持久化数据")


if __name__ == "__main__":
    """
    直接运行此文件进行测试

    使用方式:
        python tests/integration/test_chroma_integration.py
    """
    print("🚀 开始运行 ChromaDB 集成测试...\n")
    pytest.main([__file__, "-v", "-s"])
