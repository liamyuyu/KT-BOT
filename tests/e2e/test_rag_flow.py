"""
RAG 功能端到端测试

测试完整的 RAG 流程：索引 -> 检索 -> 生成
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
import asyncio
import logging
from typing import List, Dict

from src.core.llm import get_llm_manager
from src.core.vectordb import get_chroma_client
from src.core.rag.indexer import DocumentIndexer
from src.core.rag.retriever import VectorRetriever
from src.integrations.jira.models import JiraIssue, JiraComment

logger = logging.getLogger(__name__)


class TestRAGFlow:
    """RAG 流程端到端测试"""

    def __init__(self):
        """初始化测试套件"""
        # 获取组件
        self.llm_manager = get_llm_manager()
        self.chroma_client = get_chroma_client()
        # 测试中不需要实际的 Jira 客户端
        self.indexer = DocumentIndexer(jira_client=None)
        self.retriever = VectorRetriever()

        # 测试集合名称
        self.test_collection_name = "test_e2e_rag_collection"

    async def setup(self):
        """测试前置设置"""
        # 清理测试数据（如果存在）
        try:
            self.chroma_client.delete_collection(self.test_collection_name)
            logger.info(f"Deleted existing test collection: {self.test_collection_name}")
        except Exception as e:
            logger.info(f"No existing test collection to delete: {e}")

    async def teardown(self):
        """测试后清理"""
        try:
            self.chroma_client.delete_collection(self.test_collection_name)
            logger.info(f"Cleaned up test collection: {self.test_collection_name}")
        except Exception as e:
            logger.warning(f"Failed to clean up test collection: {e}")

    def _create_test_issues(self) -> List[JiraIssue]:
        """创建测试用 Jira Issues"""
        return [
            JiraIssue(
                issue_id="TEST-001",
                issue_key="TEST-001",
                project_key="TEST",
                summary="如何配置 Kubernetes 集群",
                description="""
                ## 问题描述
                需要在生产环境部署 Kubernetes 集群，包括以下要求：

                1. 高可用配置（3 个 master 节点）
                2. 使用 Calico 网络插件
                3. 配置存储类（StorageClass）
                4. 启用 RBAC 权限控制

                ## 环境信息
                - OS: Ubuntu 22.04
                - Kubernetes: v1.28.0
                - Docker: 24.0.5
                """,
                issue_type="Task",
                status="Done",
                priority="High",
                created_at="2025-01-10T10:00:00Z",
                updated_at="2025-01-12T15:30:00Z",
                reporter="user1@example.com",
                assignee="admin@example.com",
                labels=["kubernetes", "devops", "production"],
                components=["Infrastructure"],
                comments=[
                    JiraComment(
                        comment_id="comment-1",
                        author="admin@example.com",
                        created_at="2025-01-11T09:00:00Z",
                        body="""
                        建议使用 kubeadm 部署：

                        ```bash
                        # 初始化第一个 master 节点
                        kubeadm init --control-plane-endpoint="k8s-api:6443" --upload-certs

                        # 安装 Calico
                        kubectl apply -f https://docs.projectcalico.org/manifests/calico.yaml
                        ```
                        """
                    )
                ]
            ),
            JiraIssue(
                issue_id="TEST-002",
                issue_key="TEST-002",
                project_key="TEST",
                summary="Python FastAPI 最佳实践",
                description="""
                ## 需求
                总结 FastAPI 开发的最佳实践，包括：

                - 项目结构
                - 依赖注入
                - 异步处理
                - 错误处理
                - 测试策略

                ## 参考资料
                - FastAPI 官方文档
                - Real Python 教程
                """,
                issue_type="Documentation",
                status="In Progress",
                priority="Medium",
                created_at="2025-01-08T14:00:00Z",
                updated_at="2025-01-14T11:20:00Z",
                reporter="developer@example.com",
                assignee="developer@example.com",
                labels=["python", "fastapi", "best-practices"],
                components=["Backend"],
                comments=[
                    JiraComment(
                        comment_id="comment-2",
                        author="developer@example.com",
                        created_at="2025-01-09T10:00:00Z",
                        body="""
                        推荐的项目结构：

                        ```
                        app/
                        ├── api/
                        │   ├── routes/
                        │   ├── dependencies.py
                        │   └── schemas/
                        ├── core/
                        │   ├── config.py
                        │   └── security.py
                        ├── models/
                        └── services/
                        ```

                        使用 Pydantic 进行数据验证，使用依赖注入管理共享资源。
                        """
                    )
                ]
            ),
            JiraIssue(
                issue_id="TEST-003",
                issue_key="TEST-003",
                project_key="TEST",
                summary="数据库连接池优化",
                description="""
                ## 问题
                PostgreSQL 连接池经常耗尽，导致应用响应缓慢。

                ## 当前配置
                - 最大连接数：20
                - 空闲超时：300s
                - 使用 SQLAlchemy 作为 ORM

                ## 期望
                优化连接池配置，提升并发性能
                """,
                issue_type="Bug",
                status="Open",
                priority="High",
                created_at="2025-01-13T16:00:00Z",
                updated_at="2025-01-13T16:00:00Z",
                reporter="dba@example.com",
                assignee=None,
                labels=["database", "performance", "postgresql"],
                components=["Database"],
                comments=[]
            )
        ]

    async def test_01_index_documents(self):
        """测试 1: 文档索引"""
        logger.info("=" * 60)
        logger.info("测试 1: 文档索引")
        logger.info("=" * 60)

        # 创建测试 Issues
        issues = self._create_test_issues()
        logger.info(f"Created {len(issues)} test issues")

        # 索引文档
        result = await self.indexer.index_jira_issues(
            issues=issues,
            collection_name=self.test_collection_name,
            batch_size=10
        )

        # 验证索引结果
        assert result.success_count > 0, "应至少成功索引一个文档"
        assert result.failed_count == 0, f"索引失败: {result.errors}"

        logger.info(f"✅ 索引成功: {result.success_count} 个文档")
        logger.info(f"   - 总 chunks: {result.chunk_count}")
        logger.info(f"   - 耗时: {result.duration_ms}ms")

    async def test_02_retrieve_documents(self):
        """测试 2: 文档检索"""
        logger.info("=" * 60)
        logger.info("测试 2: 文档检索")
        logger.info("=" * 60)

        # 先索引文档
        issues = self._create_test_issues()
        await self.indexer.index_jira_issues(
            issues=issues,
            collection_name=self.test_collection_name
        )

        # 测试查询
        test_queries = [
            ("如何部署 Kubernetes？", "TEST-001"),  # (查询, 期望的 issue_key)
            ("FastAPI 项目结构", "TEST-002"),
            ("PostgreSQL 连接池", "TEST-003"),
        ]

        for query, expected_issue_key in test_queries:
            logger.info(f"\n查询: {query}")

            # 执行检索
            results = await self.retriever.retrieve(
                query=query,
                collection_name=self.test_collection_name,
                top_k=3
            )

            # 验证结果
            assert len(results) > 0, f"查询 '{query}' 应返回结果"

            # 打印结果
            for i, result in enumerate(results, 1):
                source = result.source
                logger.info(
                    f"  [{i}] {source.issue_key} - {source.title} "
                    f"(score: {result.score:.3f})"
                )

            # 验证最相关的结果
            top_result = results[0]
            assert top_result.source.issue_key == expected_issue_key, (
                f"查询 '{query}' 的最相关结果应该是 {expected_issue_key}, "
                f"实际是 {top_result.source.issue_key}"
            )

            logger.info(f"✅ 查询 '{query}' 验证通过")

    async def test_03_retrieve_with_filters(self):
        """测试 3: 带过滤的检索"""
        logger.info("=" * 60)
        logger.info("测试 3: 带过滤的检索")
        logger.info("=" * 60)

        # 先索引文档
        issues = self._create_test_issues()
        await self.indexer.index_jira_issues(
            issues=issues,
            collection_name=self.test_collection_name
        )

        # 测试按优先级过滤
        query = "配置和部署"
        filters = {"priority": "High"}

        logger.info(f"查询: {query}")
        logger.info(f"过滤: {filters}")

        results = await self.retriever.retrieve(
            query=query,
            collection_name=self.test_collection_name,
            top_k=5,
            filters=filters
        )

        # 验证结果都是 High 优先级
        for result in results:
            assert result.source.priority == "High", (
                f"结果 {result.source.issue_key} 的优先级应该是 High"
            )
            logger.info(
                f"  ✓ {result.source.issue_key} - {result.source.title} "
                f"(priority: {result.source.priority})"
            )

        logger.info(f"✅ 过滤测试通过，返回 {len(results)} 个 High 优先级文档")

    async def test_04_semantic_search(self):
        """测试 4: 语义检索"""
        logger.info("=" * 60)
        logger.info("测试 4: 语义检索")
        logger.info("=" * 60)

        # 先索引文档
        issues = self._create_test_issues()
        await self.indexer.index_jira_issues(
            issues=issues,
            collection_name=self.test_collection_name
        )

        # 测试语义相似的查询（使用不同的表达方式）
        semantic_queries = [
            ("搭建 K8s 环境", "TEST-001"),  # K8s = Kubernetes
            ("Web 框架最佳实践", "TEST-002"),  # FastAPI 是 Web 框架
            ("数据库性能问题", "TEST-003"),  # 连接池是性能问题
        ]

        for query, expected_issue_key in semantic_queries:
            logger.info(f"\n查询: {query}")

            results = await self.retriever.retrieve(
                query=query,
                collection_name=self.test_collection_name,
                top_k=3
            )

            assert len(results) > 0, f"查询 '{query}' 应返回结果"

            top_result = results[0]
            logger.info(
                f"  Top 1: {top_result.source.issue_key} - {top_result.source.title} "
                f"(score: {top_result.score:.3f})"
            )

            # 语义检索应该能找到相关文档（即使用词不同）
            issue_keys = [r.source.issue_key for r in results]
            assert expected_issue_key in issue_keys, (
                f"查询 '{query}' 应该能找到 {expected_issue_key}"
            )

            logger.info(f"✅ 语义查询 '{query}' 验证通过")

    async def test_05_edge_cases(self):
        """测试 5: 边界情况"""
        logger.info("=" * 60)
        logger.info("测试 5: 边界情况")
        logger.info("=" * 60)

        # 先索引文档
        issues = self._create_test_issues()
        await self.indexer.index_jira_issues(
            issues=issues,
            collection_name=self.test_collection_name
        )

        # 测试空查询
        logger.info("测试空查询...")
        results = await self.retriever.retrieve(
            query="",
            collection_name=self.test_collection_name,
            top_k=3
        )
        assert len(results) == 0, "空查询应返回空结果"
        logger.info("✅ 空查询处理正确")

        # 测试不存在的集合
        logger.info("测试不存在的集合...")
        try:
            results = await self.retriever.retrieve(
                query="test",
                collection_name="non_existent_collection",
                top_k=3
            )
            assert len(results) == 0, "不存在的集合应返回空结果"
            logger.info("✅ 不存在的集合处理正确")
        except Exception as e:
            logger.info(f"✅ 不存在的集合抛出异常: {e}")

        # 测试超长查询
        logger.info("测试超长查询...")
        long_query = "如何部署系统 " * 100  # 超长查询
        results = await self.retriever.retrieve(
            query=long_query,
            collection_name=self.test_collection_name,
            top_k=3
        )
        assert len(results) >= 0, "超长查询应能正常处理"
        logger.info(f"✅ 超长查询处理正确，返回 {len(results)} 个结果")

        logger.info("\n✅ 所有边界情况测试通过")


# 运行测试的辅助函数
async def run_all_tests():
    """运行所有测试"""
    logger.info("=" * 80)
    logger.info("开始 RAG 端到端测试")
    logger.info("=" * 80)

    test_suite = TestRAGFlow()

    # 运行 setup
    await test_suite.setup()

    try:
        # 运行所有测试
        await test_suite.test_01_index_documents()
        await test_suite.test_02_retrieve_documents()
        await test_suite.test_03_retrieve_with_filters()
        await test_suite.test_04_semantic_search()
        await test_suite.test_05_edge_cases()

        logger.info("\n" + "=" * 80)
        logger.info("✅ 所有 RAG 端到端测试通过!")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"\n❌ 测试失败: {e}", exc_info=True)
        raise
    finally:
        # 运行 teardown
        await test_suite.teardown()


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # 运行测试
    asyncio.run(run_all_tests())
