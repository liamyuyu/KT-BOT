"""
Unit tests for Jira Data Models
Jira 数据模型单元测试
"""

import pytest
from datetime import datetime

from src.integrations.jira.models import (
    JiraUser,
    JiraIssueType,
    JiraStatus,
    JiraPriority,
    JiraProject,
    JiraComment,
    JiraAttachment,
    JiraIssue,
    JiraIssuePage,
    JiraHealthStatus
)


class TestJiraUser:
    """测试 JiraUser 模型"""

    def test_create_user(self):
        """测试创建用户"""
        user = JiraUser(
            account_id="123456",
            display_name="John Doe",
            email_address="john@example.com",
            avatar_url="https://avatar.example.com/user.png"
        )
        assert user.account_id == "123456"
        assert user.display_name == "John Doe"
        assert user.email_address == "john@example.com"

    def test_create_user_without_optional_fields(self):
        """测试创建用户（无可选字段）"""
        user = JiraUser(
            account_id="123456",
            display_name="John Doe"
        )
        assert user.account_id == "123456"
        assert user.email_address is None
        assert user.avatar_url is None


class TestJiraIssueType:
    """测试 JiraIssueType 模型"""

    def test_create_issue_type(self):
        """测试创建 Issue 类型"""
        issue_type = JiraIssueType(
            id="1",
            name="Story",
            icon_url="https://icon.example.com/story.png"
        )
        assert issue_type.id == "1"
        assert issue_type.name == "Story"


class TestJiraStatus:
    """测试 JiraStatus 模型"""

    def test_create_status(self):
        """测试创建状态"""
        status = JiraStatus(
            id="1",
            name="In Progress",
            status_category="In Progress"
        )
        assert status.id == "1"
        assert status.name == "In Progress"


class TestJiraPriority:
    """测试 JiraPriority 模型"""

    def test_create_priority(self):
        """测试创建优先级"""
        priority = JiraPriority(
            id="2",
            name="High",
            icon_url="https://icon.example.com/high.png"
        )
        assert priority.id == "2"
        assert priority.name == "High"


class TestJiraProject:
    """测试 JiraProject 模型"""

    def test_create_project(self):
        """测试创建项目"""
        project = JiraProject(
            id="10000",
            key="TEST",
            name="Test Project",
            description="This is a test project"
        )
        assert project.id == "10000"
        assert project.key == "TEST"
        assert project.name == "Test Project"

    def test_create_project_with_lead(self):
        """测试创建项目（带负责人）"""
        lead = JiraUser(
            account_id="123456",
            display_name="Project Lead"
        )
        project = JiraProject(
            id="10000",
            key="TEST",
            name="Test Project",
            lead=lead
        )
        assert project.lead.display_name == "Project Lead"


class TestJiraComment:
    """测试 JiraComment 模型"""

    def test_create_comment(self):
        """测试创建评论"""
        author = JiraUser(
            account_id="123456",
            display_name="Commenter"
        )
        comment = JiraComment(
            id="10001",
            author=author,
            body="This is a comment",
            created=datetime(2024, 1, 1, 10, 0, 0),
            updated=datetime(2024, 1, 1, 11, 0, 0)
        )
        assert comment.id == "10001"
        assert comment.body == "This is a comment"
        assert comment.author.display_name == "Commenter"


class TestJiraAttachment:
    """测试 JiraAttachment 模型"""

    def test_create_attachment(self):
        """测试创建附件"""
        author = JiraUser(
            account_id="123456",
            display_name="Uploader"
        )
        attachment = JiraAttachment(
            id="10002",
            filename="document.pdf",
            size=1024000,
            mime_type="application/pdf",
            content_url="https://example.com/attachments/document.pdf",
            created=datetime(2024, 1, 1, 12, 0, 0),
            author=author
        )
        assert attachment.filename == "document.pdf"
        assert attachment.size == 1024000
        assert attachment.mime_type == "application/pdf"


