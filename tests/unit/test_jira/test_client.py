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

    @patch('src.integrations.jira.client.settings')
    def test_init_missing_config(self, mock_settings):
        """测试缺少配置时抛出异常"""
        mock_settings.jira_url = ""
        mock_settings.jira_email = ""
        mock_settings.jira_api_token = ""
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

    @patch('src.integrations.jira.client.JIRA')
    def test_connect_other_http_error(self, mock_jira_class):
        """测试其他 HTTP 错误"""
        from jira import JIRAError

        mock_error = JIRAError(status_code=500, text="Internal Server Error")
        mock_jira_class.side_effect = mock_error

        client = JiraClient(
            url="https://test.atlassian.net",
            email="test@example.com",
            api_token="token"
        )

        with pytest.raises(JiraConnectionError, match="连接失败"):
            _ = client.client

    @patch('src.integrations.jira.client.JIRA')
    def test_connect_generic_exception(self, mock_jira_class):
        """测试通用异常"""
        mock_jira_class.side_effect = RuntimeError("Connection failed")

        client = JiraClient(
            url="https://test.atlassian.net",
            email="test@example.com",
            api_token="token"
        )

        with pytest.raises(JiraConnectionError, match="连接异常"):
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

    @patch('src.integrations.jira.client.JIRA')
    def test_fetch_issues_with_jql(self, mock_jira_class):
        """测试使用自定义 JQL 查询"""
        mock_issue = self._create_mock_issue("TEST-1", "Test Issue")

        mock_result = Mock()
        mock_result.total = 1
        mock_result.__iter__ = Mock(return_value=iter([mock_issue]))
        mock_result.__len__ = Mock(return_value=1)

        mock_jira = Mock()
        mock_jira.search_issues.return_value = mock_result
        mock_jira_class.return_value = mock_jira

        client = JiraClient(
            url="https://test.atlassian.net",
            email="test@example.com",
            api_token="token"
        )

        # 使用自定义 JQL
        page = client.fetch_issues(jql="status = 'In Progress'")

        assert page.total == 1
        # 验证使用了自定义JQL
        call_kwargs = mock_jira.search_issues.call_args[1]
        assert call_kwargs['jql_str'] == "status = 'In Progress'"

    @patch('src.integrations.jira.client.settings')
    @patch('src.integrations.jira.client.JIRA')
    def test_fetch_issues_with_default_project(self, mock_jira_class, mock_settings):
        """测试使用默认项目配置"""
        mock_settings.jira_url = "https://test.atlassian.net"
        mock_settings.jira_email = "test@example.com"
        mock_settings.jira_api_token = "token"
        mock_settings.jira_timeout = 30
        mock_settings.jira_project_key = "DEFAULT"

        mock_result = Mock()
        mock_result.total = 0
        mock_result.__iter__ = Mock(return_value=iter([]))
        mock_result.__len__ = Mock(return_value=0)

        mock_jira = Mock()
        mock_jira.search_issues.return_value = mock_result
        mock_jira_class.return_value = mock_jira

        client = JiraClient(
            url="https://test.atlassian.net",
            email="test@example.com",
            api_token="token"
        )

        # 不指定 project_key，应使用默认配置
        client.fetch_issues()

        # 验证使用了默认项目
        call_kwargs = mock_jira.search_issues.call_args[1]
        assert "DEFAULT" in call_kwargs['jql_str']

    @patch('src.integrations.jira.client.JIRA')
    def test_fetch_issues_with_complex_issue(self, mock_jira_class):
        """测试带有完整字段的 Issue"""
        mock_issue = self._create_complete_mock_issue("TEST-1", "Complete Issue")

        mock_result = Mock()
        mock_result.total = 1
        mock_result.__iter__ = Mock(return_value=iter([mock_issue]))
        mock_result.__len__ = Mock(return_value=1)

        mock_jira = Mock()
        mock_jira.search_issues.return_value = mock_result
        mock_jira_class.return_value = mock_jira

        client = JiraClient(
            url="https://test.atlassian.net",
            email="test@example.com",
            api_token="token"
        )

        page = client.fetch_issues(project_key="TEST")

        assert page.total == 1
        assert len(page.issues) == 1
        issue = page.issues[0]
        # 验证解析了所有字段
        assert issue.priority is not None
        assert issue.reporter is not None
        assert issue.assignee is not None
        assert issue.resolution_date is not None
        assert issue.due_date is not None
        assert len(issue.comments) > 0
        assert len(issue.attachments) > 0

    @patch('src.integrations.jira.client.JIRA')
    def test_fetch_issues_parse_error(self, mock_jira_class):
        """测试 Issue 解析失败时跳过该 Issue"""
        # 创建一个会导致解析失败的 Issue
        bad_issue = Mock()
        bad_issue.key = "BAD-1"
        bad_issue.fields = None  # 这会导致解析失败

        good_issue = self._create_mock_issue("GOOD-1", "Good Issue")

        mock_result = Mock()
        mock_result.total = 2
        mock_result.__iter__ = Mock(return_value=iter([bad_issue, good_issue]))
        mock_result.__len__ = Mock(return_value=2)

        mock_jira = Mock()
        mock_jira.search_issues.return_value = mock_result
        mock_jira_class.return_value = mock_jira

        client = JiraClient(
            url="https://test.atlassian.net",
            email="test@example.com",
            api_token="token"
        )

        # 应该跳过坏的Issue，继续处理好的
        page = client.fetch_issues(project_key="TEST")

        assert page.total == 2
        assert len(page.issues) == 1  # 只解析成功了一个
        assert page.issues[0].key == "GOOD-1"

    @patch('src.integrations.jira.client.JIRA')
    def test_fetch_issues_api_error(self, mock_jira_class):
        """测试其他 API 错误（会触发重试）"""
        from jira import JIRAError
        from tenacity import RetryError

        mock_jira = Mock()
        mock_jira.search_issues.side_effect = JIRAError(
            status_code=500,
            text="Internal Server Error"
        )
        mock_jira_class.return_value = mock_jira

        client = JiraClient(
            url="https://test.atlassian.net",
            email="test@example.com",
            api_token="token"
        )

        # 由于 @retry 装饰器，会抛出 RetryError
        with pytest.raises(RetryError):
            client.fetch_issues()

    @staticmethod
    def _create_complete_mock_issue(key: str, summary: str):
        """创建带有所有字段的完整 Mock Issue"""
        mock_issue = Mock()
        mock_issue.id = key.replace("-", "")
        mock_issue.key = key
        mock_issue.raw = {"test": "data"}

        fields = Mock()
        fields.summary = summary
        fields.description = "Test description"
        fields.created = "2024-01-01T00:00:00.000+0000"
        fields.updated = "2024-01-01T12:00:00.000+0000"
        fields.labels = ["label1", "label2"]

        # Mock components - need to set name attribute explicitly
        component1 = Mock()
        component1.name = "Component1"
        fields.components = [component1]

        # Mock versions - need to set name attribute explicitly
        version1 = Mock()
        version1.name = "v1.0"
        fields.fixVersions = [version1]

        # Mock issue type
        issue_type = Mock()
        issue_type.id = "1"
        issue_type.name = "Story"
        issue_type.iconUrl = "https://test.atlassian.net/icon.png"
        fields.issuetype = issue_type

        # Mock status
        status = Mock()
        status.id = "1"
        status.name = "In Progress"
        status.statusCategory = {"name": "In Progress"}
        fields.status = status

        # Mock priority
        priority = Mock()
        priority.id = "2"
        priority.name = "High"
        priority.iconUrl = "https://test.atlassian.net/priority.png"
        fields.priority = priority

        # Mock project
        project = Mock()
        project.id = "10000"
        project.key = key.split("-")[0]
        project.name = "Test Project"
        project.description = "Test project description"
        project.avatarUrls = {"48x48": "https://test.atlassian.net/avatar.png"}
        fields.project = project

        # Mock reporter and assignee
        reporter = Mock()
        reporter.accountId = "reporter123"
        reporter.displayName = "Reporter User"
        reporter.emailAddress = "reporter@test.com"
        reporter.avatarUrls = {"48x48": "https://test.atlassian.net/reporter.png"}
        fields.reporter = reporter

        assignee = Mock()
        assignee.accountId = "assignee123"
        assignee.displayName = "Assignee User"
        assignee.emailAddress = "assignee@test.com"
        assignee.avatarUrls = {"48x48": "https://test.atlassian.net/assignee.png"}
        fields.assignee = assignee

        # Mock dates
        fields.resolutiondate = "2024-01-02T00:00:00.000+0000"
        fields.duedate = "2024-01-03T00:00:00.000+0000"

        # Mock comments
        comment1 = Mock()
        comment1.id = "1"
        comment1.body = "Test comment 1"
        comment1.created = "2024-01-01T10:00:00.000+0000"
        comment1.updated = "2024-01-01T10:00:00.000+0000"
        comment1.author = reporter

        comment_container = Mock()
        comment_container.comments = [comment1]
        fields.comment = comment_container

        # Mock attachments
        attachment1 = Mock()
        attachment1.id = "1"
        attachment1.filename = "test.pdf"
        attachment1.size = 1024
        attachment1.mimeType = "application/pdf"
        attachment1.content = "https://test.atlassian.net/attachment/1"
        attachment1.created = "2024-01-01T09:00:00.000+0000"
        attachment1.author = reporter
        fields.attachment = [attachment1]

        mock_issue.fields = fields
        return mock_issue

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
        issue_type.iconUrl = "https://test.atlassian.net/images/icons/issuetypes/story.png"
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
        project.description = None
        project.avatarUrls = {"48x48": "https://test.atlassian.net/avatar.png"}
        fields.project = project

        # Set optional fields to None to avoid Mock objects
        fields.priority = None
        fields.reporter = None
        fields.assignee = None
        fields.resolutiondate = None
        fields.duedate = None

        # Mock comment with empty list
        comment = Mock()
        comment.comments = []
        fields.comment = comment

        # Mock attachment as empty list
        fields.attachment = []

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

    @patch('src.integrations.jira.client.JIRA')
    def test_fetch_issue_by_key_api_error(self, mock_jira_class):
        """测试其他 API 错误"""
        from jira import JIRAError

        mock_jira = Mock()
        mock_jira.issue.side_effect = JIRAError(
            status_code=500,
            text="Internal Server Error"
        )
        mock_jira_class.return_value = mock_jira

        client = JiraClient(
            url="https://test.atlassian.net",
            email="test@example.com",
            api_token="token"
        )

        with pytest.raises(JiraAPIError, match="查询 Issue 失败"):
            client.fetch_issue_by_key("TEST-123")


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

    def test_parse_datetime_invalid(self):
        """测试日期解析失败时返回当前时间"""
        invalid_date = "invalid-date-string"
        result = JiraClient._parse_datetime(invalid_date)
        assert isinstance(result, datetime)
        # 应该返回当前时间（近似）
        now = datetime.now()
        assert abs((result - now).total_seconds()) < 5

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

    @patch('src.integrations.jira.client.JIRA')
    def test_close_method(self, mock_jira_class):
        """测试关闭连接方法"""
        mock_jira = Mock()
        mock_jira_class.return_value = mock_jira

        client = JiraClient(
            url="https://test.atlassian.net",
            email="test@example.com",
            api_token="token"
        )

        # 触发连接
        _ = client.client
        assert client._is_connected is True

        # 关闭连接
        client.close()

        assert client._client is None
        assert client._is_connected is False
        mock_jira.close.assert_called_once()


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
