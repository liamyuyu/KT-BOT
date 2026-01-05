"""
Unit tests for Jira Client
Jira 客户端单元测试
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from src.integrations.jira.client import JiraClient, get_jira_client
from src.integrations.jira.models import (
    JiraIssue,
    JiraIssuePage,
    JiraHealthStatus
)
from src.integrations.jira.exceptions import (
    JiraAuthenticationError,
    JiraConnectionError,
    JiraAPIError,
    JiraResourceNotFoundError,
    JiraRateLimitError
)


class TestJiraClientInit:
    """测试 JiraClient 初始化"""

    def test_init_with_parameters(self):
        """测试使用参数初始化"""
        client = JiraClient(
            url="https://test.atlassian.net",
            email="test@example.com",
            api_token="test_token",
            timeout=60
        )
        assert client.url == "https://test.atlassian.net"
        assert client.email == "test@example.com"
        assert client.api_token == "test_token"
        assert client.timeout == 60

    def test_init_missing_config(self):
        """测试缺少配置时抛出异常"""
        with pytest.raises(ValueError, match="Jira 配置不完整"):
            JiraClient(url="", email="", api_token="")

    @patch('src.integrations.jira.client.settings')
    def test_init_from_settings(self, mock_settings):
        """测试从配置文件读取初始化参数"""
        mock_settings.jira_url = "https://settings.atlassian.net"
        mock_settings.jira_email = "settings@example.com"
        mock_settings.jira_api_token = "settings_token"
        mock_settings.jira_timeout = 45

        client = JiraClient()
        assert client.url == "https://settings.atlassian.net"
        assert client.email == "settings@example.com"
        assert client.api_token == "settings_token"
        assert client.timeout == 45


class TestJiraClientConnection:
    """测试 Jira 连接"""

    @patch('src.integrations.jira.client.JIRA')
    def test_connect_success(self, mock_jira_class):
        """测试连接成功"""
        mock_jira_instance = Mock()
        mock_jira_class.return_value = mock_jira_instance

        client = JiraClient(
            url="https://test.atlassian.net",
            email="test@example.com",
            api_token="token"
        )

        # 触发连接（通过访问 client 属性）
        jira_client = client.client

        assert jira_client == mock_jira_instance
        assert client._is_connected is True
        mock_jira_class.assert_called_once()

    @patch('src.integrations.jira.client.JIRA')
    def test_connect_authentication_error(self, mock_jira_class):
        """测试认证失败"""
        from jira import JIRAError

        mock_error = JIRAError(status_code=401, text="Unauthorized")
        mock_jira_class.side_effect = mock_error

        client = JiraClient(
            url="https://test.atlassian.net",
            email="test@example.com",
            api_token="invalid_token"
        )

        with pytest.raises(JiraAuthenticationError, match="认证失败"):
            _ = client.client

    @patch('src.integrations.jira.client.JIRA')
    def test_connect_permission_error(self, mock_jira_class):
        """测试权限不足"""
        from jira import JIRAError

        mock_error = JIRAError(status_code=403, text="Forbidden")
        mock_jira_class.side_effect = mock_error

        client = JiraClient(
            url="https://test.atlassian.net",
            email="test@example.com",
            api_token="token"
        )

        with pytest.raises(JiraAuthenticationError, match="权限不足"):
            _ = client.client


class TestJiraClientHealthCheck:
    """测试健康检查"""

    @pytest.mark.asyncio
    @patch('src.integrations.jira.client.JIRA')
    async def test_health_check_success(self, mock_jira_class):
        """测试健康检查成功"""
        # Mock Jira client
        mock_jira = Mock()
        mock_jira.server_info.return_value = {
            "version": "9.4.0",
            "buildNumber": "12345",
            "serverTitle": "Test Jira"
        }

        # Mock projects
        mock_project = Mock()
        mock_project.key = "TEST"
        mock_jira.projects.return_value = [mock_project]

        mock_jira_class.return_value = mock_jira

        client = JiraClient(
            url="https://test.atlassian.net",
            email="test@example.com",
            api_token="token"
        )

        health = await client.health_check()

        assert health.is_connected is True
        assert health.server_info["version"] == "9.4.0"
        assert "TEST" in health.accessible_projects
        assert health.error_message is None

    @pytest.mark.asyncio
    @patch('src.integrations.jira.client.JIRA')
    async def test_health_check_failure(self, mock_jira_class):
        """测试健康检查失败"""
        from jira import JIRAError

        mock_jira = Mock()
        mock_jira.server_info.side_effect = JIRAError(
            status_code=500,
            text="Internal Server Error"
        )
        mock_jira_class.return_value = mock_jira

        client = JiraClient(
            url="https://test.atlassian.net",
            email="test@example.com",
            api_token="token"
        )

        health = await client.health_check()

        assert health.is_connected is False
        assert health.error_message is not None
        assert "Jira API 错误" in health.error_message


class TestJiraClientFetchIssues:
    """测试 Issue 查询"""

    @patch('src.integrations.jira.client.JIRA')
    def test_fetch_issues_success(self, mock_jira_class):
        """测试查询 Issues 成功"""
        # Mock Issue
        mock_issue = self._create_mock_issue("TEST-1", "Test Issue")

        # Mock search result
        mock_result = Mock()
        mock_result.total = 1
        mock_result.__iter__ = Mock(return_value=iter([mock_issue]))
        mock_result.__len__ = Mock(return_value=1)

        # Mock Jira client
        mock_jira = Mock()
        mock_jira.search_issues.return_value = mock_result
        mock_jira_class.return_value = mock_jira

        client = JiraClient(
            url="https://test.atlassian.net",
            email="test@example.com",
            api_token="token"
        )

        # Fetch issues
        page = client.fetch_issues(project_key="TEST", max_results=10)

        assert isinstance(page, JiraIssuePage)
        assert page.total == 1
        assert len(page.issues) == 1
        assert page.issues[0].key == "TEST-1"

    @patch('src.integrations.jira.client.JIRA')
    def test_fetch_issues_with_pagination(self, mock_jira_class):
        """测试分页查询"""
        mock_issues = [
            self._create_mock_issue(f"TEST-{i}", f"Issue {i}")
            for i in range(1, 6)
        ]

        mock_result = Mock()
        mock_result.total = 100
        mock_result.__iter__ = Mock(return_value=iter(mock_issues))
        mock_result.__len__ = Mock(return_value=5)

        mock_jira = Mock()
        mock_jira.search_issues.return_value = mock_result
        mock_jira_class.return_value = mock_jira

        client = JiraClient(
            url="https://test.atlassian.net",
            email="test@example.com",
            api_token="token"
        )

        # First page
        page = client.fetch_issues(start_at=0, max_results=5)
        assert page.total == 100
        assert len(page.issues) == 5
        assert page.is_last is False

    @patch('src.integrations.jira.client.JIRA')
    def test_fetch_issues_not_found(self, mock_jira_class):
        """测试项目不存在"""
        from jira import JIRAError

        mock_jira = Mock()
        mock_jira.search_issues.side_effect = JIRAError(
            status_code=404,
            text="Project not found"
        )
        mock_jira_class.return_value = mock_jira

        client = JiraClient(
            url="https://test.atlassian.net",
            email="test@example.com",
            api_token="token"
        )

        with pytest.raises(JiraResourceNotFoundError):
            client.fetch_issues(project_key="NOTEXIST")

    @patch('src.integrations.jira.client.JIRA')
    def test_fetch_issues_rate_limit(self, mock_jira_class):
        """测试 API 限流"""
        from jira import JIRAError

        mock_response = Mock()
        mock_response.headers = {"Retry-After": "60"}

        mock_error = JIRAError(status_code=429, text="Too many requests")
        mock_error.response = mock_response

        mock_jira = Mock()
        mock_jira.search_issues.side_effect = mock_error
        mock_jira_class.return_value = mock_jira

        client = JiraClient(
            url="https://test.atlassian.net",
            email="test@example.com",
            api_token="token"
        )

        with pytest.raises(JiraRateLimitError) as exc_info:
            client.fetch_issues()

        assert exc_info.value.retry_after == 60

    @staticmethod
    def _create_mock_issue(key: str, summary: str):
        """创建 Mock Issue 对象"""
        mock_issue = Mock()
        mock_issue.id = key.replace("-", "")
        mock_issue.key = key
        mock_issue.raw = {}

        # Mock fields
        fields = Mock()
        fields.summary = summary
        fields.description = "Test description"
        fields.created = "2024-01-01T00:00:00.000+0000"
        fields.updated = "2024-01-01T12:00:00.000+0000"
        fields.labels = []
        fields.components = []
        fields.fixVersions = []

        # Mock issue type
        issue_type = Mock()
        issue_type.id = "1"
        issue_type.name = "Story"
        fields.issuetype = issue_type

        # Mock status
        status = Mock()
        status.id = "1"
        status.name = "To Do"
        status.statusCategory = {"name": "To Do"}
        fields.status = status

        # Mock project
        project = Mock()
        project.id = "10000"
        project.key = key.split("-")[0]
        project.name = "Test Project"
        fields.project = project

        # Mock comment (remove it if not needed for basic tests)
        # comment = Mock()
        # comment.comments = []
        # fields.comment = comment

        # Mock attachment (remove it if not needed)
        # fields.attachment = []

        mock_issue.fields = fields
        return mock_issue


class TestJiraClientFetchIssueByKey:
    """测试单个 Issue 查询"""

    @patch('src.integrations.jira.client.JIRA')
    def test_fetch_issue_by_key_success(self, mock_jira_class):
        """测试根据 KEY 查询 Issue 成功"""
        mock_issue = TestJiraClientFetchIssues._create_mock_issue("TEST-123", "Test Issue")

        mock_jira = Mock()
        mock_jira.issue.return_value = mock_issue
        mock_jira_class.return_value = mock_jira

        client = JiraClient(
            url="https://test.atlassian.net",
            email="test@example.com",
            api_token="token"
        )

        issue = client.fetch_issue_by_key("TEST-123")
        assert issue.key == "TEST-123"
        assert issue.summary == "Test Issue"

    @patch('src.integrations.jira.client.JIRA')
    def test_fetch_issue_by_key_not_found(self, mock_jira_class):
        """测试 Issue 不存在"""
        from jira import JIRAError

        mock_jira = Mock()
        mock_jira.issue.side_effect = JIRAError(
            status_code=404,
            text="Issue not found"
        )
        mock_jira_class.return_value = mock_jira

        client = JiraClient(
            url="https://test.atlassian.net",
            email="test@example.com",
            api_token="token"
        )

        with pytest.raises(JiraResourceNotFoundError, match="Issue 不存在"):
            client.fetch_issue_by_key("TEST-999")


class TestJiraClientUtilities:
    """测试工具方法"""

    def test_parse_datetime(self):
        """测试日期解析"""
        date_str = "2024-01-15T10:30:45.123+0000"
        result = JiraClient._parse_datetime(date_str)
        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_context_manager(self):
        """测试上下文管理器"""
        client = JiraClient(
            url="https://test.atlassian.net",
            email="test@example.com",
            api_token="token"
        )

        with client as ctx_client:
            assert ctx_client == client

        # 连接应该被关闭（如果已建立）
        # 注意：由于我们没有触发连接，_client 仍然是 None


class TestGetJiraClient:
    """测试全局单例"""

    def test_get_jira_client_singleton(self):
        """测试全局单例模式"""
        # 重置全局变量
        import src.integrations.jira.client as jira_module
        jira_module._global_jira_client = None

        with patch('src.integrations.jira.client.JiraClient') as mock_class:
            mock_instance = Mock()
            mock_class.return_value = mock_instance

            client1 = get_jira_client()
            client2 = get_jira_client()

            # 应该返回同一个实例
            assert client1 == client2
            # JiraClient 应该只被实例化一次
            assert mock_class.call_count == 1