class TestJiraIssue:
    """测试 JiraIssue 模型"""

    def test_create_issue(self):
        """测试创建完整的 Issue"""
        # 创建关联对象
        issue_type = JiraIssueType(id="1", name="Story")
        status = JiraStatus(id="1", name="To Do")
        project = JiraProject(id="10000", key="TEST", name="Test Project")

        # 创建 Issue
        issue = JiraIssue(
            id="10100",
            key="TEST-1",
            summary="Test Issue",
            description="This is a test issue",
            issue_type=issue_type,
            status=status,
            project=project,
            created=datetime(2024, 1, 1),
            updated=datetime(2024, 1, 2)
        )

        assert issue.id == "10100"
        assert issue.key == "TEST-1"
        assert issue.summary == "Test Issue"
        assert issue.issue_type.name == "Story"
        assert issue.status.name == "To Do"
        assert issue.project.key == "TEST"

    def test_create_issue_with_optional_fields(self):
        """测试创建 Issue（包含可选字段）"""
        issue_type = JiraIssueType(id="1", name="Bug")
        status = JiraStatus(id="2", name="In Progress")
        priority = JiraPriority(id="3", name="High")
        project = JiraProject(id="10000", key="TEST", name="Test Project")

        reporter = JiraUser(account_id="123", display_name="Reporter")
        assignee = JiraUser(account_id="456", display_name="Assignee")

        comment = JiraComment(
            id="10001",
            author=reporter,
            body="Test comment",
            created=datetime(2024, 1, 1),
            updated=datetime(2024, 1, 1)
        )

        issue = JiraIssue(
            id="10100",
            key="TEST-2",
            summary="Bug Issue",
            description="Bug description",
            issue_type=issue_type,
            status=status,
            priority=priority,
            project=project,
            reporter=reporter,
            assignee=assignee,
            created=datetime(2024, 1, 1),
            updated=datetime(2024, 1, 2),
            labels=["bug", "urgent"],
            components=["Backend", "API"],
            comments=[comment]
        )

        assert issue.priority.name == "High"
        assert issue.reporter.display_name == "Reporter"
        assert issue.assignee.display_name == "Assignee"
        assert len(issue.labels) == 2
        assert "bug" in issue.labels
        assert len(issue.components) == 2
        assert len(issue.comments) == 1

    def test_issue_json_serialization(self):
        """测试 Issue JSON 序列化"""
        issue_type = JiraIssueType(id="1", name="Task")
        status = JiraStatus(id="1", name="Done")
        project = JiraProject(id="10000", key="TEST", name="Test Project")

        issue = JiraIssue(
            id="10100",
            key="TEST-3",
            summary="Task Issue",
            issue_type=issue_type,
            status=status,
            project=project,
            created=datetime(2024, 1, 1),
            updated=datetime(2024, 1, 2)
        )

        # 测试 JSON 序列化
        json_data = issue.model_dump()
        assert json_data["key"] == "TEST-3"
        assert json_data["issue_type"]["name"] == "Task"


class TestJiraIssuePage:
    """测试 JiraIssuePage 模型"""

    def test_create_page(self):
        """测试创建分页结果"""
        issue_type = JiraIssueType(id="1", name="Story")
        status = JiraStatus(id="1", name="To Do")
        project = JiraProject(id="10000", key="TEST", name="Test")

        issues = [
            JiraIssue(
                id=f"1010{i}",
                key=f"TEST-{i}",
                summary=f"Issue {i}",
                issue_type=issue_type,
                status=status,
                project=project,
                created=datetime(2024, 1, 1),
                updated=datetime(2024, 1, 2)
            )
            for i in range(1, 6)
        ]

        page = JiraIssuePage(
            issues=issues,
            total=100,
            start_at=0,
            max_results=5,
            is_last=False
        )

        assert len(page.issues) == 5
        assert page.total == 100
        assert page.start_at == 0
        assert page.is_last is False

    def test_page_is_last(self):
        """测试判断是否是最后一页"""
        page = JiraIssuePage(
            issues=[],
            total=10,
            start_at=10,
            max_results=5,
            is_last=True
        )
        assert page.is_last is True


class TestJiraHealthStatus:
    """测试 JiraHealthStatus 模型"""

    def test_create_health_status_connected(self):
        """测试创建健康状态（已连接）"""
        health = JiraHealthStatus(
            is_connected=True,
            server_info={
                "version": "9.4.0",
                "build_number": "12345"
            },
            accessible_projects=["TEST", "DEMO"],
            error_message=None,
            checked_at=datetime(2024, 1, 1, 10, 0, 0)
        )

        assert health.is_connected is True
        assert health.server_info["version"] == "9.4.0"
        assert len(health.accessible_projects) == 2
        assert health.error_message is None

    def test_create_health_status_disconnected(self):
        """测试创建健康状态（未连接）"""
        health = JiraHealthStatus(
            is_connected=False,
            server_info=None,
            accessible_projects=[],
            error_message="Connection timeout",
            checked_at=datetime(2024, 1, 1, 10, 0, 0)
        )

        assert health.is_connected is False
        assert health.server_info is None
        assert len(health.accessible_projects) == 0
        assert health.error_message == "Connection timeout"


class TestDataValidation:
    """测试数据验证"""

    def test_user_validation_missing_required_field(self):
        """测试用户缺少必需字段"""
        with pytest.raises(Exception):  # Pydantic ValidationError
            JiraUser(account_id="123")  # 缺少 display_name

    def test_issue_validation_missing_required_field(self):
        """测试 Issue 缺少必需字段"""
        with pytest.raises(Exception):
            JiraIssue(
                id="10100",
                key="TEST-1"
                # 缺少 summary, issue_type, status, project, created, updated
            )

    def test_project_key_format(self):
        """测试项目 KEY 格式"""
        project = JiraProject(
            id="10000",
            key="TEST-123",  # 包含数字和连字符
            name="Test Project"
        )
        assert project.key == "TEST-123"
