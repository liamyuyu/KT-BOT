"""
Integration Tests for Upload API
上传 API 集成测试
"""

import pytest
import asyncio
from io import BytesIO
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock, AsyncMock

from src.api.main import app
from src.services.upload import get_upload_manager
from src.document_processing.parser.base import ParsedDocument


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
def reset_upload_manager():
    """重置上传管理器"""
    # 在每个测试前后重置全局单例
    import src.services.upload as upload_module
    original_manager = upload_module._upload_manager
    upload_module._upload_manager = None

    yield

    upload_module._upload_manager = original_manager


@pytest.fixture
def mock_services():
    """Mock 文档服务和解析器"""
    # Mock parser
    with patch('src.services.upload.manager.get_parser_factory') as mock_parser_factory:
        factory = Mock()
        parsed_doc = ParsedDocument(
            title="Test Document",
            content="Test content" * 100,
            metadata={"test": "meta"},
            word_count=200,
            file_type="pdf"
        )
        factory.parse_file = AsyncMock(return_value=parsed_doc)
        mock_parser_factory.return_value = factory

        # Mock document service
        with patch('src.services.upload.manager.get_document_service') as mock_doc_service:
            service = Mock()
            upload_response = Mock()
            upload_response.document_id = "doc_test_123"
            upload_response.chunk_count = 10
            service.upload_document = AsyncMock(return_value=upload_response)
            mock_doc_service.return_value = service

            yield


def create_test_file(filename: str, content: bytes):
    """创建测试文件"""
    return ('files', (filename, BytesIO(content), 'application/octet-stream'))


class TestBatchUploadAPI:
    """测试批量上传 API"""

    def test_batch_upload_success(
        self,
        client,
        reset_upload_manager,
        mock_services
    ):
        """测试成功批量上传"""
        # 创建测试文件
        pdf_content = b'%PDF-1.4\nTest PDF content' * 100
        html_content = b'<!DOCTYPE html><html><body>Test</body></html>'

        files = [
            create_test_file('test1.pdf', pdf_content),
            create_test_file('test2.html', html_content)
        ]

        data = {
            'user_id': 'test_user',
            'tags': 'test,integration'
        }

        response = client.post('/api/v1/documents/batch-upload', files=files, data=data)

        assert response.status_code == 201
        result = response.json()

        assert 'batch_id' in result
        assert result['total_files'] == 2
        assert result['accepted_files'] == 2
        assert len(result['task_ids']) == 2
        assert len(result['rejected_files']) == 0

    def test_batch_upload_too_many_files(self, client, reset_upload_manager):
        """测试文件数量超限"""
        pdf_content = b'%PDF-1.4\nTest' * 100
        files = [create_test_file(f'test{i}.pdf', pdf_content) for i in range(11)]

        data = {'user_id': 'test_user'}

        response = client.post('/api/v1/documents/batch-upload', files=files, data=data)

        assert response.status_code == 400
        assert '10 个文件' in response.json()['detail']

    def test_batch_upload_with_invalid_file(
        self,
        client,
        reset_upload_manager,
        mock_services
    ):
        """测试包含无效文件"""
        valid_pdf = b'%PDF-1.4\nValid content' * 100
        invalid_empty = b''

        files = [
            create_test_file('valid.pdf', valid_pdf),
            create_test_file('empty.pdf', invalid_empty)
        ]

        data = {'user_id': 'test_user'}

        response = client.post('/api/v1/documents/batch-upload', files=files, data=data)

        assert response.status_code == 201
        result = response.json()

        assert result['accepted_files'] == 1
        assert len(result['rejected_files']) == 1
        assert result['rejected_files'][0]['file_name'] == 'empty.pdf'

    def test_batch_upload_unsupported_type(
        self,
        client,
        reset_upload_manager
    ):
        """测试不支持的文件类型"""
        files = [create_test_file('test.xyz', b'test content')]
        data = {'user_id': 'test_user'}

        response = client.post('/api/v1/documents/batch-upload', files=files, data=data)

        assert response.status_code == 201
        result = response.json()

        assert result['accepted_files'] == 0
        assert len(result['rejected_files']) == 1


