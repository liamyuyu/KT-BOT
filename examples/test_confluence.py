#!/usr/bin/env python3
"""
Confluence API 客户端测试示例
演示如何使用 ConfluenceClient 访问 Confluence 数据

环境变量要求:
- CONFLUENCE_URL: Confluence 实例 URL (如: https://your-domain.atlassian.net/wiki)
- CONFLUENCE_EMAIL: Confluence 账号邮箱
- CONFLUENCE_API_TOKEN: Confluence API Token

运行方式:
    python examples/test_confluence.py
"""

import os
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.integrations.confluence import (
    ConfluenceClient,
    get_confluence_client,
    ConfluenceConnectionError,
    ConfluenceAuthenticationError
)


def print_section(title: str):
    """打印章节标题"""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


async def test_health_check(client: ConfluenceClient):
    """测试健康检查"""
    print_section("1. 健康检查")

    try:
        health = await client.health_check()

        if health.is_connected:
            print("✅ Confluence 连接成功!")
            print(f"   检查时间: {health.checked_at}")
            print(f"   可访问空间数: {len(health.accessible_spaces)}")

            if health.accessible_spaces:
                print(f"   空间列表 (前 5 个):")
                for space_key in health.accessible_spaces[:5]:
                    print(f"     - {space_key}")
        else:
            print("❌ Confluence 连接失败")
            print(f"   错误信息: {health.error_message}")

        return health.is_connected
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False


def test_get_spaces(client: ConfluenceClient):
    """测试获取空间列表"""
    print_section("2. 获取空间列表")

    try:
        spaces = client.get_all_spaces(limit=10)

        print(f"✅ 成功获取 {len(spaces)} 个空间\n")

        for i, space in enumerate(spaces, 1):
            print(f"{i}. {space.name}")
            print(f"   KEY: {space.key}")
            print(f"   ID: {space.id}")
            print(f"   类型: {space.type}")
            if space.description:
                desc = space.description[:80] + "..." if len(space.description) > 80 else space.description
                print(f"   描述: {desc}")
            if space.url:
                print(f"   URL: {space.url}")
            print()

        return spaces
    except Exception as e:
        print(f"❌ 获取空间失败: {e}")
        return []


def test_get_pages(client: ConfluenceClient, space_key: str = None):
    """测试获取页面列表"""
    print_section(f"3. 获取页面列表 (空间: {space_key or '所有'})")

    try:
        # 分页获取
        start = 0
        limit = 10
        result = client.fetch_pages(space_key=space_key, start=start, limit=limit)

        print(f"✅ 成功获取页面")
        print(f"   总数: {result.total}")
        print(f"   当前页: {len(result.pages)} 个")
        print(f"   起始位置: {result.start}")
        print(f"   是否最后一页: {result.is_last}\n")

        for i, page in enumerate(result.pages, 1):
            print(f"{i}. {page.title}")
            print(f"   ID: {page.id}")
            print(f"   空间: {page.space.key}")
            print(f"   类型: {page.type}")
            print(f"   状态: {page.status}")
            print(f"   创建时间: {page.created_at}")
            print(f"   更新时间: {page.updated_at}")

            if page.version:
                print(f"   版本: v{page.version.number}")

            if page.labels:
                label_names = [l.name for l in page.labels]
                print(f"   标签: {', '.join(label_names)}")

            if page.url:
                print(f"   URL: {page.url}")

            # 显示内容预览
            if page.plain_text:
                preview = page.plain_text[:100].replace('\n', ' ')
                print(f"   预览: {preview}...")

            print()

        return result.pages
    except Exception as e:
        print(f"❌ 获取页面失败: {e}")
        return []


def test_get_page_detail(client: ConfluenceClient, page_id: str):
    """测试获取页面详情"""
    print_section(f"4. 获取页面详情 (ID: {page_id})")

    try:
        page = client.fetch_page_by_id(page_id)

        print(f"✅ 成功获取页面详情\n")
        print(f"标题: {page.title}")
        print(f"ID: {page.id}")
        print(f"类型: {page.type}")
        print(f"状态: {page.status}")
        print(f"空间: {page.space.key} - {page.space.name}")
        print(f"创建时间: {page.created_at}")
        print(f"更新时间: {page.updated_at}")

        if page.created_by:
            print(f"创建者: {page.created_by.display_name}")

        if page.last_modified_by:
            print(f"最后修改者: {page.last_modified_by.display_name}")

        if page.version:
            print(f"\n版本信息:")
            print(f"  版本号: v{page.version.number}")
            if page.version.message:
                print(f"  版本说明: {page.version.message}")
            if page.version.created_by:
                print(f"  修改者: {page.version.created_by.display_name}")

        if page.labels:
            print(f"\n标签: {', '.join([l.name for l in page.labels])}")

        if page.attachments:
            print(f"\n附件 ({len(page.attachments)} 个):")
            for att in page.attachments[:5]:
                size_kb = att.file_size // 1024 if att.file_size else 0
                print(f"  - {att.title} ({size_kb} KB)")

        # 显示内容
        if page.plain_text:
            print(f"\n内容 (纯文本，共 {len(page.plain_text)} 字符):")
            print("-" * 60)
            print(page.plain_text[:500])
            if len(page.plain_text) > 500:
                print("...")
            print("-" * 60)

        if page.url:
            print(f"\nWeb URL: {page.url}")

        return page
    except Exception as e:
        print(f"❌ 获取页面详情失败: {e}")
        return None


