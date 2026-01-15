"""
RAG 功能简化端到端测试（不依赖 Jira 客户端）

测试完整的 RAG 流程：分块 -> 索引 -> 检索
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import logging
from typing import List

from src.core.llm import get_llm_manager
from src.core.vectordb import get_chroma_client
from src.core.rag.chunker import TextChunker
from src.core.rag.retriever import VectorRetriever

logger = logging.getLogger(__name__)


class TestSimpleRAGFlow:
    """RAG 流程简化测试（不需要 Jira 客户端）"""

    def __init__(self):
        """初始化测试套件"""
        self.llm_manager = get_llm_manager()
        self.chroma_client = get_chroma_client()
        self.chunker = TextChunker()
        self.retriever = VectorRetriever()
        self.test_collection_name = "test_simple_rag_collection"

    async def setup(self):
        """测试前置设置"""
        try:
            self.chroma_client.delete_collection(self.test_collection_name)
            logger.info(f"Deleted existing collection: {self.test_collection_name}")
        except Exception as e:
            logger.info(f"No existing collection: {e}")

    async def teardown(self):
        """测试后清理"""
        try:
            self.chroma_client.delete_collection(self.test_collection_name)
            logger.info(f"Cleaned up collection: {self.test_collection_name}")
        except Exception as e:
            logger.warning(f"Failed to cleanup: {e}")

    def _get_test_documents(self) -> List[dict]:
        """创建测试文档"""
        return [
            {
                "id": "doc-001",
                "title": "Kubernetes 部署指南",
                "content": """
                # Kubernetes 集群部署

                本文档介绍如何在生产环境部署 Kubernetes 集群。

                ## 系统要求
                - Ubuntu 22.04 或更高版本
                - 至少 3 个节点（1 master + 2 worker）
                - 每个节点至少 4GB 内存

                ## 安装步骤

                ### 1. 安装 Docker
                ```bash
                sudo apt-get update
                sudo apt-get install -y docker.io
                ```

                ### 2. 安装 kubeadm、kubelet 和 kubectl
                ```bash
                sudo apt-get install -y apt-transport-https curl
                curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
                sudo apt-add-repository "deb http://apt.kubernetes.io/ kubernetes-xenial main"
                sudo apt-get install -y kubelet kubeadm kubectl
                ```

                ### 3. 初始化 Master 节点
                ```bash
                sudo kubeadm init --pod-network-cidr=192.168.0.0/16
                ```

                ### 4. 安装网络插件（Calico）
                ```bash
                kubectl apply -f https://docs.projectcalico.org/manifests/calico.yaml
                ```

                ## 常见问题

                ### Q: Pod 无法启动
                A: 检查网络插件是否正确安装，使用 `kubectl get pods -n kube-system` 查看。

                ### Q: 节点状态为 NotReady
                A: 确保 kubelet 服务正在运行：`systemctl status kubelet`
                """,
                "metadata": {
                    "source_type": "document",
                    "category": "DevOps",
                    "tags": ["kubernetes", "deployment", "production"]
                }
            },
            {
                "id": "doc-002",
                "title": "FastAPI 开发最佳实践",
                "content": """
                # FastAPI 开发最佳实践

                ## 项目结构

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

                ## 依赖注入

                使用 FastAPI 的依赖注入系统管理共享资源：

                ```python
                from fastapi import Depends

                def get_db():
                    db = Database()
                    try:
                        yield db
                    finally:
                        db.close()

                @app.get("/items")
                async def read_items(db = Depends(get_db)):
                    return db.query("SELECT * FROM items")
                ```

                ## 异步处理

                充分利用 async/await 提升性能：

                ```python
                @app.get("/users/{user_id}")
                async def get_user(user_id: int):
                    user = await fetch_user_from_db(user_id)
                    return user
                ```

                ## 数据验证

                使用 Pydantic 模型进行数据验证：

                ```python
                from pydantic import BaseModel, EmailStr

                class User(BaseModel):
                    name: str
                    email: EmailStr
                    age: int
                ```

                ## 错误处理

                使用 HTTPException 返回标准错误：

                ```python
                from fastapi import HTTPException

                @app.get("/items/{item_id}")
                async def read_item(item_id: int):
                    if item_id not in items:
                        raise HTTPException(status_code=404, detail="Item not found")
                    return items[item_id]
                ```
                """,
                "metadata": {
                    "source_type": "document",
                    "category": "Backend",
                    "tags": ["python", "fastapi", "best-practices"]
                }
            },
            {
                "id": "doc-003",
                "title": "PostgreSQL 性能优化",
                "content": """
                # PostgreSQL 性能优化指南

                ## 连接池配置

                合理配置连接池以提升性能：

                ### SQLAlchemy 配置
                ```python
                from sqlalchemy import create_engine

                engine = create_engine(
                    "postgresql://user:pass@localhost/dbname",
                    pool_size=20,           # 连接池大小
                    max_overflow=40,        # 最大溢出连接
                    pool_timeout=30,        # 连接超时
                    pool_recycle=3600,      # 连接回收时间
                    pool_pre_ping=True      # 连接前检查
                )
                ```

                ## 索引优化

                ### 创建索引
                ```sql
                -- B-tree 索引（默认）
                CREATE INDEX idx_users_email ON users(email);

                -- 复合索引
                CREATE INDEX idx_orders_user_date ON orders(user_id, created_at);

                -- 部分索引
                CREATE INDEX idx_active_users ON users(email) WHERE is_active = true;
                ```

                ### 查看索引使用情况
                ```sql
                SELECT
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan,
                    idx_tup_read
                FROM pg_stat_user_indexes
                ORDER BY idx_scan DESC;
                ```

                ## 查询优化

                ### 使用 EXPLAIN ANALYZE
                ```sql
                EXPLAIN ANALYZE
                SELECT * FROM users WHERE email = 'test@example.com';
                ```

                ### 避免 SELECT *
                ```sql
                -- 不好的写法
                SELECT * FROM users WHERE id = 1;

                -- 好的写法
                SELECT id, name, email FROM users WHERE id = 1;
                ```

                ## 连接池监控

                使用 pg_stat_activity 监控连接：
                ```sql
                SELECT
                    count(*) as total_connections,
                    state,
                    wait_event_type
                FROM pg_stat_activity
                GROUP BY state, wait_event_type;
                ```
                """,
                "metadata": {
                    "source_type": "document",
                    "category": "Database",
                    "tags": ["postgresql", "performance", "optimization"]
                }
            }
        ]

    async def test_01_chunk_and_index(self):
        """测试 1: 文档分块和索引"""
        logger.info("=" * 60)
        logger.info("测试 1: 文档分块和索引")
        logger.info("=" * 60)

        documents = self._get_test_documents()
        logger.info(f"Created {len(documents)} test documents")

        # 创建 Collection
        collection = self.chroma_client.get_or_create_collection(
            collection_name=self.test_collection_name
        )

        # 获取 Embedding 模型
        embedding = self.llm_manager.create_embedding()

        total_chunks = 0
        for doc in documents:
            # 文档分块
            chunks = self.chunker.chunk_text(
                text=doc["content"],
                parent_id=doc["id"]
            )

            logger.info(f"  {doc['title']}: {len(chunks)} chunks")
            total_chunks += len(chunks)

            # 生成 Embeddings
            texts = [chunk.content for chunk in chunks]  # 使用 content 而不是 text
            embeddings_response = await embedding.embed(texts)
            embeddings = embeddings_response.embeddings

            # 准备数据
            ids = [chunk.chunk_id for chunk in chunks]
            metadatas = [
                {
                    **doc["metadata"],
                    "parent_id": chunk.parent_id,
                    "chunk_index": chunk.chunk_index,
                    "title": doc["title"]
                }
                for chunk in chunks
            ]

            # 添加到 ChromaDB
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas
            )

        logger.info(f"✅ 索引完成: {len(documents)} 文档, {total_chunks} chunks")

    async def test_02_semantic_retrieval(self):
        """测试 2: 语义检索"""
        logger.info("=" * 60)
        logger.info("测试 2: 语义检索")
        logger.info("=" * 60)

        # 先索引
        await self.test_01_chunk_and_index()

        # 测试查询
        test_queries = [
            ("如何部署 Kubernetes 集群？", "doc-001"),
            ("FastAPI 的项目结构是什么？", "doc-002"),
            ("怎么优化数据库连接池？", "doc-003"),
            ("Python 异步编程", "doc-002"),
            ("SQL 索引优化", "doc-003"),
        ]

        for query, expected_doc_id in test_queries:
            logger.info(f"\n查询: {query}")

            results = await self.retriever.retrieve(
                query=query,
                collection_name=self.test_collection_name,
                top_k=3
            )

            assert len(results) > 0, f"查询 '{query}' 应返回结果"

            # 打印结果
            for i, result in enumerate(results, 1):
                source = result.source
                logger.info(
                    f"  [{i}] {source.title} (score: {result.score:.3f})"
                )

            # 验证最相关的结果
            top_result = results[0]
            parent_id = top_result.metadata.get("parent_id")

            assert parent_id == expected_doc_id, (
                f"查询 '{query}' 应该返回 {expected_doc_id}, "
                f"实际返回 {parent_id}"
            )

            logger.info(f"✅ 查询验证通过")

    async def test_03_code_search(self):
        """测试 3: 代码块搜索"""
        logger.info("=" * 60)
        logger.info("测试 3: 代码块搜索")
        logger.info("=" * 60)

        # 先索引
        await self.test_01_chunk_and_index()

        # 搜索代码相关的查询
        code_queries = [
            "kubeadm init 命令",
            "FastAPI 依赖注入示例",
            "创建 PostgreSQL 索引的 SQL",
        ]

        for query in code_queries:
            logger.info(f"\n查询: {query}")

            results = await self.retriever.retrieve(
                query=query,
                collection_name=self.test_collection_name,
                top_k=2
            )

            assert len(results) > 0, f"查询 '{query}' 应返回结果"

            # 验证返回的内容包含代码块
            top_content = results[0].content
            has_code = "```" in top_content or "sudo" in top_content or "SELECT" in top_content

            logger.info(f"  Top 1: {results[0].source.title}")
            logger.info(f"  包含代码: {'✓' if has_code else '✗'}")

            assert has_code, "结果应该包含代码块"

            logger.info(f"✅ 代码搜索验证通过")


async def run_simple_tests():
    """运行简化测试"""
    logger.info("=" * 80)
    logger.info("开始 RAG 简化端到端测试")
    logger.info("=" * 80)

    test_suite = TestSimpleRAGFlow()
    await test_suite.setup()

    try:
        await test_suite.test_01_chunk_and_index()
        await test_suite.test_02_semantic_retrieval()
        await test_suite.test_03_code_search()

        logger.info("\n" + "=" * 80)
        logger.info("✅ 所有 RAG 简化测试通过!")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"\n❌ 测试失败: {e}", exc_info=True)
        raise
    finally:
        await test_suite.teardown()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    asyncio.run(run_simple_tests())
