"""
Integration tests for Jira Client
Jira 集成测试（需要真实的 Jira 连接）

注意：这些测试需要配置有效的 Jira 凭据
运行方式:
    pytest tests/integration/test_jira_integration.py -v
    pytest tests/integration/test_jira_integration.py -v -m "not slow"  # 跳过慢速测试
"""

import pytest
from src.config import settings
from src.integrations.jira import get_jira_client, JiraClient
from src.integrations.jira.exceptions import (
    JiraAuthenticationError,
    JiraConnectionError
)


# 检查是否配置了 Jira
JIRA_CONFIGURED = bool(
    settings.jira_url and
    settings.jira_email and
    settings.jira_api_token
)

pytestmark = pytest.mark.skipif(
    not JIRA_CONFIGURED,
    reason="Jira 未配置，跳过集成测试。请设置 JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN 环境变量"
)


class TestJiraIntegrationHealthCheck:
    """测试健康检查（集成测试）"""

    @pytest.mark.asyncio
    async def test_health_check_real_connection(self):
        """测试真实的健康检查"""
        client = get_jira_client()
        health = await client.health_check()

        assert health.is_connected is True
        assert health.server_info is not None
        assert "version" in health.server_info
        assert len(health.accessible_projects) > 0

        print(f"\n✅ Jira 服务器版本: {health.server_info.get('version')}")
        print(f"✅ 可访问项目数: {len(health.accessible_projects)}")


class TestJiraIntegrationFetchIssues:
    """测试 Issue 查询（集成测试）"""

    @pytest.mark.slow
    def test_fetch_issues_real(self):
        """测试真实的 Issue 查询"""
        client = get_jira_client()
        page = client.fetch_issues(max_results=5)

        assert page.total >= 0
        assert len(page.issues) <= 5

        if page.issues:
            issue = page.issues[0]
            assert issue.key is not None
            assert issue.summary is not None
            assert issue.project is not None

            print(f"\n✅ 查询到 {page.total} 个 Issues")
            print(f"✅ 第一个 Issue: {issue.key} - {issue.summary}")

    @pytest.mark.slow
    def test_fetch_issues_with_project_key(self):
        """测试按项目查询（如果配置了项目）"""
        if not settings.jira_project_key:
            pytest.skip("未配置 JIRA_PROJECT_KEY，跳过测试")

        client = get_jira_client()
        page = client.fetch_issues(
            project_key=settings.jira_project_key,
            max_results=3
        )

        assert page.total >= 0
        for issue in page.issues:
            assert issue.project.key == settings.jira_project_key

        print(f"\n✅ 项目 {settings.jira_project_key} 有 {page.total} 个 Issues")


class TestJiraIntegrationPagination:
    """测试分页查询（集成测试）"""

    @pytest.mark.slow
    def test_pagination_real(self):
        """测试真实的分页查询"""
        client = get_jira_client()

        # 第一页
        page1 = client.fetch_issues(start_at=0, max_results=2)

        if page1.total > 2:
            # 第二页
            page2 = client.fetch_issues(start_at=2, max_results=2)

            # 验证分页
            assert page1.issues[0].key != page2.issues[0].key
            print(f"\n✅ 分页测试成功")
            print(f"  第 1 页第 1 个: {page1.issues[0].key}")
            print(f"  第 2 页第 1 个: {page2.issues[0].key}")
        else:
            pytest.skip("Issues 数量不足，无法测试分页")


class TestJiraIntegrationErrorHandling:
    """测试错误处理（集成测试）"""

    def test_invalid_project_key(self):
        """测试查询不存在的项目"""
        from src.integrations.jira.exceptions import JiraResourceNotFoundError

        client = get_jira_client()

        with pytest.raises(JiraResourceNotFoundError):
            client.fetch_issues(project_key="NOTEXIST99999")

    def test_invalid_issue_key(self):
        """测试查询不存在的 Issue"""
        from src.integrations.jira.exceptions import JiraResourceNotFoundError

        client = get_jira_client()

        with pytest.raises(JiraResourceNotFoundError):
            client.fetch_issue_by_key("NOTEXIST-99999")


@pytest.mark.skipif(JIRA_CONFIGURED, reason="仅在未配置 Jira 时运行")
class TestJiraIntegrationMissingConfig:
    """测试配置缺失的情况"""

    def test_missing_config_raises_error(self):
        """测试缺少配置时抛出异常"""
        with pytest.raises(ValueError, match="Jira 配置不完整"):
            JiraClient(url="", email="", api_token="")
