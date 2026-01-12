"""
RAG Exceptions
RAG（检索增强生成）自定义异常类
"""


class RAGError(Exception):
    """RAG 模块基础异常"""
    pass


class ChunkingError(RAGError):
    """文档分块异常"""
    pass


class IndexingError(RAGError):
    """文档索引异常"""
    def __init__(self, message: str, failed_count: int = 0, document_id: str = None):
        super().__init__(message)
        self.failed_count = failed_count
        self.document_id = document_id


class RetrievalError(RAGError):
    """文档检索异常"""
    pass


class DocumentProcessingError(RAGError):
    """文档处理异常"""
    def __init__(self, message: str, document_id: str = None):
        super().__init__(message)
        self.document_id = document_id


class EmbeddingError(RAGError):
    """Embedding 生成异常"""
    def __init__(self, message: str, text_length: int = None):
        super().__init__(message)
        self.text_length = text_length


class InvalidConfigError(RAGError):
    """无效配置异常"""
    pass
