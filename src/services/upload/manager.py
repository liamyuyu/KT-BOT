"""
Upload Manager
上传管理器 - 处理批量文件上传、进度跟踪和异步处理
"""

import os
import asyncio
import logging
import tempfile
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, AsyncGenerator
from fastapi import UploadFile

from .models import (
    UploadTask, UploadStatus, UploadProgress,
    BatchUploadResponse, FileInfo
)
from .exceptions import (
    ValidationError, ParsingError, IndexingError,
    TaskNotFoundException, TaskCancelledException
)
from src.document_processing.validator import DocumentValidator
from src.document_processing.parser.factory import get_parser_factory
from src.api.services.document_service import get_document_service
from src.api.schemas.document import DocumentUploadRequest

logger = logging.getLogger(__name__)


class UploadManager:
    """
    上传管理器

    功能:
    - 批量文件上传
    - 异步处理任务
    - 并发控制
    - 进度跟踪（SSE）
    - 可选数据库持久化
    """

    def __init__(
        self,
        max_concurrent: int = 3,
        max_file_size: int = 50 * 1024 * 1024,
        use_db: bool = False
    ):
        """
        初始化上传管理器

        Args:
            max_concurrent: 最大并发上传数
            max_file_size: 最大文件大小（字节）
            use_db: 是否使用数据库持久化
        """
        self.max_concurrent = max_concurrent
        self.max_file_size = max_file_size
        self.use_db = use_db

        # 任务存储
        self.tasks: Dict[str, UploadTask] = {}

        # 并发控制
        self.semaphore = asyncio.Semaphore(max_concurrent)

        # 进度队列（用于 SSE）
        self.progress_queues: Dict[str, asyncio.Queue] = {}

        # 取消标记
        self.cancelled_tasks: set = set()

        # 服务依赖
        self.validator = DocumentValidator(max_file_size=max_file_size)
        self.parser_factory = get_parser_factory()
        self.document_service = get_document_service()

        logger.info(
            f"UploadManager initialized (max_concurrent={max_concurrent}, "
            f"max_file_size={max_file_size/1024/1024:.0f}MB, use_db={use_db})"
        )

    async def submit_batch(
        self,
        files: List[UploadFile],
        user_id: str,
        tags: Optional[List[str]] = None
    ) -> BatchUploadResponse:
        """
        提交批量上传任务

        Args:
            files: 上传文件列表
            user_id: 用户 ID
            tags: 文档标签

        Returns:
            BatchUploadResponse: 批量上传响应

        Raises:
            ValueError: 文件数量超限
        """
        if len(files) > 10:
            raise ValueError(f"批量上传最多支持 10 个文件，当前: {len(files)}")

        batch_id = str(uuid.uuid4())
        logger.info(f"Submitting batch upload: {batch_id} ({len(files)} files)")

        accepted_task_ids = []
        rejected_files = []
        tags = tags or []

        # 验证所有文件
        for file in files:
            try:
                # 验证文件
                validation_result = await self.validator.validate(file)

                if not validation_result.is_valid:
                    rejected_files.append({
                        "file_name": validation_result.file_name,
                        "reason": validation_result.error_message or "验证失败"
                    })
                    logger.warning(
                        f"File rejected: {validation_result.file_name} - "
                        f"{validation_result.error_message}"
                    )
                    continue

                # 创建任务
                task_id = str(uuid.uuid4())

                file_info = FileInfo(
                    file_name=validation_result.file_name,
                    file_size=validation_result.file_size,
                    file_type=Path(validation_result.file_name).suffix.lower(),
                    mime_type=validation_result.mime_type
                )

                task = UploadTask(
                    task_id=task_id,
                    batch_id=batch_id,
                    user_id=user_id,
                    file_info=file_info,
                    status=UploadStatus.PENDING,
                    progress_percentage=0.0
                )

                self.tasks[task_id] = task
                accepted_task_ids.append(task_id)

                # 异步处理任务（不等待）
                asyncio.create_task(
                    self._process_with_semaphore(task_id, file, tags)
                )

            except Exception as e:
                logger.error(f"Error validating file {file.filename}: {e}")
                rejected_files.append({
                    "file_name": file.filename or "unknown",
                    "reason": str(e)
                })

        logger.info(
            f"Batch {batch_id}: accepted={len(accepted_task_ids)}, "
            f"rejected={len(rejected_files)}"
        )

        return BatchUploadResponse(
            batch_id=batch_id,
            total_files=len(files),
            accepted_files=len(accepted_task_ids),
            rejected_files=rejected_files,
            task_ids=accepted_task_ids
        )

    async def _process_with_semaphore(
        self,
        task_id: str,
        file: UploadFile,
        tags: List[str]
    ):
        """
        使用 Semaphore 控制并发

        Args:
            task_id: 任务 ID
            file: 上传文件
            tags: 文档标签
        """
        async with self.semaphore:
            try:
                await self._process_upload(task_id, file, tags)
            except Exception as e:
                logger.error(f"Task {task_id} failed: {e}", exc_info=True)

    async def _process_upload(
        self,
        task_id: str,
        file: UploadFile,
        tags: List[str]
    ):
        """
        处理单个文件上传

        Args:
            task_id: 任务 ID
            file: 上传文件
            tags: 文档标签
        """
        task = self.tasks.get(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return

        temp_path = None

        try:
            # 检查是否被取消
            if task_id in self.cancelled_tasks:
                await self._update_task_status(
                    task_id,
                    UploadStatus.CANCELLED,
                    0.0,
                    "任务已取消"
                )
                return

            # 1. 验证阶段
            await self._update_task_status(
                task_id,
                UploadStatus.VALIDATING,
                5.0,
                "验证文件..."
            )

            # 重置文件指针
            await file.seek(0)
            content = await file.read()

            # 2. 保存临时文件
            await self._update_task_status(
                task_id,
                UploadStatus.VALIDATING,
                15.0,
                "保存临时文件..."
            )

            file_ext = Path(task.file_info.file_name).suffix.lower()
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=file_ext,
                mode='wb'
            ) as tmp:
                tmp.write(content)
                temp_path = tmp.name

            # 检查取消
            if task_id in self.cancelled_tasks:
                raise TaskCancelledException("任务已取消", task_id)

            # 3. 解析阶段
            await self._update_task_status(
                task_id,
                UploadStatus.PARSING,
                30.0,
                f"解析 {file_ext} 文件..."
            )

            parsed_doc = await self.parser_factory.parse_file(temp_path)

            await self._update_task_status(
                task_id,
                UploadStatus.PARSING,
                60.0,
                "解析完成"
            )

            # 检查取消
            if task_id in self.cancelled_tasks:
                raise TaskCancelledException("任务已取消", task_id)

            # 4. 索引阶段
            await self._update_task_status(
                task_id,
                UploadStatus.INDEXING,
                70.0,
                "索引文档到向量数据库..."
            )

            # 准备上传请求
            upload_request = DocumentUploadRequest(
                title=parsed_doc.title,
                content=parsed_doc.content,
                source_type="uploaded_file",
                source_id=f"upload_{task.batch_id}_{task_id[:8]}",
                tags=tags,
                metadata={
                    **parsed_doc.metadata,
                    "file_type": parsed_doc.file_type,
                    "word_count": parsed_doc.word_count,
                    "original_filename": task.file_info.file_name,
                    "upload_batch_id": task.batch_id,
                    "upload_task_id": task_id,
                    "uploaded_by": task.user_id
                }
            )

            # 上传到文档服务
            upload_response = await self.document_service.upload_document(
                upload_request
            )

            # 5. 完成
            task.document_id = upload_response.document_id
            task.completed_at = datetime.now()

            await self._update_task_status(
                task_id,
                UploadStatus.COMPLETED,
                100.0,
                f"上传完成 - 文档 ID: {upload_response.document_id}"
            )

            logger.info(
                f"Task {task_id} completed successfully: "
                f"document_id={upload_response.document_id}"
            )

        except TaskCancelledException as e:
            logger.info(f"Task {task_id} cancelled")
            await self._update_task_status(
                task_id,
                UploadStatus.CANCELLED,
                task.progress_percentage,
                "任务已取消"
            )

        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}", exc_info=True)

            # 确定错误类型
            if "parse" in str(e).lower() or "parser" in str(e).lower():
                error_type = "解析错误"
            elif "index" in str(e).lower() or "vectordb" in str(e).lower():
                error_type = "索引错误"
            else:
                error_type = "处理错误"

            await self._update_task_status(
                task_id,
                UploadStatus.FAILED,
                task.progress_percentage,
                f"{error_type}: {str(e)}"
            )

        finally:
            # 清理临时文件
            if temp_path and os.path.exists(temp_path):
                try:
                    Path(temp_path).unlink()
                    logger.debug(f"Cleaned up temp file: {temp_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temp file: {e}")

            # 清理取消标记
            self.cancelled_tasks.discard(task_id)

    async def _update_task_status(
        self,
        task_id: str,
        status: UploadStatus,
        progress: float,
        message: str
    ):
        """
        更新任务状态并发送进度

        Args:
            task_id: 任务 ID
            status: 新状态
            progress: 进度百分比
            message: 进度消息
        """
        task = self.tasks.get(task_id)
        if not task:
            return

        # 更新任务
        task.status = status
        task.progress_percentage = progress
        task.updated_at = datetime.now()

        if status == UploadStatus.FAILED:
            task.error_message = message

        # 发送进度更新
        progress_update = UploadProgress(
            task_id=task_id,
            status=status,
            progress=progress,
            message=message,
            current_step=status.value
        )

        await self._emit_progress(task_id, progress_update)

        # 如果启用数据库，持久化状态
        if self.use_db:
            await self._save_task_to_db(task_id)

    async def _emit_progress(
        self,
        task_id: str,
        progress: UploadProgress
    ):
        """
        发送进度更新到 SSE 队列

        Args:
            task_id: 任务 ID
            progress: 进度信息
        """
        if task_id in self.progress_queues:
            try:
                await self.progress_queues[task_id].put(progress)
            except Exception as e:
                logger.error(f"Failed to emit progress for task {task_id}: {e}")

    async def _save_task_to_db(self, task_id: str):
        """
        持久化任务到数据库（占位符）

        Args:
            task_id: 任务 ID
        """
        # TODO: 实现数据库持久化
        pass

    async def get_progress_stream(
        self,
        task_id: str
    ) -> AsyncGenerator[UploadProgress, None]:
        """
        获取任务进度流（SSE）

        Args:
            task_id: 任务 ID

        Yields:
            UploadProgress: 进度更新

        Raises:
            TaskNotFoundException: 任务不存在
        """
        if task_id not in self.tasks:
            raise TaskNotFoundException(f"任务 {task_id} 不存在", task_id)

        # 创建进度队列
        queue = asyncio.Queue()
        self.progress_queues[task_id] = queue

        try:
            # 发送当前状态
            task = self.tasks[task_id]
            current_progress = UploadProgress(
                task_id=task_id,
                status=task.status,
                progress=task.progress_percentage,
                message=task.error_message or f"当前状态: {task.status.value}",
                current_step=task.status.value
            )
            yield current_progress

            # 监听更新
            while True:
                try:
                    progress = await asyncio.wait_for(queue.get(), timeout=300)
                    yield progress

                    # 终止条件
                    if progress.status in [
                        UploadStatus.COMPLETED,
                        UploadStatus.FAILED,
                        UploadStatus.CANCELLED
                    ]:
                        break

                except asyncio.TimeoutError:
                    # 超时，发送心跳
                    logger.debug(f"Progress stream timeout for task {task_id}")
                    break

        finally:
            # 清理队列
            if task_id in self.progress_queues:
                del self.progress_queues[task_id]

    async def cancel_task(self, task_id: str) -> bool:
        """
        取消上传任务

        Args:
            task_id: 任务 ID

        Returns:
            bool: 是否成功取消

        Raises:
            TaskNotFoundException: 任务不存在
        """
        task = self.tasks.get(task_id)
        if not task:
            raise TaskNotFoundException(f"任务 {task_id} 不存在", task_id)

        # 已完成的任务无法取消
        if task.status in [UploadStatus.COMPLETED, UploadStatus.FAILED]:
            logger.warning(f"Cannot cancel task {task_id} in status {task.status}")
            return False

        # 标记为取消
        self.cancelled_tasks.add(task_id)
        logger.info(f"Task {task_id} marked for cancellation")

        return True

    async def get_task_status(
        self,
        task_id: str
    ) -> Optional[UploadTask]:
        """
        获取任务状态

        Args:
            task_id: 任务 ID

        Returns:
            UploadTask: 任务信息，不存在则返回 None
        """
        return self.tasks.get(task_id)

    async def list_tasks(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[UploadTask]:
        """
        列出用户的上传任务

        Args:
            user_id: 用户 ID
            status: 状态筛选（可选）
            limit: 返回数量限制

        Returns:
            List[UploadTask]: 任务列表
        """
        tasks = []

        for task in self.tasks.values():
            # 筛选用户
            if task.user_id != user_id:
                continue

            # 筛选状态
            if status and task.status.value != status:
                continue

            tasks.append(task)

        # 按创建时间倒序排序
        tasks.sort(key=lambda t: t.created_at, reverse=True)

        # 应用限制
        return tasks[:limit]
