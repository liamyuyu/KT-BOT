#!/usr/bin/env python3
"""
ChromaDB 向量数据库测试示例
演示如何使用 ChromaDBClient 进行向量存储和检索

运行方式:
    python examples/test_chroma.py
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.vectordb import (
    ChromaDBClient,
    Document,
    get_chroma_client
)


def print_section(title: str):
    """打印章节标题"""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def test_basic_operations():
    """测试基础操作"""
    print_section("1. 基础操作演示")

    # 创建客户端（使用临时目录）
    client = ChromaDBClient(
        persist_directory="./data/chroma_example",
        collection_name="example_collection",
        use_persistent=True
    )

    print("✅ ChromaDB 客户端创建成功")
    print(f"   持久化目录: ./data/chroma_example")
    print(f"   Collection 名称: example_collection")

    # 健康检查
    health = client.health_check()
    print(f"\n✅ 健康检查:")
    print(f"   连接状态: {'✓ 已连接' if health.is_connected else '✗ 未连接'}")
    print(f"   ChromaDB 版本: {health.version}")
    print(f"   Collections 数量: {len(health.collections)}")
    print(f"   总文档数: {health.total_documents}")

    return client


def test_add_documents(client: ChromaDBClient):
    """测试添加文档"""
    print_section("2. 添加文档")

    # 添加单个文档
    doc1 = Document(
        id="doc_001",
        content="Python 是一种高级编程语言，以其简洁的语法和强大的功能而闻名。",
        metadata={
            "source": "tech_docs",
            "category": "programming",
            "language": "python",
            "created_at": "2024-01-12"
        }
    )

    client.add_document(doc1)
    print(f"✅ 添加单个文档成功: {doc1.id}")
    print(f"   内容预览: {doc1.content[:50]}...")

    # 批量添加文档
    docs = [
        Document(
            id="doc_002",
            content="机器学习是人工智能的一个分支，通过算法让计算机从数据中学习。",
            metadata={"source": "tech_docs", "category": "ai", "topic": "machine_learning"}
        ),
        Document(
            id="doc_003",
            content="深度学习使用神经网络来处理复杂的数据模式，在图像识别领域表现出色。",
            metadata={"source": "tech_docs", "category": "ai", "topic": "deep_learning"}
        ),
        Document(
            id="doc_004",
            content="自然语言处理（NLP）使计算机能够理解和生成人类语言。",
            metadata={"source": "tech_docs", "category": "ai", "topic": "nlp"}
        ),
        Document(
            id="conf_001",
            content="Confluence 是 Atlassian 公司的协作文档平台，支持团队知识管理。",
            metadata={"source": "confluence", "category": "tools", "product": "confluence"}
        ),
        Document(
            id="jira_001",
            content="Jira 是项目管理和问题跟踪工具，广泛用于敏捷开发团队。",
            metadata={"source": "jira", "category": "tools", "product": "jira"}
        ),
    ]

    result = client.add_documents(docs, batch_size=10)
    print(f"\n✅ 批量添加文档:")
    print(f"   成功: {result.inserted_count} 个")
    print(f"   失败: {result.failed_count} 个")

    # 获取 Collection 信息
    info = client.get_collection_info()
    print(f"\n📊 Collection 统计:")
    print(f"   名称: {info.name}")
    print(f"   文档总数: {info.count}")


def test_search(client: ChromaDBClient):
    """测试向量搜索"""
    print_section("3. 向量相似度搜索")

    # 搜索 1: 查找与"机器学习"相关的文档
    print("🔍 查询: '机器学习和深度学习'")
    results = client.search("机器学习和深度学习", n_results=3)

    print(f"✅ 找到 {len(results.results)} 个相关文档:\n")
    for i, result in enumerate(results.results, 1):
        print(f"{i}. 文档 ID: {result.id}")
        print(f"   相似度分数: {result.score:.3f} (距离: {result.distance:.3f})")
        print(f"   元数据: {result.metadata}")
        print(f"   内容: {result.content[:60]}...")
        print()

    # 搜索 2: 带过滤条件
    print("🔍 查询: 'AI 相关工具' (仅搜索 tools 分类)")
    results = client.search(
        "AI 相关工具",
        n_results=5,
        where={"category": "tools"}
    )

    print(f"✅ 找到 {len(results.results)} 个工具文档:\n")
    for result in results.results:
        print(f"   - {result.id}: {result.metadata.get('product', 'N/A')}")
        print(f"     {result.content[:50]}...")
        print()


def test_get_and_delete(client: ChromaDBClient):
    """测试获取和删除文档"""
    print_section("4. 获取和删除文档")

    # 获取单个文档
    doc = client.get_document("doc_001")
    if doc:
        print(f"✅ 获取文档成功:")
        print(f"   ID: {doc.id}")
        print(f"   内容: {doc.content[:60]}...")
        print(f"   元数据: {doc.metadata}")
    else:
        print("⚠️  文档不存在")

    # 删除单个文档
    print(f"\n🗑️  删除文档: doc_004")
    result = client.delete_document("doc_004")
    if result:
        print(f"✅ 删除成功")

    # 批量删除
    print(f"\n🗑️  批量删除所有 'tools' 分类的文档")
    count = client.delete_documents(where={"category": "tools"})
    print(f"✅ 删除了 {count} 个文档")

    # 查看最新统计
    info = client.get_collection_info()
    print(f"\n📊 删除后的 Collection 统计:")
    print(f"   文档总数: {info.count}")


def test_collections(client: ChromaDBClient):
    """测试 Collection 管理"""
    print_section("5. Collection 管理")

    # 创建新的 Collection
    client.get_or_create_collection(
        "test_collection_2",
        metadata={"description": "第二个测试集合"}
    )
    print("✅ 创建新 Collection: test_collection_2")

    # 列出所有 Collections
    collections = client.list_collections()
    print(f"\n📋 所有 Collections ({len(collections)} 个):")
    for col in collections:
        print(f"   - {col.name}: {col.count} 个文档")
        if col.metadata:
            print(f"     元数据: {col.metadata}")


def test_context_manager():
    """测试上下文管理器"""
    print_section("6. 使用上下文管理器")

    with ChromaDBClient(
        persist_directory="./data/chroma_context",
        collection_name="context_test"
    ) as client:
        print("✅ 进入上下文管理器")

        # 添加测试文档
        doc = Document(
            id="context_doc",
            content="这是上下文管理器测试文档",
            metadata={"test": True}
        )
        client.add_document(doc)
        print(f"✅ 在上下文中添加文档: {doc.id}")

        # 搜索
        results = client.search("测试", n_results=1)
        print(f"✅ 搜索结果: {len(results.results)} 个")

    print("✅ 退出上下文管理器，客户端已自动关闭")


def test_global_singleton():
    """测试全局单例"""
    print_section("7. 使用全局单例客户端")

    # 使用全局单例
    client = get_chroma_client()
    print("✅ 获取全局单例客户端")

    health = client.health_check()
    print(f"   连接状态: {'✓ 已连接' if health.is_connected else '✗ 未连接'}")

    # 再次获取，应该是同一个实例
    client2 = get_chroma_client()
    assert client is client2
    print("✅ 验证单例模式：两次获取的是同一个实例")


def cleanup_example_data():
    """清理示例数据"""
    print_section("8. 清理示例数据")

    try:
        import shutil
        shutil.rmtree("./data/chroma_example", ignore_errors=True)
        shutil.rmtree("./data/chroma_context", ignore_errors=True)
        print("✅ 示例数据已清理")
    except Exception as e:
        print(f"⚠️  清理失败: {e}")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("  ChromaDB 向量数据库使用示例")
    print("=" * 60)

    try:
        # 1. 基础操作
        client = test_basic_operations()

        # 2. 添加文档
        test_add_documents(client)

        # 3. 搜索
        test_search(client)

        # 4. 获取和删除
        test_get_and_delete(client)

        # 5. Collection 管理
        test_collections(client)

        # 关闭客户端
        client.close()

        # 6. 上下文管理器
        test_context_manager()

        # 7. 全局单例
        test_global_singleton()

        # 8. 清理
        cleanup_example_data()

        print_section("✨ 示例演示完成！")
        print("💡 提示:")
        print("   - 所有数据已保存到 ./data/chroma_example")
        print("   - 可以多次运行此脚本测试持久化功能")
        print("   - 使用 get_chroma_client() 获取全局单例")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n" + "=" * 60)
        print("  示例执行结束")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
