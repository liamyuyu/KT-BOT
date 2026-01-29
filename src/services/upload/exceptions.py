"""
Upload Service Exceptions
上传服务异常定义
"""


class UploadException(Exception):
    """上传基础异常"""
    def __init__(self, message: str, task_id: str = None):
        self.message = message
        self.task_id = task_id
        super().__init__(self.message)


class ValidationError(UploadException):
    """验证错误"""
    pass


class ParsingError(UploadException):
    """解析错误"""
    pass


class IndexingError(UploadException):
    """索引错误"""
    pass


class TaskNotFoundException(UploadException):
    """任务未找到异常"""
    pass


class TaskCancelledException(UploadException):
    """任务已取消异常"""
    pass
