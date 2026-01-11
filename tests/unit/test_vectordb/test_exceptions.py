"""
Unit tests for Vector Database Exceptions
向量数据库异常类单元测试
"""

import pytest

from src.core.vectordb.exceptions import (
    VectorDBError,
    VectorDBConnectionError,
    VectorDBCollectionError,
    VectorDBQueryError,
    VectorDBInsertError,
    VectorDBNotFoundError
)


class TestVectorDBExceptions:
    """测试向量数据库异常类"""

    def test_base_exception(self):
        """测试基础异常"""
        with pytest.raises(VectorDBError, match="Base error"):
            raise VectorDBError("Base error")

    def test_connection_error(self):
        """测试连接异常"""
        with pytest.raises(VectorDBConnectionError, match="Connection failed"):
            raise VectorDBConnectionError("Connection failed")

        # 应该是 VectorDBError 的子类
        with pytest.raises(VectorDBError):
            raise VectorDBConnectionError("Connection failed")

    def test_collection_error(self):
        """测试 Collection 操作异常"""
        with pytest.raises(VectorDBCollectionError, match="Collection error"):
            raise VectorDBCollectionError("Collection error")

        with pytest.raises(VectorDBError):
            raise VectorDBCollectionError("Collection error")

    def test_query_error(self):
        """测试查询异常"""
        with pytest.raises(VectorDBQueryError, match="Query failed"):
            raise VectorDBQueryError("Query failed")

        with pytest.raises(VectorDBError):
            raise VectorDBQueryError("Query failed")

    def test_insert_error(self):
        """测试插入异常"""
        with pytest.raises(VectorDBInsertError, match="Insert failed"):
            raise VectorDBInsertError("Insert failed")

        with pytest.raises(VectorDBError):
            raise VectorDBInsertError("Insert failed")

    def test_not_found_error(self):
        """测试资源未找到异常"""
        with pytest.raises(VectorDBNotFoundError, match="Not found"):
            raise VectorDBNotFoundError("Not found")

        with pytest.raises(VectorDBError):
            raise VectorDBNotFoundError("Not found")

    def test_exception_inheritance(self):
        """测试异常继承关系"""
        # 所有异常都应该继承自 VectorDBError
        assert issubclass(VectorDBConnectionError, VectorDBError)
        assert issubclass(VectorDBCollectionError, VectorDBError)
        assert issubclass(VectorDBQueryError, VectorDBError)
        assert issubclass(VectorDBInsertError, VectorDBError)
        assert issubclass(VectorDBNotFoundError, VectorDBError)

        # 并且都应该继承自 Exception
        assert issubclass(VectorDBError, Exception)
