"""
Jira Integration Example / Jira 集成示例
演示如何使用 JiraClient 查询 Issue 数据

运行方式:
    python examples/test_jira.py
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.integrations.jira import get_jira_client, JiraClient
from src.integrations.jira.exceptions import (
    JiraAuthenticationError,
    JiraConnectionError,
    JiraAPIError
)


async def test_health_check():
    """测试健康检查"""
    print("\n" + "=" * 60)
    print("测试 1: 健康检查")
    print("=" * 60)

    try:
        client = get_jira_client()
        health = await client.health_check()

        if health.is_connected:
            print("✅ Jira 连接成功!")
            print(f"\n服务器信息:")
            if health.server_info:
                for key, value in health.server_info.items():
                    print(f"  {key}: {value}")

            print(f"\n可访问的项目 ({len(health.accessible_projects)}):")
            for project_key in health.accessible_projects:
                print(f"  - {project_key}")
        else:
            print(f"❌ Jira 连接失败: {health.error_message}")

    except JiraAuthenticationError as e:
        print(f"❌ 认证失败: {e}")
    except JiraConnectionError as e:
        print(f"❌ 连接失败: {e}")
    except Exception as e:
        print(f"❌ 未知错误: {e}")


def test_fetch_issues():
    """测试查询 Issues"""
    print("\n" + "=" * 60)
    print("测试 2: 查询 Issues")
    print("=" * 60)

    try:
        client = get_jira_client()

        # 查询前 10 个 Issue
        print("\n查询参数:")
        print("  - max_results: 10")
        print("  - 排序: 按更新时间降序")

        page = client.fetch_issues(max_results=10)

        print(f"\n查询结果:")
        print(f"  - 总数: {page.total}")
        print(f"  - 当前页: {len(page.issues)} 条")
        print(f"  - 是否最后一页: {page.is_last}")

        # 显示 Issue 列表
        print(f"\nIssue 列表:")
        for i, issue in enumerate(page.issues, 1):
            print(f"\n  {i}. {issue.key}: {issue.summary}")
            print(f"     状态: {issue.status.name} | 类型: {issue.issue_type.name}")
            if issue.assignee:
                print(f"     经办人: {issue.assignee.display_name}")
            print(f"     项目: {issue.project.name} ({issue.project.key})")
            print(f"     更新时间: {issue.updated}")
            print(f"     URL: {issue.url}")

    except JiraAPIError as e:
        print(f"❌ API 调用失败: {e}")
    except Exception as e:
        print(f"❌ 查询失败: {e}")


def test_fetch_issue_by_key():
    """测试查询单个 Issue（需要提供有效的 Issue KEY）"""
    print("\n" + "=" * 60)
    print("测试 3: 查询单个 Issue")
    print("=" * 60)

    # 提示用户输入 Issue KEY
    issue_key = input("\n请输入要查询的 Issue KEY (如 PROJ-123, 直接回车跳过): ").strip()

    if not issue_key:
        print("⏭️  跳过测试")
        return

    try:
        client = get_jira_client()
        issue = client.fetch_issue_by_key(issue_key)

        print(f"\n✅ Issue 详情:")
        print(f"  KEY: {issue.key}")
        print(f"  标题: {issue.summary}")
        print(f"  描述: {issue.description[:100]}..." if len(issue.description) > 100 else f"  描述: {issue.description}")
        print(f"  状态: {issue.status.name}")
        print(f"  类型: {issue.issue_type.name}")
        if issue.priority:
            print(f"  优先级: {issue.priority.name}")
        print(f"  项目: {issue.project.name}")
        if issue.reporter:
            print(f"  报告人: {issue.reporter.display_name}")
        if issue.assignee:
            print(f"  经办人: {issue.assignee.display_name}")
        print(f"  创建时间: {issue.created}")
        print(f"  更新时间: {issue.updated}")

        # 显示标签、组件
        if issue.labels:
            print(f"  标签: {', '.join(issue.labels)}")
        if issue.components:
            print(f"  组件: {', '.join(issue.components)}")

        # 显示评论数量
        print(f"\n  评论数: {len(issue.comments)}")
        if issue.comments:
            print(f"  最新评论: {issue.comments[-1].body[:50]}...")

        # 显示附件数量
        print(f"  附件数: {len(issue.attachments)}")
        if issue.attachments:
            for attachment in issue.attachments:
                print(f"    - {attachment.filename} ({attachment.size} bytes)")

    except Exception as e:
        print(f"❌ 查询失败: {e}")


def test_fetch_by_project():
    """测试按项目查询"""
    print("\n" + "=" * 60)
    print("测试 4: 按项目查询 Issues")
    print("=" * 60)

    project_key = input("\n请输入项目 KEY (如 PROJ, 直接回车跳过): ").strip()

    if not project_key:
        print("⏭️  跳过测试")
        return

    try:
        client = get_jira_client()
        page = client.fetch_issues(project_key=project_key, max_results=5)

        print(f"\n✅ 查询结果:")
        print(f"  项目: {project_key}")
        print(f"  总数: {page.total}")
        print(f"  当前页: {len(page.issues)} 条")

        for i, issue in enumerate(page.issues, 1):
            print(f"\n  {i}. {issue.key}: {issue.summary}")
            print(f"     状态: {issue.status.name}")

    except Exception as e:
        print(f"❌ 查询失败: {e}")


def test_pagination():
    """测试分页查询"""
    print("\n" + "=" * 60)
    print("测试 5: 分页查询")
    print("=" * 60)

    try:
        client = get_jira_client()

        # 第一页
        print("\n📄 第 1 页:")
        page1 = client.fetch_issues(max_results=3, start_at=0)
        print(f"  总数: {page1.total}, 当前: {len(page1.issues)} 条")
        for issue in page1.issues:
            print(f"  - {issue.key}: {issue.summary}")

        # 第二页
        if not page1.is_last:
            print("\n📄 第 2 页:")
            page2 = client.fetch_issues(max_results=3, start_at=3)
            print(f"  总数: {page2.total}, 当前: {len(page2.issues)} 条")
            for issue in page2.issues:
                print(f"  - {issue.key}: {issue.summary}")

    except Exception as e:
        print(f"❌ 分页查询失败: {e}")


async def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("Jira Integration Test / Jira 集成测试")
    print("=" * 60)

    # 检查配置
    from src.config import settings

    if not settings.jira_url or not settings.jira_email or not settings.jira_api_token:
        print("\n❌ Jira 配置不完整!")
        print("\n请在 .env 文件中配置以下环境变量:")
        print("  - JIRA_URL=https://your-company.atlassian.net")
        print("  - JIRA_EMAIL=your-email@company.com")
        print("  - JIRA_API_TOKEN=your_api_token_here")
        print("\n获取 API Token: https://id.atlassian.com/manage-profile/security/api-tokens")
        return

    print(f"\n当前配置:")
    print(f"  JIRA_URL: {settings.jira_url}")
    print(f"  JIRA_EMAIL: {settings.jira_email}")
    print(f"  JIRA_API_TOKEN: {'*' * 20}")

    # 运行测试
    try:
        # 测试 1: 健康检查
        await test_health_check()

        # 测试 2: 查询 Issues
        test_fetch_issues()

        # 测试 3: 查询单个 Issue
        test_fetch_issue_by_key()

        # 测试 4: 按项目查询
        test_fetch_by_project()

        # 测试 5: 分页查询
        test_pagination()

    except KeyboardInterrupt:
        print("\n\n⚠️  测试被中断")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
