"""
Confluence Integration Exceptions
Confluence 集成自定义异常类
"""


class ConfluenceIntegrationError(Exception):
    """Confluence 集成基础异常"""
    pass


class ConfluenceAuthenticationError(ConfluenceIntegrationError):
    """Confluence 认证失败异常"""
    pass


class ConfluenceConnectionError(ConfluenceIntegrationError):
    """Confluence 连接失败异常"""
    pass


class ConfluenceAPIError(ConfluenceIntegrationError):
    """Confluence API 调用失败异常"""
    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.status_code = status_code


class ConfluenceResourceNotFoundError(ConfluenceIntegrationError):
    """Confluence 资源未找到异常"""
    pass


class ConfluenceRateLimitError(ConfluenceIntegrationError):
    """Confluence API 限流异常"""
    def __init__(self, message: str, retry_after: int = None):
        super().__init__(message)
        self.retry_after = retry_after
