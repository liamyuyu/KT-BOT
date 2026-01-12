"""
Document Indexer
文档索引器：将 Jira Issues 索引到向量数据库
"""

import asyncio
import time
import logging
from typing import List, Dict, Any, Optional

from src.integrations.jira.client import JiraClient, get_jira_client
from src.integrations.jira.models import JiraIssue, JiraComment
from src.core.vectordb.chroma_client import ChromaDBClient, get_chroma_client
from src.core.vectordb.models import Document
from src.core.llm.manager import get_llm_manager, LLMManager
from src.core.llm.base import BaseEmbedding

from .chunker import TextChunker
from .models import Chunk, ChunkingConfig, IndexResult
from .exceptions import IndexingError, DocumentProcessingError, EmbeddingError

logger = logging.getLogger(__name__)


class DocumentIndexer:
    """
    文档索引器
    负责从 Jira 获取 Issues，分块，生成 embeddings，并索引到向量数据库
    """

    def __init__(
        self,
        jira_client: Optional[JiraClient] = None,
        chroma_client: Optional[ChromaDBClient] = None,
        llm_manager: Optional[LLMManager] = None,
        chunking_config: Optional[ChunkingConfig] = None,
        collection_name: str = "jira_knowledge",
        batch_size: int = 50
    ):
        """
        初始化文档索引器

        Args:
            jira_client: Jira 客户端（默认使用全局实例）
            chroma_client: ChromaDB 客户端（默认使用全局实例）
            llm_manager: LLM 管理器（默认使用全局实例）
            chunking_config: 分块配置（默认使用默认配置）
            collection_name: ChromaDB Collection 名称
            batch_size: 批量处理大小（每次处理的 Issue 数量）
        """
        self.jira_client = jira_client or get_jira_client()
        self.chroma_client = chroma_client or get_chroma_client()
        self.llm_manager = llm_manager or get_llm_manager()
        self.collection_name = collection_name
        self.batch_size = batch_size

        # 初始化 Chunker
        self.chunker = TextChunker(config=chunking_config)

        # 初始化 Embedding 模型
        self.embedding_model: Optional[BaseEmbedding] = None

        logger.info(
            f"DocumentIndexer initialized: collection={collection_name}, "
            f"batch_size={batch_size}"
        )

    def _get_embedding_model(self) -> BaseEmbedding:
        """获取或创建 Embedding 模型实例（懒加载）"""
        if self.embedding_model is None:
            self.embedding_model = self.llm_manager.create_embedding()
            logger.info(f"Embedding model created: {self.embedding_model.model_name}")
        return self.embedding_model

    async def index_issues(
        self,
        project_key: str,
        max_issues: Optional[int] = None,
        jql: Optional[str] = None
    ) -> IndexResult:
        """
        索引 Jira Issues

        Args:
            project_key: Jira 项目 KEY
            max_issues: 最多索引的 Issue 数量（None 表示全部）
            jql: 自定义 JQL 查询（可选）

        Returns:
            IndexResult: 索引结果

        Raises:
            IndexingError: 索引失败时抛出
        """
        start_time = time.time()
        logger.info(f"Starting indexing for project: {project_key}")

        try:
            # 1. 获取 Issues
            issues = await self._fetch_issues(project_key, max_issues, jql)
            if not issues:
                logger.warning(f"No issues found for project: {project_key}")
                return IndexResult(
                    total_documents=0,
                    total_chunks=0,
                    success_count=0,
                    failed_count=0,
                    duration_seconds=time.time() - start_time
                )

            logger.info(f"Fetched {len(issues)} issues")

            # 2. 处理 Issues 并生成 Chunks
            all_chunks: List[Chunk] = []
            errors: List[str] = []

            for issue in issues:
                try:
                    chunks = await self._process_issue(issue)
                    all_chunks.extend(chunks)
                except Exception as e:
                    error_msg = f"Failed to process issue {issue.key}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            logger.info(f"Generated {len(all_chunks)} chunks from {len(issues)} issues")

            # 3. 生成 Embeddings
            try:
                await self._generate_embeddings(all_chunks)
            except Exception as e:
                raise EmbeddingError(f"Failed to generate embeddings: {e}")

            # 4. 存储到 ChromaDB
            success_count = 0
            failed_count = 0

            try:
                # 转换 Chunk 为 Document
                documents = [self._chunk_to_document(chunk) for chunk in all_chunks]

                # 批量插入
                result = self.chroma_client.add_documents(
                    documents=documents,
                    collection_name=self.collection_name,
                    batch_size=100
                )

                success_count = result.inserted_count
                failed_count = result.failed_count

                if result.failed_ids:
                    errors.extend([f"Failed to insert: {fid}" for fid in result.failed_ids])

            except Exception as e:
                raise IndexingError(f"Failed to store documents: {e}")

            duration = time.time() - start_time

            logger.info(
                f"Indexing completed: {len(issues)} issues -> {len(all_chunks)} chunks, "
                f"{success_count} succeeded, {failed_count} failed, "
                f"duration: {duration:.2f}s"
            )

            return IndexResult(
                total_documents=len(issues),
                total_chunks=len(all_chunks),
                success_count=success_count,
                failed_count=failed_count,
                errors=errors,
                duration_seconds=duration
            )

        except Exception as e:
            raise IndexingError(f"Indexing failed for project {project_key}: {e}")

    async def _fetch_issues(
        self,
        project_key: str,
        max_issues: Optional[int],
        jql: Optional[str]
    ) -> List[JiraIssue]:
        """
        从 Jira 获取 Issues

        Args:
            project_key: 项目 KEY
            max_issues: 最多获取的数量
            jql: 自定义 JQL

        Returns:
            JiraIssue 列表
        """
        issues: List[JiraIssue] = []
        start_at = 0
        page_size = min(self.batch_size, 100)  # Jira API 单次最多 100

        while True:
            try:
                page = await self.jira_client.fetch_issues(
                    project_key=project_key,
                    jql=jql,
                    start_at=start_at,
                    max_results=page_size
                )

                issues.extend(page.issues)

                # 检查是否需要继续
                if page.is_last or (max_issues and len(issues) >= max_issues):
                    break

                start_at += page_size

            except Exception as e:
                logger.error(f"Failed to fetch issues at start_at={start_at}: {e}")
                break

        # 限制数量
        if max_issues:
            issues = issues[:max_issues]

        return issues

    async def _process_issue(self, issue: JiraIssue) -> List[Chunk]:
        """
        处理单个 Issue：组装内容并分块

        Args:
            issue: Jira Issue

        Returns:
            Chunk 列表

        Raises:
            DocumentProcessingError: 处理失败时抛出
        """
        try:
            # 组装 Issue 内容
            content = self._assemble_issue_content(issue)

            # 准备元数据
            metadata = self._extract_issue_metadata(issue)

            # 分块
            chunks = self.chunker.chunk_text(
                text=content,
                parent_id=issue.key,
                metadata=metadata
            )

            logger.debug(f"Processed issue {issue.key}: {len(chunks)} chunks")

            return chunks

        except Exception as e:
            raise DocumentProcessingError(
                f"Failed to process issue {issue.key}: {e}",
                document_id=issue.key
            )

    def _assemble_issue_content(self, issue: JiraIssue) -> str:
        """
        组装 Issue 内容：标题 + 描述 + 评论

        Args:
            issue: Jira Issue

        Returns:
            组装后的文本内容
        """
        parts = []

        # 标题
        parts.append(f"# {issue.summary}")

        # 描述
        if issue.description:
            parts.append(f"\n## 描述\n{issue.description}")

        # 评论
        if issue.comments:
            parts.append("\n## 评论")
            for idx, comment in enumerate(issue.comments, 1):
                author_name = comment.author.display_name if comment.author else "Unknown"
                parts.append(
                    f"\n### 评论 {idx} - {author_name}\n{comment.body}"
                )

        return "\n".join(parts)

    def _extract_issue_metadata(self, issue: JiraIssue) -> Dict[str, Any]:
        """
        提取 Issue 元数据

        Args:
            issue: Jira Issue

        Returns:
            元数据字典
        """
        return {
            "source_type": "jira",
            "issue_key": issue.key,
            "issue_id": issue.id,
            "project_key": issue.project.key,
            "project_name": issue.project.name,
            "issue_type": issue.issue_type.name,
            "status": issue.status.name,
            "priority": issue.priority.name if issue.priority else None,
            "reporter": issue.reporter.display_name if issue.reporter else None,
            "assignee": issue.assignee.display_name if issue.assignee else None,
            "created_at": issue.created.isoformat(),
            "updated_at": issue.updated.isoformat(),
            "labels": issue.labels,
            "components": issue.components,
            "url": issue.url
        }

    async def _generate_embeddings(self, chunks: List[Chunk]) -> None:
        """
        为所有 Chunks 生成 Embeddings

        Args:
            chunks: Chunk 列表（会被原地修改，添加 embedding 字段）

        Raises:
            EmbeddingError: Embedding 生成失败时抛出
        """
        if not chunks:
            return

        logger.info(f"Generating embeddings for {len(chunks)} chunks...")

        try:
            embedding_model = self._get_embedding_model()

            # 提取文本
            texts = [chunk.content for chunk in chunks]

            # 批量生成 embeddings
            responses = await embedding_model.embed_batch(texts)

            # 设置 embedding
            for chunk, response in zip(chunks, responses):
                chunk.embedding = response.embedding

            logger.info(f"Successfully generated {len(chunks)} embeddings")

        except Exception as e:
            raise EmbeddingError(f"Failed to generate embeddings: {e}")

    def _chunk_to_document(self, chunk: Chunk) -> Document:
        """
        将 Chunk 转换为 Document（用于存储到 ChromaDB）

        Args:
            chunk: Chunk 对象

        Returns:
            Document 对象
        """
        # 添加 chunk 特定的元数据
        metadata = chunk.metadata.copy()
        metadata.update({
            "parent_id": chunk.parent_id,
            "chunk_index": chunk.chunk_index,
            "start_index": chunk.start_index,
            "end_index": chunk.end_index
        })

        return Document(
            id=chunk.chunk_id,
            content=chunk.content,
            embedding=chunk.embedding,
            metadata=metadata
        )

    async def clear_collection(self) -> bool:
        """
        清空 Collection（删除所有文档）

        Returns:
            bool: 是否成功
        """
        try:
            self.chroma_client.delete_collection(self.collection_name)
            logger.info(f"Collection {self.collection_name} cleared")
            return True
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
            return False


# 全局单例
_indexer: Optional[DocumentIndexer] = None


def get_document_indexer() -> DocumentIndexer:
    """
    获取全局文档索引器实例

    Returns:
        DocumentIndexer: 索引器实例
    """
    global _indexer
    if _indexer is None:
        _indexer = DocumentIndexer()
    return _indexer
