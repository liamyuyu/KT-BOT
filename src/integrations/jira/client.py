"""
Jira API Client
Jira API 客户端实现，支持 Issue 查询、健康检查等功能
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from jira import JIRA, JIRAError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from src.config import settings
from src.integrations.jira.models import (
    JiraIssue,
    JiraIssuePage,
    JiraUser,
    JiraIssueType,
    JiraStatus,
    JiraPriority,
    JiraProject,
    JiraComment,
    JiraAttachment,
    JiraHealthStatus
)
from src.integrations.jira.exceptions import (
    JiraAuthenticationError,
    JiraConnectionError,
    JiraAPIError,
    JiraResourceNotFoundError,
    JiraRateLimitError
)

logger = logging.getLogger(__name__)


class JiraClient:
    """
    Jira API 客户端
    提供 Jira 数据访问的统一接口

    Features:
    - Issue 查询和分页
    - 健康检查
    - 自动重试和错误处理
    - 数据解析和转换
    """

    def __init__(
        self,
        url: Optional[str] = None,
        email: Optional[str] = None,
        api_token: Optional[str] = None,
        timeout: int = 30
    ):
        """
        初始化 Jira 客户端

        Args:
            url: Jira 实例 URL（默认从配置读取）
            email: 账号邮箱（默认从配置读取）
            api_token: API Token（默认从配置读取）
            timeout: 请求超时时间（秒）
        """
        self.url = url or settings.jira_url
        self.email = email or settings.jira_email
        self.api_token = api_token or settings.jira_api_token
        self.timeout = timeout if timeout is not None else settings.jira_timeout

        # 验证必需配置
        if not self.url or not self.email or not self.api_token:
            raise ValueError(
                "Jira 配置不完整，请设置 JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN 环境变量"
            )

        self._client: Optional[JIRA] = None
        self._is_connected = False

    @property
    def client(self) -> JIRA:
        """获取 Jira 客户端实例（懒加载）"""
        if self._client is None:
            self._connect()
        return self._client

    def _connect(self) -> None:
        """建立 Jira 连接"""
        try:
            logger.info(f"正在连接 Jira: {self.url}")
            self._client = JIRA(
                server=self.url,
                basic_auth=(self.email, self.api_token),
                timeout=self.timeout,
                max_retries=3
            )
            self._is_connected = True
            logger.info("Jira 连接成功")
        except JIRAError as e:
            if e.status_code == 401:
                raise JiraAuthenticationError(f"Jira 认证失败: {e.text}")
            elif e.status_code == 403:
                raise JiraAuthenticationError(f"Jira 权限不足: {e.text}")
            else:
                raise JiraConnectionError(f"Jira 连接失败: {e.text}")
        except Exception as e:
            raise JiraConnectionError(f"Jira 连接异常: {str(e)}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((JiraAPIError, JiraConnectionError))
    )
    async def health_check(self) -> JiraHealthStatus:
        """
        健康检查

        Returns:
            JiraHealthStatus: 健康状态信息
        """
        try:
            # 获取服务器信息
            server_info = self.client.server_info()

            # 获取可访问的项目列表（最多 10 个）
            projects = self.client.projects()[:10]
            project_keys = [p.key for p in projects]

            return JiraHealthStatus(
                is_connected=True,
                server_info={
                    "version": server_info.get("version"),
                    "build_number": server_info.get("buildNumber"),
                    "server_title": server_info.get("serverTitle")
                },
                accessible_projects=project_keys,
                error_message=None,
                checked_at=datetime.now()
            )
        except JIRAError as e:
            return JiraHealthStatus(
                is_connected=False,
                server_info=None,
                accessible_projects=[],
                error_message=f"Jira API 错误: {e.text}",
                checked_at=datetime.now()
            )
        except Exception as e:
            return JiraHealthStatus(
                is_connected=False,
                server_info=None,
                accessible_projects=[],
                error_message=f"健康检查失败: {str(e)}",
                checked_at=datetime.now()
            )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(JiraAPIError)
    )
    def fetch_issues(
        self,
        project_key: Optional[str] = None,
        jql: Optional[str] = None,
        start_at: int = 0,
        max_results: int = 100,
        expand: Optional[List[str]] = None
    ) -> JiraIssuePage:
        """
        查询 Issue 列表（支持分页）

        Args:
            project_key: 项目 KEY（可选，默认查询所有项目）
            jql: 自定义 JQL 查询语句（可选）
            start_at: 起始位置（分页）
            max_results: 每页数量
            expand: 需要扩展的字段（如 changelog, renderedFields）

        Returns:
            JiraIssuePage: 分页查询结果
        """
        try:
            # 构建 JQL 查询
            if jql:
                query = jql
            elif project_key:
                query = f"project = {project_key} ORDER BY updated DESC"
            else:
                # 默认查询配置的项目，或所有项目
                default_project = settings.jira_project_key
                if default_project:
                    query = f"project = {default_project} ORDER BY updated DESC"
                else:
                    query = "ORDER BY updated DESC"

            logger.info(f"执行 JQL 查询: {query}, start_at={start_at}, max_results={max_results}")

            # 执行查询
            expand_fields = expand or ["changelog"]
            result = self.client.search_issues(
                jql_str=query,
                startAt=start_at,
                maxResults=max_results,
                expand=",".join(expand_fields),
                fields="*all"  # 获取所有字段
            )

            # 解析结果
            issues = []
            for issue in result:
                try:
                    parsed = self._parse_issue(issue)
                    issues.append(parsed)
                except Exception as e:
                    logger.warning(f"解析 Issue {getattr(issue, 'key', 'UNKNOWN')} 失败: {e}")
                    continue

            return JiraIssuePage(
                issues=issues,
                total=result.total,
                start_at=start_at,
                max_results=max_results,
                is_last=start_at + len(issues) >= result.total
            )

        except JIRAError as e:
            if e.status_code == 404:
                raise JiraResourceNotFoundError(f"项目不存在: {project_key}")
            elif e.status_code == 429:
                retry_after = int(e.response.headers.get("Retry-After", 60))
                raise JiraRateLimitError(f"API 限流，请 {retry_after} 秒后重试", retry_after)
            else:
                raise JiraAPIError(f"查询 Issue 失败: {e.text}", e.status_code)
        except Exception as e:
            raise JiraAPIError(f"查询 Issue 异常: {str(e)}")

    def fetch_issue_by_key(self, issue_key: str, expand: Optional[List[str]] = None) -> JiraIssue:
        """
        根据 KEY 查询单个 Issue

        Args:
            issue_key: Issue KEY（如 PROJ-123）
            expand: 需要扩展的字段

        Returns:
            JiraIssue: Issue 详细信息
        """
        try:
            expand_fields = expand or ["changelog"]
            issue = self.client.issue(
                issue_key,
                expand=",".join(expand_fields),
                fields="*all"
            )
            return self._parse_issue(issue)
        except JIRAError as e:
            if e.status_code == 404:
                raise JiraResourceNotFoundError(f"Issue 不存在: {issue_key}")
            else:
                raise JiraAPIError(f"查询 Issue 失败: {e.text}", e.status_code)

    def _parse_issue(self, raw_issue: Any) -> JiraIssue:
        """
        解析 Jira Issue 原始数据为结构化模型

        Args:
            raw_issue: Jira API 返回的原始 Issue 对象

        Returns:
            JiraIssue: 解析后的 Issue 模型
        """
        fields = raw_issue.fields

        # 解析基础字段
        issue_data = {
            "id": raw_issue.id,
            "key": raw_issue.key,
            "summary": fields.summary,
            "description": fields.description or "",
            "url": f"{self.url}/browse/{raw_issue.key}"
        }

        # 解析 Issue 类型
        issue_data["issue_type"] = JiraIssueType(
            id=fields.issuetype.id,
            name=fields.issuetype.name,
            icon_url=getattr(fields.issuetype, "iconUrl", None)
        )

        # 解析状态
        issue_data["status"] = JiraStatus(
            id=fields.status.id,
            name=fields.status.name,
            status_category=getattr(fields.status, "statusCategory", {}).get("name")
        )

        # 解析优先级
        if hasattr(fields, "priority") and fields.priority:
            issue_data["priority"] = JiraPriority(
                id=fields.priority.id,
                name=fields.priority.name,
                icon_url=getattr(fields.priority, "iconUrl", None)
            )

        # 解析项目
        issue_data["project"] = JiraProject(
            id=fields.project.id,
            key=fields.project.key,
            name=fields.project.name,
            description=getattr(fields.project, "description", None),
            avatar_url=getattr(fields.project, "avatarUrls", {}).get("48x48")
        )

        # 解析用户
        if hasattr(fields, "reporter") and fields.reporter:
            issue_data["reporter"] = self._parse_user(fields.reporter)
        if hasattr(fields, "assignee") and fields.assignee:
            issue_data["assignee"] = self._parse_user(fields.assignee)

        # 解析时间字段
        issue_data["created"] = self._parse_datetime(fields.created)
        issue_data["updated"] = self._parse_datetime(fields.updated)
        if hasattr(fields, "resolutiondate") and fields.resolutiondate:
            issue_data["resolution_date"] = self._parse_datetime(fields.resolutiondate)
        if hasattr(fields, "duedate") and fields.duedate:
            issue_data["due_date"] = self._parse_datetime(fields.duedate)

        # 解析标签、组件、版本
        issue_data["labels"] = getattr(fields, "labels", [])
        issue_data["components"] = [c.name for c in getattr(fields, "components", [])]
        issue_data["fix_versions"] = [v.name for v in getattr(fields, "fixVersions", [])]

        # 解析评论
        if hasattr(fields, "comment") and fields.comment.comments:
            issue_data["comments"] = [
                self._parse_comment(c) for c in fields.comment.comments
            ]

        # 解析附件
        if hasattr(fields, "attachment") and fields.attachment:
            issue_data["attachments"] = [
                self._parse_attachment(a) for a in fields.attachment
            ]

        # 保存原始数据（用于调试和扩展）
        issue_data["raw_data"] = raw_issue.raw

        return JiraIssue(**issue_data)

    def _parse_user(self, raw_user: Any) -> JiraUser:
        """解析用户信息"""
        return JiraUser(
            account_id=raw_user.accountId,
            display_name=raw_user.displayName,
            email_address=getattr(raw_user, "emailAddress", None),
            avatar_url=getattr(raw_user, "avatarUrls", {}).get("48x48")
        )

    def _parse_comment(self, raw_comment: Any) -> JiraComment:
        """解析评论信息"""
        return JiraComment(
            id=raw_comment.id,
            author=self._parse_user(raw_comment.author),
            body=raw_comment.body,
            created=self._parse_datetime(raw_comment.created),
            updated=self._parse_datetime(raw_comment.updated)
        )

    def _parse_attachment(self, raw_attachment: Any) -> JiraAttachment:
        """解析附件信息"""
        return JiraAttachment(
            id=raw_attachment.id,
            filename=raw_attachment.filename,
            size=raw_attachment.size,
            mime_type=raw_attachment.mimeType,
            content_url=raw_attachment.content,
            created=self._parse_datetime(raw_attachment.created),
            author=self._parse_user(raw_attachment.author) if hasattr(raw_attachment, "author") else None
        )

    @staticmethod
    def _parse_datetime(date_str: str) -> datetime:
        """
        解析 Jira 日期字符串

        Jira 日期格式: '2024-01-01T12:00:00.000+0000'
        """
        try:
            # 移除毫秒和时区（简化处理）
            if "." in date_str:
                date_str = date_str.split(".")[0]
            return datetime.fromisoformat(date_str.replace("+0000", ""))
        except Exception as e:
            logger.warning(f"日期解析失败: {date_str}, 错误: {e}")
            return datetime.now()

    def close(self) -> None:
        """关闭 Jira 连接"""
        if self._client:
            self._client.close()
            self._client = None
            self._is_connected = False
            logger.info("Jira 连接已关闭")

    def __enter__(self):
        """上下文管理器：进入"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器：退出"""
        self.close()


# 全局单例实例（可选）
_global_jira_client: Optional[JiraClient] = None


def get_jira_client() -> JiraClient:
    """
    获取全局 Jira 客户端单例

    Returns:
        JiraClient: Jira 客户端实例
    """
    global _global_jira_client
    if _global_jira_client is None:
        _global_jira_client = JiraClient()
    return _global_jira_client
