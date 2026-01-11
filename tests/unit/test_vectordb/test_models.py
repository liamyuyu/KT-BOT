"""
Unit tests for Vector Database Models
向量数据库数据模型单元测试
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from src.core.vectordb.models import (
    Document,
    SearchResult,
    SearchResults,
    CollectionInfo,
    HealthStatus,
    BatchInsertResult
)


class TestDocument:
    """测试 Document 模型"""

    def test_create_document(self):
        """测试创建文档"""
        doc = Document(
            id="doc_1",
            content="这是一个测试文档",
            metadata={"source": "test", "title": "测试"}
        )
        assert doc.id == "doc_1"
        assert doc.content == "这是一个测试文档"
        assert doc.metadata["source"] == "test"
        assert doc.embedding is None

    def test_create_document_with_embedding(self):
        """测试创建带向量的文档"""
        embedding = [0.1, 0.2, 0.3, 0.4]
        doc = Document(
            id="doc_1",
            content="测试",
            embedding=embedding,
            metadata={}
        )
        assert doc.embedding == embedding

    def test_document_missing_required_fields(self):
        """测试缺少必需字段"""
        with pytest.raises(ValidationError):
            Document(id="doc_1")  # 缺少 content

        with pytest.raises(ValidationError):
            Document(content="test")  # 缺少 id


class TestSearchResult:
    """测试 SearchResult 模型"""

    def test_create_search_result(self):
        """测试创建搜索结果"""
        result = SearchResult(
            id="doc_1",
            content="相关文档",
            metadata={"source": "test"},
            distance=0.15,
            score=0.85
        )
        assert result.id == "doc_1"
        assert result.content == "相关文档"
        assert result.distance == 0.15
        assert result.score == 0.85

    def test_search_result_without_score(self):
        """测试创建不带分数的搜索结果"""
        result = SearchResult(
            id="doc_1",
            content="test",
            distance=0.1
        )
        assert result.score is None


class TestSearchResults:
    """测试 SearchResults 模型"""

    def test_create_search_results(self):
        """测试创建搜索结果列表"""
        results = SearchResults(
            results=[],
            total=0,
            query="测试查询",
            limit=10
        )
        assert results.total == 0
        assert results.query == "测试查询"
        assert results.limit == 10
        assert len(results.results) == 0

    def test_search_results_with_items(self):
        """测试带结果的搜索结果列表"""
        search_results = [
            SearchResult(id=f"doc_{i}", content=f"文档 {i}", distance=0.1 * i)
            for i in range(5)
        ]

        results = SearchResults(
            results=search_results,
            total=5,
            query="test",
            limit=10
        )
        assert len(results.results) == 5
        assert results.total == 5


class TestCollectionInfo:
    """测试 CollectionInfo 模型"""

    def test_create_collection_info(self):
        """测试创建 Collection 信息"""
        info = CollectionInfo(
            name="test_collection",
            count=100,
            metadata={"description": "测试集合"}
        )
        assert info.name == "test_collection"
        assert info.count == 100
        assert info.metadata["description"] == "测试集合"

    def test_collection_info_minimal(self):
        """测试最小 Collection 信息"""
        info = CollectionInfo(name="test")
        assert info.name == "test"
        assert info.count == 0
        assert info.metadata == {}


class TestHealthStatus:
    """测试 HealthStatus 模型"""

    def test_health_status_connected(self):
        """测试连接成功的健康状态"""
        status = HealthStatus(
            is_connected=True,
            version="0.4.22",
            collections=["col1", "col2"],
            total_documents=1000
        )
        assert status.is_connected is True
        assert status.version == "0.4.22"
        assert len(status.collections) == 2
        assert status.total_documents == 1000
        assert status.error_message is None

    def test_health_status_failed(self):
        """测试连接失败的健康状态"""
        status = HealthStatus(
            is_connected=False,
            error_message="Connection timeout"
        )
        assert status.is_connected is False
        assert status.error_message == "Connection timeout"
        assert len(status.collections) == 0


class TestBatchInsertResult:
    """测试 BatchInsertResult 模型"""

    def test_batch_insert_success(self):
        """测试批量插入成功"""
        result = BatchInsertResult(
            success=True,
            inserted_count=100,
            failed_count=0
        )
        assert result.success is True
        assert result.inserted_count == 100
        assert result.failed_count == 0
        assert len(result.failed_ids) == 0

    def test_batch_insert_partial_failure(self):
        """测试批量插入部分失败"""
        result = BatchInsertResult(
            success=False,
            inserted_count=80,
            failed_count=20,
            failed_ids=["doc_1", "doc_2"],
            error_message="部分文档插入失败"
        )
        assert result.success is False
        assert result.inserted_count == 80
        assert result.failed_count == 20
        assert len(result.failed_ids) == 2
        assert result.error_message == "部分文档插入失败"