class TestListTasksAPI:
    """测试列出任务 API"""

    def test_list_tasks(
        self,
        client,
        reset_upload_manager,
        mock_services
    ):
        """测试列出任务"""
        # 先创建一些任务
        pdf_content = b'%PDF-1.4\nTest' * 100
        files = [create_test_file('test.pdf', pdf_content)]
        data = {'user_id': 'test_user'}

        upload_response = client.post('/documents/batch-upload', files=files, data=data)
        assert upload_response.status_code == 201

        # 列出任务
        response = client.get('/api/v1/documents/upload/tasks?user_id=test_user')

        assert response.status_code == 200
        result = response.json()

        assert isinstance(result, list)
        assert len(result) >= 1

        # 验证任务结构
        task = result[0]
        assert 'task_id' in task
        assert 'batch_id' in task
        assert 'file_name' in task
        assert 'status' in task
        assert 'progress_percentage' in task

    def test_list_tasks_with_status_filter(
        self,
        client,
        reset_upload_manager,
        mock_services
    ):
        """测试按状态筛选任务"""
        pdf_content = b'%PDF-1.4\nTest' * 100
        files = [create_test_file('test.pdf', pdf_content)]
        data = {'user_id': 'test_user'}

        client.post('/documents/batch-upload', files=files, data=data)

        # 按状态筛选
        response = client.get('/api/v1/documents/upload/tasks?user_id=test_user&status=pending')

        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, list)

    def test_list_tasks_with_limit(
        self,
        client,
        reset_upload_manager,
        mock_services
    ):
        """测试任务数量限制"""
        pdf_content = b'%PDF-1.4\nTest' * 100
        files = [create_test_file(f'test{i}.pdf', pdf_content) for i in range(3)]
        data = {'user_id': 'test_user'}

        client.post('/documents/batch-upload', files=files, data=data)

        # 限制返回 2 个
        response = client.get('/api/v1/documents/upload/tasks?user_id=test_user&limit=2')

        assert response.status_code == 200
        result = response.json()
        assert len(result) <= 2


class TestCancelTaskAPI:
    """测试取消任务 API"""

    def test_cancel_task_success(
        self,
        client,
        reset_upload_manager,
        mock_services
    ):
        """测试成功取消任务"""
        pdf_content = b'%PDF-1.4\nTest' * 100
        files = [create_test_file('test.pdf', pdf_content)]
        data = {'user_id': 'test_user'}

        upload_response = client.post('/documents/batch-upload', files=files, data=data)
        task_id = upload_response.json()['task_ids'][0]

        # 取消任务
        response = client.post(f'/api/v1/documents/upload/{task_id}/cancel')

        assert response.status_code == 200
        result = response.json()

        assert result['task_id'] == task_id
        assert result['success'] is True

    def test_cancel_nonexistent_task(self, client, reset_upload_manager):
        """测试取消不存在的任务"""
        response = client.post('/api/v1/documents/upload/nonexistent_id/cancel')

        assert response.status_code == 404


class TestProgressStreamAPI:
    """测试进度流 API"""

    def test_get_progress_stream(
        self,
        client,
        reset_upload_manager,
        mock_services
    ):
        """测试获取进度流"""
        pdf_content = b'%PDF-1.4\nTest' * 100
        files = [create_test_file('test.pdf', pdf_content)]
        data = {'user_id': 'test_user'}

        upload_response = client.post('/documents/batch-upload', files=files, data=data)
        task_id = upload_response.json()['task_ids'][0]

        # 获取进度流（只读取开头）
        with client.stream('GET', f'/api/v1/documents/upload/{task_id}/progress') as response:
            assert response.status_code == 200
            assert 'text/event-stream' in response.headers.get('content-type', '')

            # 读取几个事件
            count = 0
            for line in response.iter_lines():
                if line:
                    count += 1
                    if count >= 5:  # 只读取几行
                        break

    def test_get_progress_stream_not_found(self, client, reset_upload_manager):
        """测试获取不存在任务的进度流"""
        response = client.get('/api/v1/documents/upload/nonexistent_id/progress')

        assert response.status_code == 404


class TestAPIResponseFormat:
    """测试 API 响应格式"""

    def test_batch_upload_response_format(
        self,
        client,
        reset_upload_manager,
        mock_services
    ):
        """测试批量上传响应格式"""
        pdf_content = b'%PDF-1.4\nTest' * 100
        files = [create_test_file('test.pdf', pdf_content)]
        data = {'user_id': 'test_user'}

        response = client.post('/api/v1/documents/batch-upload', files=files, data=data)
        result = response.json()

        # 验证响应字段
        required_fields = ['batch_id', 'total_files', 'accepted_files', 'rejected_files', 'task_ids']
        for field in required_fields:
            assert field in result

    def test_task_list_response_format(
        self,
        client,
        reset_upload_manager,
        mock_services
    ):
        """测试任务列表响应格式"""
        pdf_content = b'%PDF-1.4\nTest' * 100
        files = [create_test_file('test.pdf', pdf_content)]
        data = {'user_id': 'test_user'}

        client.post('/documents/batch-upload', files=files, data=data)

        response = client.get('/api/v1/documents/upload/tasks?user_id=test_user')
        result = response.json()

        if len(result) > 0:
            task = result[0]
            required_fields = [
                'task_id', 'batch_id', 'file_name', 'file_size',
                'status', 'progress_percentage', 'created_at', 'updated_at'
            ]
            for field in required_fields:
                assert field in task
