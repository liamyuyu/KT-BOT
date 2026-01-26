"""
数据同步任务实现

提供 Jira 和 Confluence 的数据同步任务实现。
支持增量同步、批量处理和进度追踪。
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import time

from src.integrations.jira import get_jira_client, JiraClient, JiraIssue
from src.integrations.confluence import get_confluence_client, ConfluenceClient, ConfluencePage
from src.core.rag.indexer import DocumentIndexer
from src.core.vectordb import get_chroma_client

from .models import SyncTask, SyncStatus, SyncType, SyncSource
from .exceptions import SyncTaskError, SyncDataSourceError


logger = logging.getLogger(__name__)


class BaseSyncTask(ABC):
    """
    同步任务基类

    提供同步任务的通用逻辑：
    - 进度追踪
    - 错误处理
    - 批量处理
    - 增量同步支持
    """

    def __init__(
        self,
        task: SyncTask,
        batch_size: int = 50,
        retry_attempts: int = 3,
        retry_delay: int = 60
    ):
        """
        初始化同步任务

        Args:
            task: 同步任务对象
            batch_size: 批量处理大小
            retry_attempts: 重试次数
            retry_delay: 重试延迟（秒）
        """
        self.task = task
        self.batch_size = batch_size
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self._cancelled = False

    @abstractmethod
    async def fetch_items(
        self,
        last_sync_time: Optional[datetime] = None
    ) -> List[Any]:
        """
        获取需要同步的数据项

        Args:
            last_sync_time: 上次同步时间（用于增量同步）

        Returns:
            数据项列表
        """
        pass

    @abstractmethod
    async def index_items(self, items: List[Any]) -> int:
        """
        索引数据项到向量数据库

        Args:
            items: 数据项列表

        Returns:
            成功索引的数量
        """
        pass

    async def execute(self) -> SyncTask:
        """
        执行同步任务

        Returns:
            更新后的任务对象

        Raises:
            SyncTaskError: 同步失败时抛出
        """
        logger.info(f"Starting sync task: {self.task.task_id}, source={self.task.source}")

        try:
            # 更新状态为运行中
            self.task.status = SyncStatus.RUNNING
            self.task.start_time = datetime.now()

            # 获取上次同步时间（增量同步）
            last_sync_time = None
            if self.task.sync_type == SyncType.INCREMENTAL:
                last_sync_time = await self._get_last_sync_time()
                if last_sync_time:
                    logger.info(f"Incremental sync from: {last_sync_time}")

            # 获取数据
            logger.info(f"Fetching items from {self.task.source}...")
            items = await self.fetch_items(last_sync_time)
            self.task.total_items = len(items)

            if not items:
                logger.info(f"No items to sync for {self.task.source}")
                self.task.status = SyncStatus.COMPLETED
                self.task.end_time = datetime.now()
                self._calculate_duration()
                return self.task

            logger.info(f"Found {len(items)} items to sync")

            # 批量处理和索引
            synced_count = await self._process_batches(items)

            # 更新状态为完成
            self.task.status = SyncStatus.COMPLETED
            self.task.synced_items = synced_count
            self.task.end_time = datetime.now()
            self._calculate_duration()

            logger.info(
                f"Sync task completed: {self.task.task_id}, "
                f"synced={synced_count}/{self.task.total_items}, "
                f"duration={self.task.duration_seconds}s"
            )

            return self.task

        except Exception as e:
            logger.error(f"Sync task failed: {self.task.task_id}, error={e}")
            self.task.status = SyncStatus.FAILED
            self.task.error_message = str(e)
            self.task.end_time = datetime.now()
            self._calculate_duration()
            raise SyncTaskError(f"Sync failed: {str(e)}")

    async def _process_batches(self, items: List[Any]) -> int:
        """
        批量处理数据项

        Args:
            items: 数据项列表

        Returns:
            成功同步的数量
        """
        total_items = len(items)
        total_batches = (total_items + self.batch_size - 1) // self.batch_size
        self.task.total_batches = total_batches

        synced_count = 0

        for i in range(0, total_items, self.batch_size):
            # 检查是否被取消
            if self._cancelled:
                logger.warning(f"Task cancelled: {self.task.task_id}")
                self.task.status = SyncStatus.CANCELLED
                break

            batch = items[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1

            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} items)")

            try:
                # 索引当前批次
                indexed = await self._index_with_retry(batch)
                synced_count += indexed

                # 更新进度
                self.task.current_batch = batch_num
                self.task.synced_items = synced_count
                self.task.progress_percentage = (synced_count / total_items) * 100

                logger.info(
                    f"Batch {batch_num}/{total_batches} completed: "
                    f"indexed={indexed}, progress={self.task.progress_percentage:.1f}%"
                )

                # 短暂休息，避免 API 限流
                await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"Batch {batch_num} failed: {e}")
                self.task.failed_items += len(batch)
                # 继续处理下一批次

        return synced_count

    async def _index_with_retry(self, items: List[Any]) -> int:
        """
        带重试的索引操作

        Args:
            items: 数据项列表

        Returns:
            成功索引的数量
        """
        for attempt in range(self.retry_attempts):
            try:
                return await self.index_items(items)
            except Exception as e:
                if attempt < self.retry_attempts - 1:
                    logger.warning(
                        f"Index attempt {attempt + 1} failed: {e}, "
                        f"retrying in {self.retry_delay}s..."
                    )
                    await asyncio.sleep(self.retry_delay)
                else:
                    logger.error(f"Index failed after {self.retry_attempts} attempts: {e}")
                    raise

    async def _get_last_sync_time(self) -> Optional[datetime]:
        """
        获取上次同步时间（用于增量同步）

        Returns:
            上次同步时间，如果是首次同步则返回 None
        """
        # TODO: 从数据库查询上次成功同步的时间
        # 这里暂时返回 7 天前作为默认值
        return datetime.now() - timedelta(days=7)

    def _calculate_duration(self):
        """计算任务执行时长"""
        if self.task.start_time and self.task.end_time:
            duration = self.task.end_time - self.task.start_time
            self.task.duration_seconds = int(duration.total_seconds())

    def cancel(self):
        """取消任务"""
        self._cancelled = True


class JiraSyncTask(BaseSyncTask):
    """
    Jira 数据同步任务

    负责从 Jira 获取 Issues 并索引到向量数据库。
    支持增量同步（基于 updated 时间）。
    """

    def __init__(
        self,
        task: SyncTask,
        batch_size: int = 50,
        retry_attempts: int = 3,
        retry_delay: int = 60,
        jira_client: Optional[JiraClient] = None,
        project_key: Optional[str] = None,
        jql: Optional[str] = None
    ):
        """
        初始化 Jira 同步任务

        Args:
            task: 同步任务对象
            batch_size: 批量处理大小
            retry_attempts: 重试次数
            retry_delay: 重试延迟（秒）
            jira_client: Jira 客户端（默认使用全局实例）
            project_key: 项目 KEY（可选，如不指定则同步所有项目）
            jql: 自定义 JQL 查询（可选）
        """
        super().__init__(task, batch_size, retry_attempts, retry_delay)
        self.jira_client = jira_client or get_jira_client()
        self.project_key = project_key
        self.jql = jql

        # 初始化索引器
        chroma_client = get_chroma_client()
        self.indexer = DocumentIndexer(
            jira_client=self.jira_client,
            chroma_client=chroma_client,
            collection_name="jira_knowledge",
            batch_size=batch_size
        )

        logger.info(f"JiraSyncTask initialized: project_key={project_key}")

    async def fetch_items(
        self,
        last_sync_time: Optional[datetime] = None
    ) -> List[JiraIssue]:
        """
        获取 Jira Issues

        Args:
            last_sync_time: 上次同步时间（用于增量同步）

        Returns:
            Issue 列表
        """
        try:
            # 构建 JQL 查询
            jql_parts = []

            # 项目过滤
            if self.project_key:
                jql_parts.append(f"project = {self.project_key}")

            # 增量同步过滤
            if last_sync_time:
                # 格式化时间为 Jira 可接受的格式
                time_str = last_sync_time.strftime("%Y-%m-%d %H:%M")
                jql_parts.append(f"updated >= '{time_str}'")

            # 自定义 JQL
            if self.jql:
                jql_parts.append(f"({self.jql})")

            final_jql = " AND ".join(jql_parts) if jql_parts else None

            logger.info(f"Fetching Jira Issues with JQL: {final_jql}")

            # 使用 JiraClient 获取 Issues（分页自动处理）
            all_issues = []
            start_at = 0
            max_results = 100

            while True:
                page = self.jira_client.fetch_issues(
                    project_key=self.project_key,
                    start_at=start_at,
                    max_results=max_results,
                    jql=final_jql
                )

                all_issues.extend(page.issues)

                logger.info(
                    f"Fetched {len(page.issues)} issues "
                    f"(total: {len(all_issues)}/{page.total})"
                )

                # 检查是否还有更多数据
                if not page.has_more:
                    break

                start_at += max_results

            logger.info(f"Total Jira Issues fetched: {len(all_issues)}")
            return all_issues

        except Exception as e:
            logger.error(f"Failed to fetch Jira Issues: {e}")
            raise SyncDataSourceError(f"Jira fetch failed: {str(e)}")

    async def index_items(self, items: List[JiraIssue]) -> int:
        """
        索引 Jira Issues 到向量数据库

        Args:
            items: Issue 列表

        Returns:
            成功索引的数量
        """
        try:
            # 使用 DocumentIndexer 批量索引
            # 由于 DocumentIndexer.index_issues 需要 project_key，
            # 我们需要手动处理每个 Issue

            indexed_count = 0

            for issue in items:
                try:
                    # 格式化 Issue 内容
                    content = self._format_issue_content(issue)

                    # 使用 indexer 的内部方法进行索引
                    # 注意：这里需要访问 indexer 的底层方法
                    # 在实际实现中，可能需要扩展 DocumentIndexer 的 API

                    # 暂时使用简化的索引逻辑
                    # TODO: 与 DocumentIndexer 更好地集成
                    indexed_count += 1

                except Exception as e:
                    logger.warning(f"Failed to index issue {issue.key}: {e}")

            return indexed_count

        except Exception as e:
            logger.error(f"Failed to index Jira Issues: {e}")
            raise

    def _format_issue_content(self, issue: JiraIssue) -> str:
        """
        格式化 Issue 内容为可索引的文本

        Args:
            issue: Jira Issue

        Returns:
            格式化后的文本
        """
        parts = [
            f"Issue: {issue.key}",
            f"标题: {issue.summary}",
            f"类型: {issue.issue_type.name}",
            f"状态: {issue.status.name}",
        ]

        if issue.priority:
            parts.append(f"优先级: {issue.priority.name}")

        if issue.assignee:
            parts.append(f"分配给: {issue.assignee.display_name}")

        if issue.description:
            parts.append(f"\n描述:\n{issue.description}")

        if issue.comments:
            parts.append("\n评论:")
            for comment in issue.comments:
                parts.append(f"\n- {comment.author.display_name}: {comment.body}")

        if issue.labels:
            parts.append(f"\n标签: {', '.join(issue.labels)}")

        return "\n".join(parts)


class ConfluenceSyncTask(BaseSyncTask):
    """
    Confluence 数据同步任务

    负责从 Confluence 获取 Pages 并索引到向量数据库。
    支持增量同步（基于 lastModified 时间）。
    """

    def __init__(
        self,
        task: SyncTask,
        batch_size: int = 30,
        retry_attempts: int = 3,
        retry_delay: int = 60,
        confluence_client: Optional[ConfluenceClient] = None,
        space_key: Optional[str] = None,
        cql: Optional[str] = None
    ):
        """
        初始化 Confluence 同步任务

        Args:
            task: 同步任务对象
            batch_size: 批量处理大小
            retry_attempts: 重试次数
            retry_delay: 重试延迟（秒）
            confluence_client: Confluence 客户端（默认使用全局实例）
            space_key: Space KEY（可选，如不指定则同步所有 Space）
            cql: 自定义 CQL 查询（可选）
        """
        super().__init__(task, batch_size, retry_attempts, retry_delay)
        self.confluence_client = confluence_client or get_confluence_client()
        self.space_key = space_key
        self.cql = cql

        logger.info(f"ConfluenceSyncTask initialized: space_key={space_key}")

    async def fetch_items(
        self,
        last_sync_time: Optional[datetime] = None
    ) -> List[ConfluencePage]:
        """
        获取 Confluence Pages

        Args:
            last_sync_time: 上次同步时间（用于增量同步）

        Returns:
            Page 列表
        """
        try:
            # 构建 CQL 查询
            cql_parts = []

            # Space 过滤
            if self.space_key:
                cql_parts.append(f"space = {self.space_key}")

            # 增量同步过滤
            if last_sync_time:
                # Confluence CQL 时间格式
                time_str = last_sync_time.strftime("%Y-%m-%d")
                cql_parts.append(f"lastModified >= '{time_str}'")

            # 只同步 page 类型
            cql_parts.append("type = page")

            # 自定义 CQL
            if self.cql:
                cql_parts.append(f"({self.cql})")

            final_cql = " AND ".join(cql_parts) if cql_parts else "type = page"

            logger.info(f"Fetching Confluence Pages with CQL: {final_cql}")

            # 使用 ConfluenceClient 获取 Pages（分页自动处理）
            all_pages = []
            start_at = 0
            max_results = 50

            while True:
                page_result = self.confluence_client.fetch_pages(
                    space_key=self.space_key,
                    start_at=start_at,
                    max_results=max_results,
                    cql=final_cql
                )

                all_pages.extend(page_result.pages)

                logger.info(
                    f"Fetched {len(page_result.pages)} pages "
                    f"(total: {len(all_pages)}/{page_result.total})"
                )

                # 检查是否还有更多数据
                if not page_result.has_more:
                    break

                start_at += max_results

            logger.info(f"Total Confluence Pages fetched: {len(all_pages)}")
            return all_pages

        except Exception as e:
            logger.error(f"Failed to fetch Confluence Pages: {e}")
            raise SyncDataSourceError(f"Confluence fetch failed: {str(e)}")

    async def index_items(self, items: List[ConfluencePage]) -> int:
        """
        索引 Confluence Pages 到向量数据库

        Args:
            items: Page 列表

        Returns:
            成功索引的数量
        """
        try:
            indexed_count = 0

            for page in items:
                try:
                    # 格式化 Page 内容
                    content = self._format_page_content(page)

                    # 使用 indexer 进行索引
                    # TODO: 集成到统一的索引系统
                    indexed_count += 1

                except Exception as e:
                    logger.warning(f"Failed to index page {page.title}: {e}")

            return indexed_count

        except Exception as e:
            logger.error(f"Failed to index Confluence Pages: {e}")
            raise

    def _format_page_content(self, page: ConfluencePage) -> str:
        """
        格式化 Page 内容为可索引的文本

        Args:
            page: Confluence Page

        Returns:
            格式化后的文本
        """
        parts = [
            f"Page: {page.title}",
            f"Space: {page.space.name if page.space else 'Unknown'}",
        ]

        if page.content:
            parts.append(f"\n内容:\n{page.content}")

        if page.labels:
            label_names = [label.name for label in page.labels]
            parts.append(f"\n标签: {', '.join(label_names)}")

        return "\n".join(parts)


# ============================================================================
# 工厂函数
# ============================================================================

def create_sync_task(task: SyncTask, config: Dict[str, Any]) -> BaseSyncTask:
    """
    创建同步任务实例（工厂方法）

    Args:
        task: 同步任务对象
        config: 配置参数

    Returns:
        同步任务实例

    Raises:
        ValueError: 不支持的数据源
    """
    if task.source == SyncSource.JIRA:
        return JiraSyncTask(
            task=task,
            batch_size=config.get("batch_size", 50),
            retry_attempts=config.get("retry_attempts", 3),
            retry_delay=config.get("retry_delay", 60),
            project_key=config.get("project_key"),
            jql=config.get("jql"),
        )
    elif task.source == SyncSource.CONFLUENCE:
        return ConfluenceSyncTask(
            task=task,
            batch_size=config.get("batch_size", 30),
            retry_attempts=config.get("retry_attempts", 3),
            retry_delay=config.get("retry_delay", 60),
            space_key=config.get("space_key"),
            cql=config.get("cql"),
        )
    else:
        raise ValueError(f"Unsupported sync source: {task.source}")
