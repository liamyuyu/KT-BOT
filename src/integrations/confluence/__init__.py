"""
Confluence Integration Module
Confluence 集成模块 - 提供 Confluence API 连接和数据访问

主要功能:
- Confluence API 连接和认证
- 页面查询和解析
- 空间管理
- CQL 查询支持
- HTML 内容解析
- 健康检查
- 自动重试和错误处理

Usage:
    from src.integrations.confluence import get_confluence_client, ConfluenceClient

    # 使用全局单例
    client = get_confluence_client()
    health = await client.health_check()

    # 查询页面
    page = client.fetch_pages(space_key="SPACE", limit=50)
    for p in page.pages:
        print(f"{p.title}: {p.url}")

    # 查询单个页面
    page = client.fetch_page_by_id("123456")
    print(page.plain_text)
"""

from src.integrations.confluence.client import ConfluenceClient, get_confluence_client
from src.integrations.confluence.models import (
    ConfluencePage,
    ConfluencePagePage,
    ConfluenceUser,
    ConfluenceSpace,
    ConfluenceLabel,
    ConfluenceAttachment,
    ConfluenceVersion,
    ConfluenceHealthStatus
)
from src.integrations.confluence.exceptions import (
    ConfluenceIntegrationError,
    ConfluenceAuthenticationError,
    ConfluenceConnectionError,
    ConfluenceAPIError,
    ConfluenceResourceNotFoundError,
    ConfluenceRateLimitError
)

__all__ = [
    # Client
    "ConfluenceClient",
    "get_confluence_client",

    # Models
    "ConfluencePage",
    "ConfluencePagePage",
    "ConfluenceUser",
    "ConfluenceSpace",
    "ConfluenceLabel",
    "ConfluenceAttachment",
    "ConfluenceVersion",
    "ConfluenceHealthStatus",

    # Exceptions
    "ConfluenceIntegrationError",
    "ConfluenceAuthenticationError",
    "ConfluenceConnectionError",
    "ConfluenceAPIError",
    "ConfluenceResourceNotFoundError",
    "ConfluenceRateLimitError",
]
