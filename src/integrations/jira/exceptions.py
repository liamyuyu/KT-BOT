"""
Jira Integration Exceptions
Jira 集成自定义异常类
"""


class JiraIntegrationError(Exception):
    """Jira 集成基础异常"""
    pass


class JiraAuthenticationError(JiraIntegrationError):
    """Jira 认证失败异常"""
    pass


class JiraConnectionError(JiraIntegrationError):
    """Jira 连接失败异常"""
    pass


class JiraAPIError(JiraIntegrationError):
    """Jira API 调用失败异常"""
    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.status_code = status_code


class JiraResourceNotFoundError(JiraIntegrationError):
    """Jira 资源未找到异常"""
    pass


class JiraRateLimitError(JiraIntegrationError):
    """Jira API 限流异常"""
    def __init__(self, message: str, retry_after: int = None):
        super().__init__(message)
        self.retry_after = retry_after
