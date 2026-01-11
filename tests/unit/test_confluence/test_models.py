"""
Unit tests for Confluence Models
Confluence 数据模型单元测试
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from src.integrations.confluence.models import (
    ConfluenceUser,
    ConfluenceSpace,
    ConfluenceLabel,
    ConfluenceAttachment,
    ConfluenceVersion,
    ConfluencePage,
    ConfluencePagePage,
    ConfluenceHealthStatus
)


class TestConfluenceUser:
    """测试 ConfluenceUser 模型"""

    def test_create_user_cloud(self):
        """测试创建 Cloud 版本用户"""
        user = ConfluenceUser(
            account_id="abc123",
            display_name="John Doe",
            email="john@example.com"
        )
        assert user.account_id == "abc123"
        assert user.display_name == "John Doe"
        assert user.email == "john@example.com"

    def test_create_user_server(self):
        """测试创建 Server 版本用户"""
        user = ConfluenceUser(
            username="johndoe",
            display_name="John Doe"
        )
        assert user.username == "johndoe"
        assert user.display_name == "John Doe"

    def test_user_missing_display_name(self):
        """测试缺少必需字段"""
        with pytest.raises(ValidationError):
            ConfluenceUser(account_id="abc123")


class TestConfluenceSpace:
    """测试 ConfluenceSpace 模型"""

    def test_create_space(self):
        """测试创建空间"""
        space = ConfluenceSpace(
            id="1",
            key="TEST",
            name="Test Space",
            type="global",
            description="A test space"
        )
        assert space.id == "1"
        assert space.key == "TEST"
        assert space.name == "Test Space"
        assert space.type == "global"

    def test_create_space_minimal(self):
        """测试创建最小空间"""
        space = ConfluenceSpace(
            id="1",
            key="TEST",
            name="Test Space",
            type="global"
        )
        assert space.description is None
        assert space.url is None


class TestConfluenceLabel:
    """测试 ConfluenceLabel 模型"""

    def test_create_label(self):
        """测试创建标签"""
        label = ConfluenceLabel(
            id="label123",
            name="important",
            prefix="global"
        )
        assert label.id == "label123"
        assert label.name == "important"
        assert label.prefix == "global"

    def test_create_label_minimal(self):
        """测试创建最小标签"""
        label = ConfluenceLabel(name="test")
        assert label.name == "test"
        assert label.id is None


class TestConfluenceAttachment:
    """测试 ConfluenceAttachment 模型"""

    def test_create_attachment(self):
        """测试创建附件"""
        attachment = ConfluenceAttachment(
            id="att123",
            title="document.pdf",
            filename="document.pdf",
            file_size=1024,
            media_type="application/pdf",
            download_url="https://example.com/download"
        )
        assert attachment.id == "att123"
        assert attachment.title == "document.pdf"
        assert attachment.file_size == 1024

    def test_create_attachment_minimal(self):
        """测试创建最小附件"""
        attachment = ConfluenceAttachment(
            id="att123",
            title="file.txt"
        )
        assert attachment.id == "att123"
        assert attachment.title == "file.txt"


class TestConfluenceVersion:
    """测试 ConfluenceVersion 模型"""

    def test_create_version(self):
        """测试创建版本"""
        created_at = datetime(2024, 1, 1, 12, 0, 0)
        user = ConfluenceUser(
            account_id="user123",
            display_name="John Doe"
        )
        version = ConfluenceVersion(
            number=5,
            message="Updated content",
            minor_edit=False,
            created_at=created_at,
            created_by=user
        )
        assert version.number == 5
        assert version.message == "Updated content"
        assert version.minor_edit is False
        assert version.created_at == created_at
        assert version.created_by.display_name == "John Doe"


class TestConfluencePage:
    """测试 ConfluencePage 模型"""

    def test_create_page(self):
        """测试创建页面"""
        space = ConfluenceSpace(
            id="1",
            key="TEST",
            name="Test Space",
            type="global"
        )

        created_at = datetime(2024, 1, 1, 10, 0, 0)
        updated_at = datetime(2024, 1, 1, 12, 0, 0)

        page = ConfluencePage(
            id="123",
            title="Test Page",
            type="page",
            status="current",
            space=space,
            created_at=created_at,
            updated_at=updated_at,
            body_storage="<p>Test content</p>",
            plain_text="Test content"
        )

        assert page.id == "123"
        assert page.title == "Test Page"
        assert page.type == "page"
        assert page.status == "current"
        assert page.space.key == "TEST"
        assert page.body_storage == "<p>Test content</p>"
        assert page.plain_text == "Test content"

    def test_page_with_version(self):
        """测试带版本的页面"""
        space = ConfluenceSpace(
            id="1",
            key="TEST",
            name="Test Space",
            type="global"
        )

        version = ConfluenceVersion(
            number=3,
            created_at=datetime.now()
        )

        page = ConfluencePage(
            id="123",
            title="Test Page",
            type="page",
            status="current",
            space=space,
            version=version,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        assert page.version is not None
        assert page.version.number == 3

    def test_page_with_labels_and_attachments(self):
        """测试带标签和附件的页面"""
        space = ConfluenceSpace(
            id="1",
            key="TEST",
            name="Test Space",
            type="global"
        )

        labels = [
            ConfluenceLabel(name="important"),
            ConfluenceLabel(name="reviewed")
        ]

        attachments = [
            ConfluenceAttachment(id="att1", title="file1.pdf"),
            ConfluenceAttachment(id="att2", title="file2.doc")
        ]

        page = ConfluencePage(
            id="123",
            title="Test Page",
            type="page",
            status="current",
            space=space,
            labels=labels,
            attachments=attachments,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        assert len(page.labels) == 2
        assert len(page.attachments) == 2
        assert page.labels[0].name == "important"
        assert page.attachments[0].title == "file1.pdf"


class TestConfluencePagePage:
    """测试 ConfluencePagePage 分页模型"""

    def test_create_page_page(self):
        """测试创建分页结果"""
        space = ConfluenceSpace(
            id="1",
            key="TEST",
            name="Test Space",
            type="global"
        )

        pages = [
            ConfluencePage(
                id=str(i),
                title=f"Page {i}",
                type="page",
                status="current",
                space=space,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            for i in range(1, 6)
        ]

        page_page = ConfluencePagePage(
            pages=pages,
            total=100,
            start=0,
            limit=5,
            size=5,
            is_last=False
        )

        assert len(page_page.pages) == 5
        assert page_page.total == 100
        assert page_page.start == 0
        assert page_page.limit == 5
        assert page_page.is_last is False

    def test_page_page_last_page(self):
        """测试最后一页"""
        page_page = ConfluencePagePage(
            pages=[],
            total=10,
            start=10,
            limit=5,
            size=0,
            is_last=True
        )

        assert page_page.is_last is True
        assert len(page_page.pages) == 0


class TestConfluenceHealthStatus:
    """测试 ConfluenceHealthStatus 模型"""

    def test_health_status_connected(self):
        """测试连接成功的健康状态"""
        status = ConfluenceHealthStatus(
            is_connected=True,
            server_info={"version": "7.19.0"},
            accessible_spaces=["SPACE1", "SPACE2"],
            checked_at=datetime.now()
        )

        assert status.is_connected is True
        assert len(status.accessible_spaces) == 2
        assert status.error_message is None

    def test_health_status_failed(self):
        """测试连接失败的健康状态"""
        status = ConfluenceHealthStatus(
            is_connected=False,
            accessible_spaces=[],
            error_message="Connection timeout",
            checked_at=datetime.now()
        )

        assert status.is_connected is False
        assert len(status.accessible_spaces) == 0
        assert status.error_message == "Connection timeout"
