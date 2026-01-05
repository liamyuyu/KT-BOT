"""
Jira Integration Module
Jira 集成模块 - 提供 Jira API 连接和数据访问

主要功能:
- Jira API 连接和认证
- Issue 查询和解析
- 健康检查
- 自动重试和错误处理

Usage:
    from src.integrations.jira import get_jira_client, JiraClient

    # 使用全局单例
    client = get_jira_client()
    health = await client.health_check()

    # 查询 Issues
    page = client.fetch_issues(project_key="PROJ", max_results=50)
    for issue in page.issues:
        print(f"{issue.key}: {issue.summary}")
"""

from src.integrations.jira.client import JiraClient, get_jira_client
from src.integrations.jira.models import (
    JiraIssue,
    JiraIssuePage,
    JiraUser,
    JiraProject,
    JiraComment,
    JiraAttachment,
    JiraHealthStatus
)
from src.integrations.jira.exceptions import (
    JiraIntegrationError,
    JiraAuthenticationError,
    JiraConnectionError,
    JiraAPIError,
    JiraResourceNotFoundError,
    JiraRateLimitError
)

__all__ = [
    # Client
    "JiraClient",
    "get_jira_client",

    # Models
    "JiraIssue",
    "JiraIssuePage",
    "JiraUser",
    "JiraProject",
    "JiraComment",
    "JiraAttachment",
    "JiraHealthStatus",

    # Exceptions
    "JiraIntegrationError",
    "JiraAuthenticationError",
    "JiraConnectionError",
    "JiraAPIError",
    "JiraResourceNotFoundError",
    "JiraRateLimitError",
]
