"""
Unit tests for Confluence Client
Confluence 客户端单元测试
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from src.integrations.confluence.client import ConfluenceClient, get_confluence_client
from src.integrations.confluence.models import (
    ConfluencePage,
    ConfluencePagePage,
    ConfluenceSpace,
    ConfluenceHealthStatus
)
from src.integrations.confluence.exceptions import (
    ConfluenceAuthenticationError,
    ConfluenceConnectionError,
    ConfluenceAPIError,
    ConfluenceResourceNotFoundError,
    ConfluenceRateLimitError
)


class TestConfluenceClientInit:
    """测试 ConfluenceClient 初始化"""

    def test_init_with_parameters(self):
        """测试使用参数初始化"""
        client = ConfluenceClient(
            url="https://test.atlassian.net/wiki",
            username="test@example.com",
            api_token="test_token",
            timeout=60
        )
        assert client.url == "https://test.atlassian.net/wiki"
        assert client.username == "test@example.com"
        assert client.api_token == "test_token"
        assert client.timeout == 60

    def test_init_missing_config(self):
        """测试缺少配置时抛出异常"""
        with pytest.raises(ValueError, match="Confluence 配置不完整"):
            ConfluenceClient(url="", username="", api_token="")

    @patch('src.integrations.confluence.client.settings')
    def test_init_from_settings(self, mock_settings):
        """测试从配置文件读取初始化参数"""
        mock_settings.confluence_url = "https://settings.atlassian.net/wiki"
        mock_settings.confluence_email = "settings@example.com"
        mock_settings.confluence_api_token = "settings_token"
        mock_settings.confluence_timeout = 45

        client = ConfluenceClient()
        assert client.url == "https://settings.atlassian.net/wiki"
        assert client.username == "settings@example.com"
        assert client.api_token == "settings_token"
        assert client.timeout == 45


class TestConfluenceClientConnection:
    """测试 Confluence 连接"""

    @patch('src.integrations.confluence.client.Confluence')
    def test_connect_success(self, mock_confluence_class):
        """测试连接成功"""
        mock_confluence_instance = Mock()
        mock_confluence_instance.get_all_spaces.return_value = {'results': []}
        mock_confluence_class.return_value = mock_confluence_instance

        client = ConfluenceClient(
            url="https://test.atlassian.net/wiki",
            username="test@example.com",
            api_token="token"
        )

        # 触发连接（通过访问 client 属性）
        confluence_client = client.client

        assert confluence_client == mock_confluence_instance
        assert client._is_connected is True
        mock_confluence_class.assert_called_once()

    @patch('src.integrations.confluence.client.Confluence')
    def test_connect_authentication_error(self, mock_confluence_class):
        """测试认证失败"""
        from requests.exceptions import HTTPError

        response = Mock()
        response.status_code = 401
        mock_error = HTTPError()
        mock_error.response = response
        mock_confluence_class.side_effect = mock_error

        client = ConfluenceClient(
            url="https://test.atlassian.net/wiki",
            username="test@example.com",
            api_token="invalid_token"
        )

        with pytest.raises(ConfluenceAuthenticationError, match="认证失败"):
            _ = client.client


class TestConfluenceClientHealthCheck:
    """测试健康检查功能"""

    @pytest.mark.asyncio
    @patch('src.integrations.confluence.client.Confluence')
    async def test_health_check_success(self, mock_confluence_class):
        """测试健康检查成功"""
        mock_client = Mock()
        mock_client.get_all_spaces.return_value = {
            'results': [
                {'key': 'SPACE1', 'name': 'Space 1'},
                {'key': 'SPACE2', 'name': 'Space 2'}
            ]
        }
        mock_confluence_class.return_value = mock_client

        client = ConfluenceClient(
            url="https://test.atlassian.net/wiki",
            username="test@example.com",
            api_token="token"
        )

        health = await client.health_check()

        assert health.is_connected is True
        assert len(health.accessible_spaces) == 2
        assert 'SPACE1' in health.accessible_spaces
        assert health.error_message is None

    @pytest.mark.asyncio
    @patch('src.integrations.confluence.client.Confluence')
    async def test_health_check_failure(self, mock_confluence_class):
        """测试健康检查失败"""
        mock_client = Mock()
        mock_client.get_all_spaces.side_effect = Exception("Connection failed")
        mock_confluence_class.return_value = mock_client

        client = ConfluenceClient(
            url="https://test.atlassian.net/wiki",
            username="test@example.com",
            api_token="token"
        )

        health = await client.health_check()

        assert health.is_connected is False
        assert len(health.accessible_spaces) == 0
        assert "健康检查失败" in health.error_message


class TestConfluenceClientFetchPages:
    """测试获取页面功能"""

    @patch('src.integrations.confluence.client.Confluence')
    def test_fetch_pages_from_space(self, mock_confluence_class):
        """测试从指定空间获取页面"""
        mock_client = Mock()
        mock_client.get_all_pages_from_space.return_value = {
            'results': [
                {
                    'id': '123',
                    'title': 'Test Page',
                    'type': 'page',
                    'status': 'current',
                    'space': {
                        'id': '1',
                        'key': 'TEST',
                        'name': 'Test Space',
                        'type': 'global'
                    },
                    'body': {
                        'storage': {
                            'value': '<p>Test content</p>'
                        }
                    },
                    'version': {
                        'number': 1,
                        'when': '2024-01-01T12:00:00.000Z',
                        'by': {
                            'displayName': 'Test User'
                        }
                    },
                    'history': {
                        'createdDate': '2024-01-01T10:00:00.000Z'
                    },
                    '_links': {
                        'webui': '/spaces/TEST/pages/123'
                    }
                }
            ],
            'totalSize': 1,
            'size': 1
        }
        mock_confluence_class.return_value = mock_client

        client = ConfluenceClient(
            url="https://test.atlassian.net/wiki",
            username="test@example.com",
            api_token="token"
        )

        result = client.fetch_pages(space_key="TEST", limit=25)

        assert isinstance(result, ConfluencePagePage)
        assert len(result.pages) == 1
        assert result.pages[0].title == "Test Page"
        assert result.pages[0].space.key == "TEST"
        assert result.total == 1

    @patch('src.integrations.confluence.client.Confluence')
    def test_fetch_pages_with_cql(self, mock_confluence_class):
        """测试使用 CQL 查询页面"""
        mock_client = Mock()
        mock_client.cql.return_value = {
            'results': [],
            'totalSize': 0,
            'size': 0
        }
        mock_confluence_class.return_value = mock_client

        client = ConfluenceClient(
            url="https://test.atlassian.net/wiki",
            username="test@example.com",
            api_token="token"
        )

        result = client.fetch_pages(cql="type=page and title~'test'")

        assert isinstance(result, ConfluencePagePage)
        assert len(result.pages) == 0
        mock_client.cql.assert_called_once()

    @patch('src.integrations.confluence.client.Confluence')
    def test_fetch_pages_not_found(self, mock_confluence_class):
        """测试查询不存在的空间"""
        from requests.exceptions import HTTPError

        response = Mock()
        response.status_code = 404
        mock_error = HTTPError()
        mock_error.response = response

        mock_client = Mock()
        mock_client.get_all_pages_from_space.side_effect = mock_error
        mock_confluence_class.return_value = mock_client

        client = ConfluenceClient(
            url="https://test.atlassian.net/wiki",
            username="test@example.com",
            api_token="token"
        )

        with pytest.raises(ConfluenceResourceNotFoundError, match="空间不存在"):
            client.fetch_pages(space_key="NOTEXIST")


class TestConfluenceClientFetchPageById:
    """测试根据 ID 获取页面"""

    @patch('src.integrations.confluence.client.Confluence')
    def test_fetch_page_by_id_success(self, mock_confluence_class):
        """测试成功获取页面"""
        mock_client = Mock()
        mock_client.get_page_by_id.return_value = {
            'id': '123',
            'title': 'Test Page',
            'type': 'page',
            'status': 'current',
            'space': {
                'id': '1',
                'key': 'TEST',
                'name': 'Test Space',
                'type': 'global'
            },
            'body': {
                'storage': {
                    'value': '<p>Test content</p>'
                }
            },
            'version': {
                'number': 1,
                'when': '2024-01-01T12:00:00.000Z',
                'by': {
                    'displayName': 'Test User'
                }
            },
            'history': {
                'createdDate': '2024-01-01T10:00:00.000Z'
            },
            '_links': {}
        }
        mock_confluence_class.return_value = mock_client

        client = ConfluenceClient(
            url="https://test.atlassian.net/wiki",
            username="test@example.com",
            api_token="token"
        )

        page = client.fetch_page_by_id("123")

        assert isinstance(page, ConfluencePage)
        assert page.id == "123"
        assert page.title == "Test Page"


class TestConfluenceClientGetSpaces:
    """测试获取空间列表"""

    @patch('src.integrations.confluence.client.Confluence')
    def test_get_all_spaces(self, mock_confluence_class):
        """测试获取所有空间"""
        mock_client = Mock()
        mock_client.get_all_spaces.return_value = {
            'results': [
                {
                    'id': '1',
                    'key': 'SPACE1',
                    'name': 'Space 1',
                    'type': 'global',
                    '_links': {}
                },
                {
                    'id': '2',
                    'key': 'SPACE2',
                    'name': 'Space 2',
                    'type': 'personal',
                    '_links': {}
                }
            ]
        }
        mock_confluence_class.return_value = mock_client

        client = ConfluenceClient(
            url="https://test.atlassian.net/wiki",
            username="test@example.com",
            api_token="token"
        )

        spaces = client.get_all_spaces()

        assert len(spaces) == 2
        assert all(isinstance(s, ConfluenceSpace) for s in spaces)
        assert spaces[0].key == "SPACE1"
        assert spaces[1].key == "SPACE2"


class TestConfluenceClientHTMLParsing:
    """测试 HTML 解析功能"""

    def test_html_to_plain_text_simple(self):
        """测试简单 HTML 转文本"""
        html = "<p>Hello World</p>"
        text = ConfluenceClient._html_to_plain_text(html)
        assert "Hello World" in text

    def test_html_to_plain_text_complex(self):
        """测试复杂 HTML 转文本"""
        html = """
        <div>
            <h1>Title</h1>
            <p>Paragraph 1</p>
            <ul>
                <li>Item 1</li>
                <li>Item 2</li>
            </ul>
        </div>
        """
        text = ConfluenceClient._html_to_plain_text(html)
        assert "Title" in text
        assert "Paragraph 1" in text
        assert "Item 1" in text
        assert "Item 2" in text

    def test_html_to_plain_text_with_entities(self):
        """测试包含 HTML 实体的转换"""
        html = "<p>Price: &pound;10 &amp; free shipping</p>"
        text = ConfluenceClient._html_to_plain_text(html)
        assert "Price:" in text
        assert "10" in text
        assert "free shipping" in text

    def test_html_to_plain_text_empty(self):
        """测试空 HTML"""
        assert ConfluenceClient._html_to_plain_text("") == ""
        assert ConfluenceClient._html_to_plain_text(None) == ""


class TestConfluenceClientContextManager:
    """测试上下文管理器"""

    @patch('src.integrations.confluence.client.Confluence')
    def test_context_manager(self, mock_confluence_class):
        """测试上下文管理器正常工作"""
        mock_client = Mock()
        mock_client.get_all_spaces.return_value = {'results': []}
        mock_confluence_class.return_value = mock_client

        with ConfluenceClient(
            url="https://test.atlassian.net/wiki",
            username="test@example.com",
            api_token="token"
        ) as client:
            assert client is not None
            # 触发懒加载，访问 client 属性
            _ = client.client
            assert client._client is not None

        # 退出后客户端应该被关闭
        assert client._client is None
        assert client._is_connected is False


class TestGetConfluenceClient:
    """测试全局单例函数"""

    @patch('src.integrations.confluence.client.settings')
    def test_get_confluence_client_singleton(self, mock_settings):
        """测试单例模式"""
        mock_settings.confluence_url = "https://test.atlassian.net/wiki"
        mock_settings.confluence_email = "test@example.com"
        mock_settings.confluence_api_token = "token"
        mock_settings.confluence_timeout = 30

        # 重置全局单例
        import src.integrations.confluence.client as client_module
        client_module._global_confluence_client = None

        client1 = get_confluence_client()
        client2 = get_confluence_client()

        assert client1 is client2
