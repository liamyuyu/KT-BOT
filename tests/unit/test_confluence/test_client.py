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

    @patch('src.integrations.confluence.client.settings')
    def test_init_missing_config(self, mock_settings):
        """测试缺少配置时抛出异常"""
        mock_settings.confluence_url = ""
        mock_settings.confluence_username = ""
        mock_settings.confluence_api_token = ""
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

    @patch('src.integrations.confluence.client.Confluence')
    def test_connect_permission_error(self, mock_confluence_class):
        """测试权限不足"""
        from requests.exceptions import HTTPError

        response = Mock()
        response.status_code = 403
        mock_error = HTTPError()
        mock_error.response = response
        mock_confluence_class.side_effect = mock_error

        client = ConfluenceClient(
            url="https://test.atlassian.net/wiki",
            username="test@example.com",
            api_token="token"
        )

        with pytest.raises(ConfluenceAuthenticationError, match="权限不足"):
            _ = client.client

    @patch('src.integrations.confluence.client.Confluence')
    def test_connect_network_error(self, mock_confluence_class):
        """测试网络连接失败"""
        from requests.exceptions import ConnectionError as RequestsConnectionError

        mock_confluence_class.side_effect = RequestsConnectionError("Network error")

        client = ConfluenceClient(
            url="https://test.atlassian.net/wiki",
            username="test@example.com",
            api_token="token"
        )

        with pytest.raises(ConfluenceConnectionError, match="网络连接失败"):
            _ = client.client

    @patch('src.integrations.confluence.client.Confluence')
    def test_connect_other_http_error(self, mock_confluence_class):
        """测试其他 HTTP 错误"""
        from requests.exceptions import HTTPError

        response = Mock()
        response.status_code = 500
        http_error = HTTPError()
        http_error.response = response
        mock_confluence_class.side_effect = http_error

        client = ConfluenceClient(
            url="https://test.atlassian.net/wiki",
            username="test@example.com",
            api_token="token"
        )

        with pytest.raises(ConfluenceConnectionError, match="连接失败"):
            _ = client.client

    @patch('src.integrations.confluence.client.Confluence')
    def test_connect_generic_exception(self, mock_confluence_class):
        """测试通用异常"""
        mock_confluence_class.side_effect = RuntimeError("Unexpected error")

        client = ConfluenceClient(
            url="https://test.atlassian.net/wiki",
            username="test@example.com",
            api_token="token"
        )

        with pytest.raises(ConfluenceConnectionError, match="连接异常"):
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

    @patch('src.integrations.confluence.client.Confluence')
    def test_fetch_pages_rate_limit(self, mock_confluence_class):
        """测试 API 限流"""
        from requests.exceptions import HTTPError

        response = Mock()
        response.status_code = 429
        response.headers = {"Retry-After": "120"}
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

        with pytest.raises(ConfluenceRateLimitError) as exc_info:
            client.fetch_pages(space_key="TEST")

        assert exc_info.value.retry_after == 120

    @patch('src.integrations.confluence.client.Confluence')
    def test_fetch_pages_generic_exception(self, mock_confluence_class):
        """测试通用异常（会触发重试）"""
        from tenacity import RetryError

        mock_client = Mock()
        mock_client.get_all_pages_from_space.side_effect = RuntimeError("Unexpected error")
        mock_confluence_class.return_value = mock_client

        client = ConfluenceClient(
            url="https://test.atlassian.net/wiki",
            username="test@example.com",
            api_token="token"
        )

        # 由于 @retry 装饰器，会抛出 RetryError
        with pytest.raises(RetryError):
            client.fetch_pages(space_key="TEST")

    @patch('src.integrations.confluence.client.settings')
    @patch('src.integrations.confluence.client.Confluence')
    def test_fetch_pages_with_default_space(self, mock_confluence_class, mock_settings):
        """测试使用默认空间查询"""
        mock_settings.confluence_url = "https://test.atlassian.net/wiki"
        mock_settings.confluence_username = "test@example.com"
        mock_settings.confluence_api_token = "token"
        mock_settings.confluence_space_key = "DEFAULT"
        mock_settings.confluence_timeout = 30

        mock_client = Mock()
        mock_client.get_all_pages_from_space.return_value = {
            'results': [],
            'size': 0
        }
        mock_confluence_class.return_value = mock_client

        client = ConfluenceClient(
            url="https://test.atlassian.net/wiki",
            username="test@example.com",
            api_token="token"
        )

        # 不指定 space_key，应该使用默认空间
        result = client.fetch_pages()

        assert result.total == 0
        mock_client.get_all_pages_from_space.assert_called_once()
        call_kwargs = mock_client.get_all_pages_from_space.call_args[1]
        assert call_kwargs['space'] == "DEFAULT"

    @patch('src.integrations.confluence.client.settings')
    @patch('src.integrations.confluence.client.Confluence')
    def test_fetch_pages_with_cql_fallback(self, mock_confluence_class, mock_settings):
        """测试无空间配置时使用 CQL 查询"""
        mock_settings.confluence_url = "https://test.atlassian.net/wiki"
        mock_settings.confluence_username = "test@example.com"
        mock_settings.confluence_api_token = "token"
        mock_settings.confluence_space_key = ""  # 无默认空间
        mock_settings.confluence_timeout = 30

        mock_client = Mock()
        mock_client.cql.return_value = {
            'results': [],
            'size': 0
        }
        mock_confluence_class.return_value = mock_client

        client = ConfluenceClient(
            url="https://test.atlassian.net/wiki",
            username="test@example.com",
            api_token="token"
        )

        # 不指定 space_key，且无默认空间，应该使用 CQL
        result = client.fetch_pages()

        assert result.total == 0
        mock_client.cql.assert_called_once()
        call_kwargs = mock_client.cql.call_args[1]
        assert 'cql' in call_kwargs

    @patch('src.integrations.confluence.client.Confluence')
    def test_fetch_pages_with_complex_page(self, mock_confluence_class):
        """测试带有完整字段的页面"""
        mock_client = Mock()
        mock_client.get_all_pages_from_space.return_value = {
            'results': [{
                'id': '123',
                'title': 'Complex Page',
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
                    'number': 2,
                    'when': '2024-01-02T12:00:00.000Z',
                    'by': {
                        'displayName': 'Editor User',
                        'email': 'editor@test.com'
                    }
                },
                'ancestors': [
                    {'id': '100', 'title': 'Parent Page'},
                    {'id': '101', 'title': 'Grandparent Page'}
                ],
                'history': {
                    'createdDate': '2024-01-01T10:00:00.000Z',
                    'createdBy': {
                        'displayName': 'Creator User',
                        'email': 'creator@test.com'
                    }
                },
                'metadata': {
                    'labels': {
                        'results': [
                            {'id': '1', 'name': 'label1', 'prefix': 'global'}
                        ]
                    }
                },
                'children': {
                    'attachment': {
                        'results': [
                            {
                                'id': 'att1',
                                'title': 'test.pdf',
                                'type': 'attachment',
                                'status': 'current',
                                'extensions': {
                                    'mediaType': 'application/pdf',
                                    'fileSize': 1024
                                },
                                'history': {
                                    'createdDate': '2024-01-01T09:00:00.000Z',
                                    'createdBy': {
                                        'displayName': 'Uploader',
                                        'email': 'uploader@test.com'
                                    }
                                },
                                '_links': {
                                    'download': '/download/attachments/123/test.pdf'
                                }
                            }
                        ]
                    }
                },
                '_links': {}
            }],
            'size': 1
        }
        mock_confluence_class.return_value = mock_client

        client = ConfluenceClient(
            url="https://test.atlassian.net/wiki",
            username="test@example.com",
            api_token="token"
        )

        page = client.fetch_pages(space_key="TEST")

        assert page.total == 1
        assert len(page.pages) == 1
        p = page.pages[0]
        # 验证解析了ancestors
        assert p.parent_id == '101'  # 最后一个ancestor
        assert len(p.ancestor_ids) == 2
        # 验证解析了created_by
        assert p.created_by is not None
        # 验证解析了last_modified_by
        assert p.last_modified_by is not None
        # 验证解析了labels
        assert len(p.labels) == 1
        # 验证解析了attachments
        assert len(p.attachments) == 1
        assert p.attachments[0].title == 'test.pdf'

    @patch('src.integrations.confluence.client.Confluence')
    def test_fetch_pages_minimal_fields(self, mock_confluence_class):
        """测试只有最小必需字段的页面"""
        mock_client = Mock()
        mock_client.get_all_pages_from_space.return_value = {
            'results': [{
                'id': '456',
                'title': 'Minimal Page',
                'type': 'page',
                'status': 'current',
                'space': {
                    'id': '1',
                    'key': 'TEST',
                    'name': 'Test Space',
                    'type': 'global'
                },
                # 没有body, version, history等字段
                '_links': {}
            }],
            'size': 1
        }
        mock_confluence_class.return_value = mock_client

        client = ConfluenceClient(
            url="https://test.atlassian.net/wiki",
            username="test@example.com",
            api_token="token"
        )

        page = client.fetch_pages(space_key="TEST")

        assert page.total == 1
        assert len(page.pages) == 1
        p = page.pages[0]
        # 验证使用了默认值
        assert p.created_at is not None
        assert p.updated_at is not None

    @patch('src.integrations.confluence.client.settings')
    @patch('src.integrations.confluence.client.Confluence')
    def test_fetch_pages_no_space_no_cql(self, mock_confluence_class, mock_settings):
        """测试既没有space也没有默认space时使用all pages查询"""
        mock_settings.confluence_url = "https://test.atlassian.net/wiki"
        mock_settings.confluence_username = "test@example.com"
        mock_settings.confluence_api_token = "token"
        mock_settings.confluence_space_key = ""  # 无默认空间
        mock_settings.confluence_timeout = 30

        mock_client = Mock()
        mock_client.get_all_pages_from_space.return_value = {'results': [], 'size': 0}
        mock_client.cql.return_value = {'results': [], 'size': 0}
        mock_confluence_class.return_value = mock_client

        client = ConfluenceClient(
            url="https://test.atlassian.net/wiki",
            username="test@example.com",
            api_token="token"
        )

        # 既不指定space_key，也没有默认空间，既不指定CQL
        # 应该使用CQL fallback
        result = client.fetch_pages()

        assert result.total == 0
        # 应该调用了CQL查询
        mock_client.cql.assert_called()


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

    @patch('src.integrations.confluence.client.Confluence')
    def test_fetch_page_by_id_not_found(self, mock_confluence_class):
        """测试页面不存在"""
        from requests.exceptions import HTTPError

        mock_client = Mock()
        response = Mock()
        response.status_code = 404
        http_error = HTTPError()
        http_error.response = response
        mock_client.get_page_by_id.side_effect = http_error
        mock_confluence_class.return_value = mock_client

        client = ConfluenceClient(
            url="https://test.atlassian.net/wiki",
            username="test@example.com",
            api_token="token"
        )

        with pytest.raises(ConfluenceResourceNotFoundError, match="页面不存在"):
            client.fetch_page_by_id("999")

    @patch('src.integrations.confluence.client.Confluence')
    def test_fetch_page_by_id_api_error(self, mock_confluence_class):
        """测试其他 API 错误"""
        from requests.exceptions import HTTPError

        mock_client = Mock()
        response = Mock()
        response.status_code = 500
        http_error = HTTPError()
        http_error.response = response
        mock_client.get_page_by_id.side_effect = http_error
        mock_confluence_class.return_value = mock_client

        client = ConfluenceClient(
            url="https://test.atlassian.net/wiki",
            username="test@example.com",
            api_token="token"
        )

        with pytest.raises(ConfluenceAPIError, match="查询页面失败"):
            client.fetch_page_by_id("123")


