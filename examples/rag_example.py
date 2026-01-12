"""
RAG Module Usage Example
RAG 模块使用示例

演示如何使用 RAG 模块进行文档索引和检索
"""

import asyncio
from src.core.rag import (
    DocumentIndexer,
    VectorRetriever,
    ChunkingConfig,
    RetrievalConfig
)


async def index_example():
    """索引示例：从 Jira 索引 Issues"""
    print("=" * 60)
    print("索引示例")
    print("=" * 60)

    # 1. 创建索引器（使用自定义配置）
    chunking_config = ChunkingConfig(
        chunk_size=800,      # 块大小：800 字符
        chunk_overlap=150,   # 重叠：150 字符
        min_chunk_size=50    # 最小块大小：50 字符
    )

    indexer = DocumentIndexer(
        chunking_config=chunking_config,
        collection_name="jira_knowledge",
        batch_size=50
    )

    # 2. 索引 Jira Issues
    print("\n开始索引 Jira Issues...")
    try:
        result = await indexer.index_issues(
            project_key="PROJ",    # 替换为你的项目 KEY
            max_issues=10,         # 最多索引 10 个 Issues（测试用）
            jql=None               # 可选：自定义 JQL 查询
        )

        # 3. 打印结果
        print(f"\n索引完成:")
        print(f"  - 处理文档数: {result.total_documents}")
        print(f"  - 生成块数: {result.total_chunks}")
        print(f"  - 成功数: {result.success_count}")
        print(f"  - 失败数: {result.failed_count}")
        print(f"  - 耗时: {result.duration_seconds:.2f} 秒")

        if result.errors:
            print(f"\n错误列表:")
            for error in result.errors[:5]:  # 只显示前 5 个错误
                print(f"  - {error}")

    except Exception as e:
        print(f"索引失败: {e}")


async def retrieve_example():
    """检索示例：使用向量相似度检索"""
    print("\n" + "=" * 60)
    print("检索示例")
    print("=" * 60)

    # 1. 创建检索器
    retrieval_config = RetrievalConfig(
        top_k=5,              # 返回前 5 个结果
        min_score=0.7,        # 最小相似度分数：0.7
        include_metadata=True # 包含元数据
    )

    retriever = VectorRetriever(
        collection_name="jira_knowledge",
        config=retrieval_config
    )

    # 2. 执行检索
    query = "如何修复登录问题？"  # 替换为你的查询
    print(f"\n查询: {query}")

    try:
        results = await retriever.retrieve(query)

        # 3. 打印结果
        print(f"\n找到 {len(results)} 个相关结果:\n")

        for idx, result in enumerate(results, 1):
            print(f"结果 {idx}:")
            print(f"  - Issue Key: {result.metadata.get('issue_key', 'N/A')}")
            print(f"  - 相似度分数: {result.score:.3f}")
            print(f"  - 内容预览: {result.content[:150]}...")
            print(f"  - 项目: {result.metadata.get('project_name', 'N/A')}")
            print(f"  - 类型: {result.metadata.get('issue_type', 'N/A')}")
            print()

    except Exception as e:
        print(f"检索失败: {e}")


async def full_workflow_example():
    """完整工作流示例：索引 + 检索"""
    print("\n" + "=" * 60)
    print("完整工作流示例")
    print("=" * 60)

    # 1. 索引
    print("\n步骤 1: 索引文档")
    indexer = DocumentIndexer()

    try:
        index_result = await indexer.index_issues(
            project_key="PROJ",  # 替换为你的项目 KEY
            max_issues=5
        )
        print(f"✓ 索引完成: {index_result.total_chunks} 个块")
    except Exception as e:
        print(f"✗ 索引失败: {e}")
        return

    # 2. 检索
    print("\n步骤 2: 检索文档")
    retriever = VectorRetriever()

    queries = [
        "登录问题",
        "性能优化",
        "数据库连接"
    ]

    for query in queries:
        print(f"\n查询: {query}")
        try:
            results = await retriever.retrieve(query, top_k=3)
            print(f"  找到 {len(results)} 个结果")

            if results:
                top_result = results[0]
                print(f"  最相关: {top_result.metadata.get('issue_key')} "
                      f"(分数: {top_result.score:.3f})")
        except Exception as e:
            print(f"  检索失败: {e}")


async def main():
    """主函数"""
    print("\n")
    print("*" * 60)
    print("RAG 模块使用示例")
    print("*" * 60)

    # 提示：需要先配置环境变量
    print("\n注意：运行前请确保已配置以下环境变量:")
    print("  - JIRA_URL: Jira 实例 URL")
    print("  - JIRA_EMAIL: Jira 账号邮箱")
    print("  - JIRA_API_TOKEN: Jira API Token")
    print("  - OLLAMA_HOST: Ollama 服务地址")
    print()

    # 选择要运行的示例
    choice = input("选择示例 (1=索引, 2=检索, 3=完整工作流, 0=全部): ").strip()

    if choice == "1":
        await index_example()
    elif choice == "2":
        await retrieve_example()
    elif choice == "3":
        await full_workflow_example()
    elif choice == "0":
        await index_example()
        await retrieve_example()
        await full_workflow_example()
    else:
        print("无效选择")

    print("\n" + "*" * 60)
    print("示例运行完成")
    print("*" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
