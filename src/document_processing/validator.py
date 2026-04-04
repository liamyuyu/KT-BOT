"""
Document Validator
文档验证器 - 验证文件大小、类型和完整性
"""

import os
import logging
import mimetypes
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel, Field
from fastapi import UploadFile

logger = logging.getLogger(__name__)


class ValidationResult(BaseModel):
    """验证结果"""
    is_valid: bool = Field(..., description="是否通过验证")
    error_message: Optional[str] = Field(None, description="错误信息")
    file_name: str = Field(..., description="文件名")
    file_size: int = Field(..., description="文件大小（字节）")
    mime_type: Optional[str] = Field(None, description="MIME 类型")


class DocumentValidator:
    """文档验证器"""

    # 支持的文件类型及其魔数（文件头）
    MAGIC_NUMBERS = {
        '.pdf': [b'%PDF'],
        '.docx': [b'PK\x03\x04'],  # ZIP 格式
        '.doc': [b'\xD0\xCF\x11\xE0'],  # OLE2 格式
        '.html': [b'<!DOCTYPE', b'<html', b'<HTML', b'<?xml'],
        '.htm': [b'<!DOCTYPE', b'<html', b'<HTML', b'<?xml']
    }

    # 支持的 MIME 类型
    ALLOWED_MIME_TYPES = {
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/msword',
        'text/html',
        'text/plain',
        'text/markdown'
    }

    def __init__(self, max_file_size: int = 50 * 1024 * 1024):
        """
        初始化验证器

        Args:
            max_file_size: 最大文件大小（字节），默认 50MB
        """
        self.max_file_size = max_file_size

    async def validate(self, file: UploadFile) -> ValidationResult:
        """
        验证上传文件

        Args:
            file: FastAPI UploadFile 对象

        Returns:
            ValidationResult: 验证结果
        """
        file_name = file.filename or "unknown"

        # 1. 检查文件名
        if not file_name or file_name == "" or file_name == "unknown":
            return ValidationResult(
                is_valid=False,
                error_message="文件名为空",
                file_name=file_name,
                file_size=0
            )

        # 2. 读取文件内容
        content = await file.read()
        file_size = len(content)

        # 重置文件指针以便后续使用
        await file.seek(0)

        # 3. 检查文件大小
        if file_size == 0:
            return ValidationResult(
                is_valid=False,
                error_message="文件为空",
                file_name=file_name,
                file_size=file_size
            )

        if file_size > self.max_file_size:
            max_size_mb = self.max_file_size / (1024 * 1024)
            actual_size_mb = file_size / (1024 * 1024)
            return ValidationResult(
                is_valid=False,
                error_message=f"文件过大: {actual_size_mb:.2f}MB (最大 {max_size_mb:.0f}MB)",
                file_name=file_name,
                file_size=file_size
            )

        # 4. 检查文件扩展名
        ext = Path(file_name).suffix.lower()
        if ext not in ['.pdf', '.docx', '.doc', '.md', '.html', '.htm']:
            return ValidationResult(
                is_valid=False,
                error_message=f"不支持的文件类型: {ext}",
                file_name=file_name,
                file_size=file_size
            )

        # 5. 验证 MIME 类型
        mime_type = file.content_type or mimetypes.guess_type(file_name)[0]
        if mime_type and mime_type not in self.ALLOWED_MIME_TYPES:
            logger.warning(f"MIME type mismatch for {file_name}: {mime_type}")

        # 6. 验证文件头（魔数）
        if not self._validate_magic_number(content, ext):
            return ValidationResult(
                is_valid=False,
                error_message=f"文件头验证失败，可能是伪造的 {ext} 文件",
                file_name=file_name,
                file_size=file_size,
                mime_type=mime_type
            )

        # 全部验证通过
        return ValidationResult(
            is_valid=True,
            file_name=file_name,
            file_size=file_size,
            mime_type=mime_type
        )

    async def validate_file_path(self, file_path: str) -> ValidationResult:
        """
        验证本地文件路径

        Args:
            file_path: 文件路径

        Returns:
            ValidationResult: 验证结果
        """
        path = Path(file_path)
        file_name = path.name

        # 1. 检查文件是否存在
        if not path.exists():
            return ValidationResult(
                is_valid=False,
                error_message="文件不存在",
                file_name=file_name,
                file_size=0
            )

        if not path.is_file():
            return ValidationResult(
                is_valid=False,
                error_message="不是有效的文件",
                file_name=file_name,
                file_size=0
            )

        # 2. 检查文件大小
        file_size = path.stat().st_size

        if file_size == 0:
            return ValidationResult(
                is_valid=False,
                error_message="文件为空",
                file_name=file_name,
                file_size=file_size
            )

        if file_size > self.max_file_size:
            max_size_mb = self.max_file_size / (1024 * 1024)
            actual_size_mb = file_size / (1024 * 1024)
            return ValidationResult(
                is_valid=False,
                error_message=f"文件过大: {actual_size_mb:.2f}MB (最大 {max_size_mb:.0f}MB)",
                file_name=file_name,
                file_size=file_size
            )

        # 3. 检查文件扩展名
        ext = path.suffix.lower()
        if ext not in ['.pdf', '.docx', '.doc', '.md', '.html', '.htm']:
            return ValidationResult(
                is_valid=False,
                error_message=f"不支持的文件类型: {ext}",
                file_name=file_name,
                file_size=file_size
            )

        # 4. 验证文件头
        with open(file_path, 'rb') as f:
            header = f.read(1024)

        if not self._validate_magic_number(header, ext):
            return ValidationResult(
                is_valid=False,
                error_message=f"文件头验证失败，可能是伪造的 {ext} 文件",
                file_name=file_name,
                file_size=file_size
            )

        # 全部验证通过
        mime_type = mimetypes.guess_type(file_path)[0]
        return ValidationResult(
            is_valid=True,
            file_name=file_name,
            file_size=file_size,
            mime_type=mime_type
        )

    def _validate_magic_number(self, content: bytes, ext: str) -> bool:
        """
        验证文件魔数（文件头）

        Args:
            content: 文件内容（前几个字节）
            ext: 文件扩展名

        Returns:
            bool: 是否匹配
        """
        # Markdown 文件没有固定魔数，跳过验证
        if ext in ['.md']:
            return True

        # 获取该扩展名的魔数列表
        magic_numbers = self.MAGIC_NUMBERS.get(ext)
        if not magic_numbers:
            logger.warning(f"No magic number defined for {ext}")
            return True  # 没有定义魔数则通过

        # 检查文件头是否匹配任一魔数
        for magic in magic_numbers:
            if content.startswith(magic):
                return True

        # HTML 特殊处理：可能有空白字符开头
        if ext in ['.html', '.htm']:
            # 去除前导空白后再检查
            stripped = content.lstrip()
            for magic in magic_numbers:
                if stripped.startswith(magic):
                    return True

        return False

    def get_max_file_size_mb(self) -> float:
        """获取最大文件大小（MB）"""
        return self.max_file_size / (1024 * 1024)