class TestConfluenceClientFetchPageByTitle:
    """测试根据标题获取页面"""

    @patch('src.integrations.confluence.client.Confluence')
    def test_fetch_page_by_title_success(self, mock_confluence_class):
        """测试成功根据标题获取页面"""
        mock_client = Mock()
        mock_client.get_page_by_title.return_value = {
            'id': '456',
            'title': 'Test Page Title',
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
                    'value': '<p>Test content by title</p>'
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

        page = client.fetch_page_by_title(space_key="TEST", title="Test Page Title")

        assert page is not None
        assert page.id == "456"
        assert page.title == "Test Page Title"
        mock_client.get_page_by_title.assert_called_once()

    @patch('src.integrations.confluence.client.Confluence')
    def test_fetch_page_by_title_not_found(self, mock_confluence_class):
        """测试页面不存在返回 None"""
        mock_client = Mock()
        mock_client.get_page_by_title.return_value = None
        mock_confluence_class.return_value = mock_client

        client = ConfluenceClient(
            url="https://test.atlassian.net/wiki",
            username="test@example.com",
            api_token="token"
        )

        page = client.fetch_page_by_title(space_key="TEST", title="Nonexistent Page")

        assert page is None

    @patch('src.integrations.confluence.client.Confluence')
    def test_fetch_page_by_title_http_404(self, mock_confluence_class):
        """测试 404 错误返回 None"""
        from requests.exceptions import HTTPError

        mock_client = Mock()
        response = Mock()
        response.status_code = 404
        http_error = HTTPError()
        http_error.response = response
        mock_client.get_page_by_title.side_effect = http_error
        mock_confluence_class.return_value = mock_client

        client = ConfluenceClient(
            url="https://test.atlassian.net/wiki",
            username="test@example.com",
            api_token="token"
        )

        page = client.fetch_page_by_title(space_key="TEST", title="Test Page")

        assert page is None

    @patch('src.integrations.confluence.client.Confluence')
    def test_fetch_page_by_title_http_error(self, mock_confluence_class):
        """测试其他 HTTP 错误抛出异常"""
        from requests.exceptions import HTTPError

        mock_client = Mock()
        response = Mock()
        response.status_code = 500
        http_error = HTTPError()
        http_error.response = response
        mock_client.get_page_by_title.side_effect = http_error
        mock_confluence_class.return_value = mock_client

        client = ConfluenceClient(
            url="https://test.atlassian.net/wiki",
            username="test@example.com",
            api_token="token"
        )

        with pytest.raises(ConfluenceAPIError, match="查询页面失败"):
            client.fetch_page_by_title(space_key="TEST", title="Test Page")


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

    @patch('src.integrations.confluence.client.Confluence')
    def test_get_all_spaces_api_error(self, mock_confluence_class):
        """测试获取空间列表时的 API 错误"""
        from requests.exceptions import HTTPError

        mock_client = Mock()
        # 先返回成功以通过连接测试，然后在实际调用时失败
        def side_effect_func(limit=None):
            if limit == 1:  # 连接测试调用
                return {'results': []}
            else:  # 实际调用
                response = Mock()
                response.status_code = 500
                http_error = HTTPError()
                http_error.response = response
                raise http_error

        mock_client.get_all_spaces.side_effect = side_effect_func
        mock_confluence_class.return_value = mock_client

        client = ConfluenceClient(
            url="https://test.atlassian.net/wiki",
            username="test@example.com",
            api_token="token"
        )

        with pytest.raises(ConfluenceAPIError, match="获取空间列表失败"):
            client.get_all_spaces()


class TestConfluenceClientUtilities:
    """测试工具方法"""

    @patch('src.integrations.confluence.client.Confluence')
    def test_close_method(self, mock_confluence_class):
        """测试关闭连接方法"""
        mock_client = Mock()
        mock_confluence_class.return_value = mock_client

        client = ConfluenceClient(
            url="https://test.atlassian.net/wiki",
            username="test@example.com",
            api_token="token"
        )

        # 触发连接
        _ = client.client
        assert client._is_connected is True

        # 关闭连接
        client.close()

        assert client._client is None
        assert client._is_connected is False

    def test_context_manager(self):
        """测试上下文管理器"""
        client = ConfluenceClient(
            url="https://test.atlassian.net/wiki",
            username="test@example.com",
            api_token="token"
        )

        with client as ctx_client:
            assert ctx_client == client

        # 连接应该被关闭（如果已建立）
        assert client._client is None


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

    def test_html_to_plain_text_with_tables(self):
        """测试包含表格的 HTML"""
        html = """
        <table>
            <tr>
                <th>Header 1</th>
                <th>Header 2</th>
            </tr>
            <tr>
                <td>Cell 1</td>
                <td>Cell 2</td>
            </tr>
        </table>
        """
        text = ConfluenceClient._html_to_plain_text(html)
        assert "Header 1" in text
        assert "Header 2" in text
        assert "Cell 1" in text
        assert "Cell 2" in text
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
