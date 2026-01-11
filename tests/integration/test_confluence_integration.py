"""
Confluence Integration Tests
Confluence 集成测试（需要真实的 Confluence 凭据）

环境变量要求:
- CONFLUENCE_URL: Confluence 实例 URL
- CONFLUENCE_EMAIL: Confluence 账号邮箱
- CONFLUENCE_API_TOKEN: Confluence API Token

运行方式:
    pytest tests/integration/test_confluence_integration.py -v
"""

import pytest
import os
import asyncio
from src.integrations.confluence import (
    ConfluenceClient,
    ConfluencePage,
    ConfluenceSpace,
    ConfluenceHealthStatus
)


# 检查是否配置了 Confluence 凭据
CONFLUENCE_CONFIGURED = all([
    os.getenv("CONFLUENCE_URL"),
    os.getenv("CONFLUENCE_EMAIL"),
    os.getenv("CONFLUENCE_API_TOKEN")
])

skip_if_not_configured = pytest.mark.skipif(
    not CONFLUENCE_CONFIGURED,
    reason="Confluence 凭据未配置，跳过集成测试"
)


@skip_if_not_configured
class TestConfluenceIntegration:
    """Confluence 集成测试套件"""

    @pytest.fixture(scope="class")
    def client(self):
        """创建 Confluence 客户端"""
        client = ConfluenceClient(
            url=os.getenv("CONFLUENCE_URL"),
            username=os.getenv("CONFLUENCE_EMAIL"),
            api_token=os.getenv("CONFLUENCE_API_TOKEN")
        )
        yield client
        client.close()

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """测试健康检查"""
        health = await client.health_check()

        assert isinstance(health, ConfluenceHealthStatus)
        assert health.is_connected is True
        assert health.error_message is None
        print(f"\n✓ 健康检查成功")
        print(f"  可访问空间数量: {len(health.accessible_spaces)}")
        if health.accessible_spaces:
            print(f"  空间列表: {', '.join(health.accessible_spaces[:5])}")

    def test_get_all_spaces(self, client):
        """测试获取空间列表"""
        spaces = client.get_all_spaces(limit=10)

        assert isinstance(spaces, list)
        assert len(spaces) > 0
        assert all(isinstance(s, ConfluenceSpace) for s in spaces)

        print(f"\n✓ 成功获取 {len(spaces)} 个空间")
        for space in spaces[:3]:
            print(f"  - {space.key}: {space.name}")

    def test_fetch_pages_from_first_space(self, client):
        """测试从第一个空间获取页面"""
        # 先获取空间列表
        spaces = client.get_all_spaces(limit=1)
        if not spaces:
            pytest.skip("没有可访问的空间")

        space_key = spaces[0].key
        print(f"\n测试空间: {space_key} - {spaces[0].name}")

        # 获取页面
        result = client.fetch_pages(space_key=space_key, limit=10)

        assert isinstance(result, object)  # ConfluencePagePage
        print(f"✓ 成功获取 {len(result.pages)}/{result.total} 个页面")

        if result.pages:
            print(f"  示例页面:")
            for page in result.pages[:3]:
                print(f"  - {page.title}")
                if page.plain_text:
                    preview = page.plain_text[:100].replace('\n', ' ')
                    print(f"    预览: {preview}...")

    def test_fetch_page_by_id(self, client):
        """测试根据 ID 获取页面"""
        # 先获取页面列表
        spaces = client.get_all_spaces(limit=1)
        if not spaces:
            pytest.skip("没有可访问的空间")

        result = client.fetch_pages(space_key=spaces[0].key, limit=1)
        if not result.pages:
            pytest.skip("空间中没有页面")

        page_id = result.pages[0].id
        print(f"\n测试页面 ID: {page_id}")

        # 获取详细页面
        page = client.fetch_page_by_id(page_id)

        assert isinstance(page, ConfluencePage)
        assert page.id == page_id
        print(f"✓ 成功获取页面: {page.title}")
        print(f"  空间: {page.space.key}")
        print(f"  状态: {page.status}")
        print(f"  创建时间: {page.created_at}")
        print(f"  更新时间: {page.updated_at}")
        if page.version:
            print(f"  版本: {page.version.number}")

    def test_html_to_plain_text_conversion(self, client):
        """测试 HTML 转纯文本"""
        # 获取一个页面
        spaces = client.get_all_spaces(limit=1)
        if not spaces:
            pytest.skip("没有可访问的空间")

        result = client.fetch_pages(space_key=spaces[0].key, limit=1)
        if not result.pages:
            pytest.skip("空间中没有页面")

        page = result.pages[0]
        print(f"\n测试页面: {page.title}")

        # 检查 HTML 内容
        if page.body_storage:
            print(f"  原始 HTML 长度: {len(page.body_storage)} 字符")

        # 检查纯文本转换
        if page.plain_text:
            print(f"  纯文本长度: {len(page.plain_text)} 字符")
            print(f"  纯文本预览:\n{page.plain_text[:200]}...")
            assert len(page.plain_text) > 0
            # 纯文本不应包含 HTML 标签
            assert "<p>" not in page.plain_text
            assert "<div>" not in page.plain_text

    def test_fetch_pages_with_cql(self, client):
        """测试使用 CQL 查询"""
        # 使用 CQL 查询最近更新的页面
        cql = "type=page order by lastmodified desc"
        result = client.fetch_pages(cql=cql, limit=5)

        print(f"\n✓ CQL 查询成功: {cql}")
        print(f"  找到 {len(result.pages)} 个页面")

        for page in result.pages:
            print(f"  - {page.title} (更新于: {page.updated_at})")

    def test_fetch_page_by_title(self, client):
        """测试根据标题查询页面"""
        # 先获取一个页面的标题
        spaces = client.get_all_spaces(limit=1)
        if not spaces:
            pytest.skip("没有可访问的空间")

        result = client.fetch_pages(space_key=spaces[0].key, limit=1)
        if not result.pages:
            pytest.skip("空间中没有页面")

        space_key = spaces[0].key
        title = result.pages[0].title

        print(f"\n查询页面: 空间={space_key}, 标题={title}")

        # 根据标题查询
        page = client.fetch_page_by_title(space_key, title)

        if page:
            assert isinstance(page, ConfluencePage)
            assert page.title == title
            print(f"✓ 成功找到页面: {page.id}")
        else:
            print("⚠ 未找到页面（可能是 API 限制）")

    def test_context_manager(self):
        """测试上下文管理器"""
        print("\n测试上下文管理器")

        with ConfluenceClient(
            url=os.getenv("CONFLUENCE_URL"),
            username=os.getenv("CONFLUENCE_EMAIL"),
            api_token=os.getenv("CONFLUENCE_API_TOKEN")
        ) as client:
            spaces = client.get_all_spaces(limit=1)
            assert len(spaces) > 0
            print(f"✓ 上下文管理器内成功获取 {len(spaces)} 个空间")

        # 退出后客户端应该被关闭
        assert client._client is None
        print("✓ 上下文管理器退出后客户端已关闭")


if __name__ == "__main__":
    """
    直接运行此文件进行测试

    使用方式:
        export CONFLUENCE_URL="https://your-domain.atlassian.net/wiki"
        export CONFLUENCE_EMAIL="your-email@example.com"
        export CONFLUENCE_API_TOKEN="your-api-token"
        python tests/integration/test_confluence_integration.py
    """
    if not CONFLUENCE_CONFIGURED:
        print("❌ Confluence 凭据未配置，无法运行集成测试")
        print("\n请设置以下环境变量:")
        print("  - CONFLUENCE_URL")
        print("  - CONFLUENCE_EMAIL")
        print("  - CONFLUENCE_API_TOKEN")
        exit(1)

    print("🚀 开始运行 Confluence 集成测试...\n")
    pytest.main([__file__, "-v", "-s"])
