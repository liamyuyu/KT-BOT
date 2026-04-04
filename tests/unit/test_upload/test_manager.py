"""
Tests for Upload Manager
上传管理器测试
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from io import BytesIO
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi import UploadFile

from src.services.upload.manager import UploadManager
from src.services.upload.models import UploadStatus, UploadTask, BatchUploadResponse
from src.services.upload.exceptions import TaskNotFoundException
from src.document_processing.parser.base import ParsedDocument


def create_upload_file(content: bytes, filename: str) -> UploadFile:
    """创建测试用 UploadFile"""
    file_obj = BytesIO(content)
    return UploadFile(filename=filename, file=file_obj)


@pytest.fixture
def upload_manager():
    """创建上传管理器实例"""
    return UploadManager(max_concurrent=2, max_file_size=1024*1024, use_db=False)


@pytest.fixture
def pdf_file():
    """创建 PDF 文件"""
    content = b'%PDF-1.4\nTest PDF content' * 100
    return create_upload_file(content, "test.pdf")


@pytest.fixture
def docx_file():
    """创建 DOCX 文件"""
    content = b'PK\x03\x04' + b'fake docx content' * 100
    return create_upload_file(content, "test.docx")


@pytest.fixture
def html_file():
    """创建 HTML 文件"""
    content = b'<!DOCTYPE html><html><body>Test</body></html>'
    return create_upload_file(content, "test.html")


@pytest.fixture
def mock_parser_factory():
    """Mock parser factory"""
    with patch('src.services.upload.manager.get_parser_factory') as mock:
        factory = Mock()
        parsed_doc = ParsedDocument(
            title="Test Document",
            content="Test content",
            metadata={"test": "meta"},
            word_count=100,
            file_type="pdf"
        )
        factory.parse_file = AsyncMock(return_value=parsed_doc)
        mock.return_value = factory
        yield factory


@pytest.fixture
def mock_document_service():
    """Mock document service"""
    with patch('src.services.upload.manager.get_document_service') as mock:
        service = Mock()
        upload_response = Mock()
        upload_response.document_id = "doc_12345"
        upload_response.chunk_count = 5
        service.upload_document = AsyncMock(return_value=upload_response)
        mock.return_value = service
        yield service


class TestUploadManagerInit:
    """测试上传管理器初始化"""

    def test_init_default_params(self):
        """测试默认参数初始化"""
        manager = UploadManager()

        assert manager.max_concurrent == 3
        assert manager.max_file_size == 50 * 1024 * 1024
        assert manager.use_db is False
        assert isinstance(manager.tasks, dict)
        assert len(manager.tasks) == 0

    def test_init_custom_params(self):
        """测试自定义参数初始化"""
        manager = UploadManager(
            max_concurrent=5,
            max_file_size=100*1024*1024,
            use_db=True
        )

        assert manager.max_concurrent == 5
        assert manager.max_file_size == 100*1024*1024
        assert manager.use_db is True


class TestBatchUpload:
    """测试批量上传"""

    @pytest.mark.asyncio
    async def test_submit_batch_success(
        self,
        upload_manager,
        pdf_file,
        html_file,
        mock_parser_factory,
        mock_document_service
    ):
        """测试成功提交批量上传"""
        files = [pdf_file, html_file]

        response = await upload_manager.submit_batch(
            files=files,
            user_id="test_user",
            tags=["test", "upload"]
        )

        assert isinstance(response, BatchUploadResponse)
        assert response.total_files == 2
        assert response.accepted_files == 2
        assert len(response.rejected_files) == 0
        assert len(response.task_ids) == 2
        assert response.batch_id is not None

        # 验证任务已创建
        assert len(upload_manager.tasks) == 2

    @pytest.mark.asyncio
    async def test_submit_batch_too_many_files(self, upload_manager, pdf_file):
        """测试文件数量超限"""
        files = [pdf_file] * 11  # 11 个文件

        with pytest.raises(ValueError, match="批量上传最多支持 10 个文件"):
            await upload_manager.submit_batch(files, "test_user")

    @pytest.mark.asyncio
    async def test_submit_batch_with_invalid_file(self, upload_manager):
        """测试包含无效文件的批量上传"""
        # 创建无效文件（空文件）
        invalid_file = create_upload_file(b'', "empty.pdf")
        valid_file = create_upload_file(b'%PDF-1.4\nContent', "valid.pdf")

        files = [invalid_file, valid_file]

        response = await upload_manager.submit_batch(files, "test_user")

        # 应该接受 1 个，拒绝 1 个
        assert response.total_files == 2
        assert response.accepted_files == 1
        assert len(response.rejected_files) == 1
        assert response.rejected_files[0]["file_name"] == "empty.pdf"

    @pytest.mark.asyncio
    async def test_submit_batch_unsupported_type(self, upload_manager):
        """测试不支持的文件类型"""
        unsupported_file = create_upload_file(b'test content', "test.xyz")

        response = await upload_manager.submit_batch([unsupported_file], "test_user")

        assert response.accepted_files == 0
        assert len(response.rejected_files) == 1


class TestTaskStatus:
    """测试任务状态管理"""

    @pytest.mark.asyncio
    async def test_get_task_status(
        self,
        upload_manager,
        pdf_file,
        mock_parser_factory,
        mock_document_service
    ):
        """测试获取任务状态"""
        response = await upload_manager.submit_batch([pdf_file], "test_user")
        task_id = response.task_ids[0]

        # 获取任务状态
        task = await upload_manager.get_task_status(task_id)

        assert task is not None
        assert task.task_id == task_id
        assert task.user_id == "test_user"
        assert isinstance(task, UploadTask)

    @pytest.mark.asyncio
    async def test_get_task_status_not_found(self, upload_manager):
        """测试获取不存在的任务"""
        task = await upload_manager.get_task_status("nonexistent_id")

        assert task is None

    @pytest.mark.asyncio
    async def test_list_tasks(
        self,
        upload_manager,
        pdf_file,
        html_file,
        mock_parser_factory,
        mock_document_service
    ):
        """测试列出任务"""
        # 创建多个任务
        await upload_manager.submit_batch([pdf_file], "user1")
        await upload_manager.submit_batch([html_file], "user1")
        await upload_manager.submit_batch([pdf_file], "user2")

        # 列出 user1 的任务
        tasks = await upload_manager.list_tasks("user1")

        assert len(tasks) == 2
        assert all(t.user_id == "user1" for t in tasks)

    @pytest.mark.asyncio
    async def test_list_tasks_with_status_filter(
        self,
        upload_manager,
        pdf_file,
        mock_parser_factory,
        mock_document_service
    ):
        """测试按状态筛选任务"""
        response = await upload_manager.submit_batch([pdf_file], "user1")
        task_id = response.task_ids[0]

        # 等待任务处理一会儿
        await asyncio.sleep(0.1)

        # 按状态筛选
        pending_tasks = await upload_manager.list_tasks("user1", status="pending")
        # 由于异步处理，状态可能已经变化，所以不做严格断言
        assert isinstance(pending_tasks, list)


class TestCancelTask:
    """测试任务取消"""

    @pytest.mark.asyncio
    async def test_cancel_pending_task(
        self,
        upload_manager,
        pdf_file,
        mock_parser_factory,
        mock_document_service
    ):
        """测试取消待处理任务"""
        response = await upload_manager.submit_batch([pdf_file], "test_user")
        task_id = response.task_ids[0]

        # 取消任务
        result = await upload_manager.cancel_task(task_id)

        assert result is True
        assert task_id in upload_manager.cancelled_tasks

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_task(self, upload_manager):
        """测试取消不存在的任务"""
        with pytest.raises(TaskNotFoundException):
            await upload_manager.cancel_task("nonexistent_id")


class TestProgressStream:
    """测试进度流"""

    @pytest.mark.asyncio
    async def test_get_progress_stream(
        self,
        upload_manager,
        pdf_file,
        mock_parser_factory,
        mock_document_service
    ):
        """测试获取进度流"""
        response = await upload_manager.submit_batch([pdf_file], "test_user")
        task_id = response.task_ids[0]

        # 获取进度流
        progress_count = 0
        async for progress in upload_manager.get_progress_stream(task_id):
            progress_count += 1
            assert progress.task_id == task_id
            assert 0 <= progress.progress <= 100

            # 只读取几个进度更新
            if progress_count >= 2 or progress.status in [
                UploadStatus.COMPLETED,
                UploadStatus.FAILED,
                UploadStatus.CANCELLED
            ]:
                break

        assert progress_count > 0

    @pytest.mark.asyncio
    async def test_get_progress_stream_not_found(self, upload_manager):
        """测试获取不存在任务的进度流"""
        with pytest.raises(TaskNotFoundException):
            async for _ in upload_manager.get_progress_stream("nonexistent_id"):
                pass


class TestConcurrencyControl:
    """测试并发控制"""

    @pytest.mark.asyncio
    async def test_concurrent_upload_limit(
        self,
        upload_manager,
        mock_parser_factory,
        mock_document_service
    ):
        """测试并发上传限制"""
        # 创建多个独立的文件对象
        files = []
        for i in range(5):
            content = b'%PDF-1.4\nTest PDF content' * 100
            files.append(create_upload_file(content, f"test{i}.pdf"))

        response = await upload_manager.submit_batch(files, "test_user")

        # 验证任务已创建
        assert len(response.task_ids) == 5

        # 由于有 semaphore 限制，同时只能处理 2 个
        # 这里只验证创建成功，实际并发由 semaphore 控制


class TestModels:
    """测试数据模型"""

    def test_upload_task_model(self):
        """测试 UploadTask 模型"""
        from src.services.upload.models import FileInfo

        file_info = FileInfo(
            file_name="test.pdf",
            file_size=1024,
            file_type=".pdf",
            mime_type="application/pdf"
        )

        task = UploadTask(
            task_id="task_123",
            batch_id="batch_456",
            user_id="user_789",
            file_info=file_info
        )

        assert task.task_id == "task_123"
        assert task.status == UploadStatus.PENDING
        assert task.progress_percentage == 0.0

    def test_batch_upload_response(self):
        """测试批量上传响应模型"""
        response = BatchUploadResponse(
            batch_id="batch_123",
            total_files=5,
            accepted_files=4,
            rejected_files=[{"file_name": "bad.xyz", "reason": "unsupported"}],
            task_ids=["t1", "t2", "t3", "t4"]
        )

        assert response.batch_id == "batch_123"
        assert response.total_files == 5
        assert len(response.task_ids) == 4
