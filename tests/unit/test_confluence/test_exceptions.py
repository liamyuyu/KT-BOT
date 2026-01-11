"""
Unit tests for Confluence Exceptions
Confluence 异常类单元测试
"""

import pytest

from src.integrations.confluence.exceptions import (
    ConfluenceIntegrationError,
    ConfluenceAuthenticationError,
    ConfluenceConnectionError,
    ConfluenceAPIError,
    ConfluenceResourceNotFoundError,
    ConfluenceRateLimitError
)


class TestConfluenceExceptions:
    """测试 Confluence 异常类"""

    def test_base_exception(self):
        """测试基础异常"""
        with pytest.raises(ConfluenceIntegrationError, match="Base error"):
            raise ConfluenceIntegrationError("Base error")

    def test_authentication_error(self):
        """测试认证异常"""
        with pytest.raises(ConfluenceAuthenticationError, match="Auth failed"):
            raise ConfluenceAuthenticationError("Auth failed")

        # 应该是 ConfluenceIntegrationError 的子类
        with pytest.raises(ConfluenceIntegrationError):
            raise ConfluenceAuthenticationError("Auth failed")

    def test_connection_error(self):
        """测试连接异常"""
        with pytest.raises(ConfluenceConnectionError, match="Connection failed"):
            raise ConfluenceConnectionError("Connection failed")

        with pytest.raises(ConfluenceIntegrationError):
            raise ConfluenceConnectionError("Connection failed")

    def test_api_error(self):
        """测试 API 异常"""
        error = ConfluenceAPIError("API failed", status_code=500)

        assert str(error) == "API failed"
        assert error.status_code == 500

        with pytest.raises(ConfluenceAPIError, match="API failed"):
            raise error

    def test_api_error_without_status(self):
        """测试不带状态码的 API 异常"""
        error = ConfluenceAPIError("API failed")
        assert error.status_code is None

    def test_resource_not_found_error(self):
        """测试资源未找到异常"""
        with pytest.raises(ConfluenceResourceNotFoundError, match="Not found"):
            raise ConfluenceResourceNotFoundError("Not found")

        with pytest.raises(ConfluenceIntegrationError):
            raise ConfluenceResourceNotFoundError("Not found")

    def test_rate_limit_error(self):
        """测试限流异常"""
        error = ConfluenceRateLimitError("Rate limited", retry_after=60)

        assert str(error) == "Rate limited"
        assert error.retry_after == 60

        with pytest.raises(ConfluenceRateLimitError, match="Rate limited"):
            raise error

    def test_rate_limit_error_without_retry(self):
        """测试不带重试时间的限流异常"""
        error = ConfluenceRateLimitError("Rate limited")
        assert error.retry_after is None

    def test_exception_inheritance(self):
        """测试异常继承关系"""
        # 所有异常都应该继承自 ConfluenceIntegrationError
        assert issubclass(ConfluenceAuthenticationError, ConfluenceIntegrationError)
        assert issubclass(ConfluenceConnectionError, ConfluenceIntegrationError)
        assert issubclass(ConfluenceAPIError, ConfluenceIntegrationError)
        assert issubclass(ConfluenceResourceNotFoundError, ConfluenceIntegrationError)
        assert issubclass(ConfluenceRateLimitError, ConfluenceIntegrationError)

        # 并且都应该继承自 Exception
        assert issubclass(ConfluenceIntegrationError, Exception)
