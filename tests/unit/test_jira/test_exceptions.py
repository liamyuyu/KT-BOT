"""
Unit tests for Jira Exceptions
Jira 异常类单元测试
"""

import pytest

from src.integrations.jira.exceptions import (
    JiraIntegrationError,
    JiraAuthenticationError,
    JiraConnectionError,
    JiraAPIError,
    JiraResourceNotFoundError,
    JiraRateLimitError
)


class TestJiraExceptions:
    """测试 Jira 异常类"""

    def test_base_exception(self):
        """测试基础异常"""
        error = JiraIntegrationError("Base error message")
        assert str(error) == "Base error message"
        assert isinstance(error, Exception)

    def test_authentication_error(self):
        """测试认证失败异常"""
        error = JiraAuthenticationError("Invalid credentials")
        assert str(error) == "Invalid credentials"
        assert isinstance(error, JiraIntegrationError)

    def test_connection_error(self):
        """测试连接失败异常"""
        error = JiraConnectionError("Connection timeout")
        assert str(error) == "Connection timeout"
        assert isinstance(error, JiraIntegrationError)

    def test_api_error(self):
        """测试 API 错误异常"""
        error = JiraAPIError("API call failed", status_code=500)
        assert str(error) == "API call failed"
        assert error.status_code == 500
        assert isinstance(error, JiraIntegrationError)

    def test_api_error_without_status_code(self):
        """测试 API 错误（无状态码）"""
        error = JiraAPIError("Unknown API error")
        assert str(error) == "Unknown API error"
        assert error.status_code is None

    def test_resource_not_found_error(self):
        """测试资源未找到异常"""
        error = JiraResourceNotFoundError("Issue TEST-999 not found")
        assert str(error) == "Issue TEST-999 not found"
        assert isinstance(error, JiraIntegrationError)

    def test_rate_limit_error(self):
        """测试限流异常"""
        error = JiraRateLimitError("Rate limit exceeded", retry_after=60)
        assert str(error) == "Rate limit exceeded"
        assert error.retry_after == 60
        assert isinstance(error, JiraIntegrationError)

    def test_rate_limit_error_without_retry_after(self):
        """测试限流异常（无重试时间）"""
        error = JiraRateLimitError("Too many requests")
        assert str(error) == "Too many requests"
        assert error.retry_after is None


class TestExceptionHandling:
    """测试异常处理场景"""

    def test_catch_specific_exception(self):
        """测试捕获特定异常"""
        try:
            raise JiraAuthenticationError("Auth failed")
        except JiraAuthenticationError as e:
            assert str(e) == "Auth failed"
        except JiraIntegrationError:
            pytest.fail("Should catch JiraAuthenticationError")

    def test_catch_base_exception(self):
        """测试捕获基础异常"""
        try:
            raise JiraConnectionError("Connection failed")
        except JiraIntegrationError as e:
            assert str(e) == "Connection failed"

    def test_exception_inheritance(self):
        """测试异常继承关系"""
        # 所有 Jira 异常都继承自 JiraIntegrationError
        assert issubclass(JiraAuthenticationError, JiraIntegrationError)
        assert issubclass(JiraConnectionError, JiraIntegrationError)
        assert issubclass(JiraAPIError, JiraIntegrationError)
        assert issubclass(JiraResourceNotFoundError, JiraIntegrationError)
        assert issubclass(JiraRateLimitError, JiraIntegrationError)

    def test_reraise_exception(self):
        """测试重新抛出异常"""
        def inner_function():
            raise JiraAPIError("API error", status_code=400)

        def outer_function():
            try:
                inner_function()
            except JiraAPIError:
                raise  # 重新抛出

        with pytest.raises(JiraAPIError) as exc_info:
            outer_function()

        assert exc_info.value.status_code == 400


class TestExceptionWithContext:
    """测试带上下文的异常"""

    def test_api_error_with_multiple_details(self):
        """测试包含多个细节的 API 错误"""
        error_details = {
            "status_code": 400,
            "error_type": "Bad Request",
            "message": "Invalid JQL query"
        }

        error = JiraAPIError(
            f"API Error: {error_details['message']}",
            status_code=error_details["status_code"]
        )

        assert error.status_code == 400
        assert "Invalid JQL query" in str(error)

    def test_rate_limit_error_with_details(self):
        """测试包含详细信息的限流错误"""
        retry_after = 120
        error = JiraRateLimitError(
            f"Rate limit exceeded. Retry after {retry_after} seconds",
            retry_after=retry_after
        )

        assert error.retry_after == 120
        assert "120 seconds" in str(error)


class TestExceptionMessages:
    """测试异常消息格式"""

    def test_authentication_error_messages(self):
        """测试认证错误消息"""
        test_cases = [
            ("Invalid credentials", "Invalid credentials"),
            ("401 Unauthorized", "401 Unauthorized"),
            ("API token expired", "API token expired"),
        ]

        for message, expected in test_cases:
            error = JiraAuthenticationError(message)
            assert str(error) == expected

    def test_connection_error_messages(self):
        """测试连接错误消息"""
        test_cases = [
            ("Connection timeout", "Connection timeout"),
            ("Network unreachable", "Network unreachable"),
            ("DNS resolution failed", "DNS resolution failed"),
        ]

        for message, expected in test_cases:
            error = JiraConnectionError(message)
            assert str(error) == expected


class TestExceptionComparison:
    """测试异常比较"""

    def test_same_exception_type(self):
        """测试相同异常类型"""
        error1 = JiraAPIError("Error 1", status_code=400)
        error2 = JiraAPIError("Error 2", status_code=400)

        assert type(error1) == type(error2)
        assert error1.status_code == error2.status_code

    def test_different_exception_types(self):
        """测试不同异常类型"""
        error1 = JiraAuthenticationError("Auth error")
        error2 = JiraConnectionError("Connection error")

        assert type(error1) != type(error2)
        assert isinstance(error1, JiraIntegrationError)
        assert isinstance(error2, JiraIntegrationError)
