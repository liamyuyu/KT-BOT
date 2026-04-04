"""
Tests for Document Validator
文档验证器测试
"""

import pytest
import tempfile
from pathlib import Path
from io import BytesIO
from fastapi import UploadFile
from src.document_processing.validator import DocumentValidator, ValidationResult


@pytest.fixture
def validator():
    """创建验证器实例（默认 50MB 限制）"""
    return DocumentValidator(max_file_size=50 * 1024 * 1024)


@pytest.fixture
def small_validator():
    """创建小文件限制的验证器（1KB）"""
    return DocumentValidator(max_file_size=1024)


def create_upload_file(content: bytes, filename: str, content_type: str = None) -> UploadFile:
    """创建 FastAPI UploadFile 对象"""
    file_obj = BytesIO(content)
    upload = UploadFile(filename=filename, file=file_obj)
    # Use object.__setattr__ to bypass property setter
    if content_type:
        object.__setattr__(upload, '_content_type', content_type)
    return upload


class TestValidatorUploadFile:
    """测试验证 UploadFile"""

    @pytest.mark.asyncio
    async def test_validate_valid_pdf(self, validator):
        """测试验证有效的 PDF 文件"""
        # PDF 魔数
        content = b'%PDF-1.4\n%\xE2\xE3\xCF\xD3\n' + b'test content' * 100
        file = create_upload_file(content, "test.pdf", "application/pdf")

        result = await validator.validate(file)

        assert result.is_valid is True
        assert result.error_message is None
        assert result.file_name == "test.pdf"
        assert result.file_size > 0

    @pytest.mark.asyncio
    async def test_validate_valid_docx(self, validator):
        """测试验证有效的 DOCX 文件"""
        # ZIP 魔数（DOCX 是 ZIP 格式）
        content = b'PK\x03\x04' + b'fake docx content' * 50
        file = create_upload_file(content, "test.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

        result = await validator.validate(file)

        assert result.is_valid is True
        assert result.file_name == "test.docx"

    @pytest.mark.asyncio
    async def test_validate_valid_html(self, validator):
        """测试验证有效的 HTML 文件"""
        content = b'<!DOCTYPE html><html><body>Test</body></html>'
        file = create_upload_file(content, "test.html", "text/html")

        result = await validator.validate(file)

        assert result.is_valid is True
        assert result.file_name == "test.html"

    @pytest.mark.asyncio
    async def test_validate_valid_markdown(self, validator):
        """测试验证有效的 Markdown 文件"""
        content = b'# Test Markdown\n\nThis is a test.'
        file = create_upload_file(content, "test.md", "text/markdown")

        result = await validator.validate(file)

        assert result.is_valid is True
        assert result.file_name == "test.md"

    @pytest.mark.asyncio
    async def test_validate_empty_filename(self, validator):
        """测试验证空文件名"""
        content = b'test content'
        file = create_upload_file(content, "", "text/plain")

        result = await validator.validate(file)

        assert result.is_valid is False
        assert "文件名为空" in result.error_message

    @pytest.mark.asyncio
    async def test_validate_empty_file(self, validator):
        """测试验证空文件"""
        content = b''
        file = create_upload_file(content, "empty.pdf", "application/pdf")

        result = await validator.validate(file)

        assert result.is_valid is False
        assert "文件为空" in result.error_message
        assert result.file_size == 0

    @pytest.mark.asyncio
    async def test_validate_file_too_large(self, small_validator):
        """测试验证超大文件"""
        # 创建 2KB 内容，超过 1KB 限制
        content = b'a' * 2048
        file = create_upload_file(content, "large.pdf", "application/pdf")

        result = await small_validator.validate(file)

        assert result.is_valid is False
        assert "文件过大" in result.error_message

    @pytest.mark.asyncio
    async def test_validate_unsupported_extension(self, validator):
        """测试验证不支持的文件扩展名"""
        content = b'test content'
        file = create_upload_file(content, "test.xyz", "application/octet-stream")

        result = await validator.validate(file)

        assert result.is_valid is False
        assert "不支持的文件类型" in result.error_message

    @pytest.mark.asyncio
    async def test_validate_magic_number_mismatch(self, validator):
        """测试验证文件头不匹配（伪造文件）"""
        # 使用错误的文件头
        content = b'FAKE_HEADER' + b'not a real pdf'
        file = create_upload_file(content, "fake.pdf", "application/pdf")

        result = await validator.validate(file)

        assert result.is_valid is False
        assert "文件头验证失败" in result.error_message


class TestValidatorFilePath:
    """测试验证本地文件路径"""

    @pytest.mark.asyncio
    async def test_validate_valid_file_path(self, validator):
        """测试验证有效的文件路径"""
        # 创建临时 PDF 文件
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as f:
            f.write(b'%PDF-1.4\ntest content')
            temp_path = f.name

        try:
            result = await validator.validate_file_path(temp_path)

            assert result.is_valid is True
            assert result.file_size > 0
        finally:
            Path(temp_path).unlink()

    @pytest.mark.asyncio
    async def test_validate_nonexistent_file(self, validator):
        """测试验证不存在的文件"""
        result = await validator.validate_file_path("/nonexistent/file.pdf")

        assert result.is_valid is False
        assert "文件不存在" in result.error_message

    @pytest.mark.asyncio
    async def test_validate_directory_path(self, validator):
        """测试验证目录路径（不是文件）"""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = await validator.validate_file_path(temp_dir)

            assert result.is_valid is False
            assert "不是有效的文件" in result.error_message

    @pytest.mark.asyncio
    async def test_validate_empty_file_path(self, validator):
        """测试验证空文件"""
        # 创建空文件
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as f:
            temp_path = f.name

        try:
            result = await validator.validate_file_path(temp_path)

            assert result.is_valid is False
            assert "文件为空" in result.error_message
        finally:
            Path(temp_path).unlink()

    @pytest.mark.asyncio
    async def test_validate_html_with_whitespace(self, validator):
        """测试验证带前导空白的 HTML 文件"""
        # HTML 文件可能有前导空白
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.html', delete=False) as f:
            f.write(b'\n\n  <!DOCTYPE html><html><body>Test</body></html>')
            temp_path = f.name

        try:
            result = await validator.validate_file_path(temp_path)

            assert result.is_valid is True
        finally:
            Path(temp_path).unlink()


class TestValidatorUtilities:
    """测试验证器工具方法"""

    def test_get_max_file_size_mb(self, validator):
        """测试获取最大文件大小（MB）"""
        assert validator.get_max_file_size_mb() == 50.0

    def test_get_max_file_size_mb_small(self, small_validator):
        """测试获取小文件限制大小"""
        expected = 1024 / (1024 * 1024)
        assert abs(small_validator.get_max_file_size_mb() - expected) < 0.001