def test_cql_query(client: ConfluenceClient):
    """测试 CQL 查询"""
    print_section("5. CQL 查询示例")

    queries = [
        ("最近更新的页面", "type=page order by lastmodified desc"),
        ("包含 'test' 的页面", "type=page and title~'test'"),
        ("本周创建的页面", "type=page and created >= startOfWeek()"),
    ]

    for name, cql in queries:
        print(f"\n查询: {name}")
        print(f"CQL: {cql}")
        print("-" * 40)

        try:
            result = client.fetch_pages(cql=cql, limit=5)
            print(f"✅ 找到 {len(result.pages)} 个结果 (总共 {result.total} 个)")

            for page in result.pages:
                print(f"  - {page.title} (更新于: {page.updated_at})")

        except Exception as e:
            print(f"❌ 查询失败: {e}")

        print()


def test_html_parsing(client: ConfluenceClient):
    """测试 HTML 解析功能"""
    print_section("6. HTML 解析测试")

    test_html = """
    <h1>测试标题</h1>
    <p>这是一个<strong>测试段落</strong>，包含<em>强调文本</em>。</p>
    <ul>
        <li>列表项 1</li>
        <li>列表项 2</li>
        <li>列表项 3</li>
    </ul>
    <p>Price: &pound;10 &amp; free shipping</p>
    """

    plain_text = ConfluenceClient._html_to_plain_text(test_html)

    print("原始 HTML:")
    print("-" * 60)
    print(test_html)
    print("-" * 60)

    print("\n转换后的纯文本:")
    print("-" * 60)
    print(plain_text)
    print("-" * 60)


async def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("  Confluence API 客户端测试")
    print("=" * 60)

    # 检查环境变量
    confluence_url = os.getenv("CONFLUENCE_URL")
    confluence_email = os.getenv("CONFLUENCE_EMAIL")
    confluence_api_token = os.getenv("CONFLUENCE_API_TOKEN")

    if not all([confluence_url, confluence_email, confluence_api_token]):
        print("\n❌ 错误: Confluence 凭据未配置")
        print("\n请设置以下环境变量:")
        print("  export CONFLUENCE_URL='https://your-domain.atlassian.net/wiki'")
        print("  export CONFLUENCE_EMAIL='your-email@example.com'")
        print("  export CONFLUENCE_API_TOKEN='your-api-token'")
        print("\n如何获取 API Token:")
        print("  1. 访问 https://id.atlassian.com/manage-profile/security/api-tokens")
        print("  2. 点击 'Create API token'")
        print("  3. 输入标签名称并创建")
        print("  4. 复制生成的 token")
        return

    print(f"\n配置信息:")
    print(f"  URL: {confluence_url}")
    print(f"  Email: {confluence_email}")
    print(f"  Token: {'*' * 10}{confluence_api_token[-4:]}")

    # 创建客户端
    try:
        client = ConfluenceClient(
            url=confluence_url,
            username=confluence_email,
            api_token=confluence_api_token
        )

        # 1. 健康检查
        is_healthy = await test_health_check(client)
        if not is_healthy:
            print("\n⚠️  连接失败，后续测试将跳过")
            return

        # 2. 获取空间列表
        spaces = test_get_spaces(client)

        # 3. 获取页面列表
        if spaces:
            first_space_key = spaces[0].key
            pages = test_get_pages(client, first_space_key)

            # 4. 获取页面详情
            if pages:
                first_page_id = pages[0].id
                test_get_page_detail(client, first_page_id)

        # 5. CQL 查询
        test_cql_query(client)

        # 6. HTML 解析
        test_html_parsing(client)

        # 关闭客户端
        client.close()
        print_section("测试完成")
        print("✅ 所有测试执行完毕")

    except ConfluenceAuthenticationError as e:
        print(f"\n❌ 认证失败: {e}")
        print("\n请检查:")
        print("  1. Email 是否正确")
        print("  2. API Token 是否有效")
        print("  3. 是否有访问 Confluence 的权限")

    except ConfluenceConnectionError as e:
        print(f"\n❌ 连接失败: {e}")
        print("\n请检查:")
        print("  1. URL 是否正确")
        print("  2. 网络连接是否正常")
        print("  3. 防火墙是否阻止连接")

    except Exception as e:
        print(f"\n❌ 未知错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 运行主函数
    asyncio.run(main())
