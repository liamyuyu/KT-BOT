"""
Vector Database Exceptions
向量数据库自定义异常类
"""


class VectorDBError(Exception):
    """向量数据库基础异常"""
    pass


class VectorDBConnectionError(VectorDBError):
    """向量数据库连接失败异常"""
    pass


class VectorDBCollectionError(VectorDBError):
    """Collection 操作异常"""
    pass


class VectorDBQueryError(VectorDBError):
    """查询操作异常"""
    pass


class VectorDBInsertError(VectorDBError):
    """插入操作异常"""
    pass


class VectorDBNotFoundError(VectorDBError):
    """资源未找到异常"""
    pass
