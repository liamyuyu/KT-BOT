"""
Text Chunker
文本分块器：将长文本分割成固定大小的块
"""

import re
import logging
from typing import List, Dict, Any

from .models import Chunk, ChunkingConfig
from .exceptions import ChunkingError, InvalidConfigError

logger = logging.getLogger(__name__)


class TextChunker:
    """
    文本分块器
    使用固定长度分块策略，支持重叠
    """

    def __init__(self, config: ChunkingConfig = None):
        """
        初始化文本分块器

        Args:
            config: 分块配置，如果不提供则使用默认配置
        """
        self.config = config or ChunkingConfig()
        try:
            self.config.validate_config()
        except ValueError as e:
            raise InvalidConfigError(f"Invalid chunking config: {e}")

        logger.info(
            f"TextChunker initialized with chunk_size={self.config.chunk_size}, "
            f"chunk_overlap={self.config.chunk_overlap}, "
            f"min_chunk_size={self.config.min_chunk_size}"
        )

    def chunk_text(
        self,
        text: str,
        parent_id: str,
        metadata: Dict[str, Any] = None
    ) -> List[Chunk]:
        """
        将文本分块

        Args:
            text: 要分块的文本内容
            parent_id: 父文档 ID（如 Jira Issue Key）
            metadata: 块的元数据（将被复制到每个块）

        Returns:
            Chunk 对象列表

        Raises:
            ChunkingError: 分块失败时抛出
        """
        if not text or not text.strip():
            logger.warning(f"Empty text for parent_id={parent_id}, skipping chunking")
            return []

        if not parent_id:
            raise ChunkingError("parent_id is required for chunking")

        try:
            # 清理文本
            cleaned_text = self._clean_text(text)

            # 如果文本太短，直接返回单个块
            if len(cleaned_text) <= self.config.min_chunk_size:
                logger.debug(
                    f"Text too short ({len(cleaned_text)} chars), returning as single chunk"
                )
                return [
                    Chunk(
                        chunk_id=f"{parent_id}_chunk_0",
                        parent_id=parent_id,
                        content=cleaned_text,
                        chunk_index=0,
                        start_index=0,
                        end_index=len(cleaned_text),
                        metadata=metadata or {}
                    )
                ]

            # 分割文本
            chunks = self._split_text(cleaned_text)

            # 创建 Chunk 对象
            chunk_objects = []
            current_position = 0

            for idx, chunk_content in enumerate(chunks):
                # 计算实际的 start_index（考虑重叠）
                if idx > 0:
                    # 对于非首块，start_index 需要减去 overlap
                    start_index = current_position
                else:
                    start_index = 0

                end_index = start_index + len(chunk_content)

                chunk = Chunk(
                    chunk_id=f"{parent_id}_chunk_{idx}",
                    parent_id=parent_id,
                    content=chunk_content,
                    chunk_index=idx,
                    start_index=start_index,
                    end_index=end_index,
                    metadata=metadata or {}
                )
                chunk_objects.append(chunk)

                # 更新当前位置（移动 chunk_size - overlap）
                current_position += (len(chunk_content) - self.config.chunk_overlap)

            logger.info(
                f"Successfully chunked text for parent_id={parent_id}: "
                f"{len(cleaned_text)} chars -> {len(chunk_objects)} chunks"
            )

            return chunk_objects

        except Exception as e:
            raise ChunkingError(f"Failed to chunk text for parent_id={parent_id}: {e}")

    def _split_text(self, text: str) -> List[str]:
        """
        使用固定长度分割文本，支持重叠

        Args:
            text: 要分割的文本

        Returns:
            文本块列表
        """
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            # 计算块的结束位置
            end = min(start + self.config.chunk_size, text_length)

            # 提取块
            chunk = text[start:end]

            # 如果不是最后一块，且块大小达到 chunk_size，尝试在句子边界分割
            if end < text_length and len(chunk) == self.config.chunk_size:
                chunk = self._adjust_chunk_boundary(chunk)

            # 过滤掉太短的块（除非是最后一块）
            if len(chunk.strip()) >= self.config.min_chunk_size or end >= text_length:
                chunks.append(chunk)

            # 移动到下一个起始位置（考虑重叠）
            start += (self.config.chunk_size - self.config.chunk_overlap)

        return chunks

    def _adjust_chunk_boundary(self, chunk: str) -> str:
        """
        调整块边界，尝试在句子边界处分割

        Args:
            chunk: 原始块

        Returns:
            调整后的块
        """
        # 定义句子结束标点
        sentence_endings = ["。", "！", "？", ".", "!", "?", "\n\n"]

        # 从后向前查找最近的句子结束标点
        for i in range(len(chunk) - 1, max(len(chunk) - 200, 0), -1):
            if chunk[i] in sentence_endings:
                return chunk[:i + 1]

        # 如果找不到句子边界，查找空格或标点
        for i in range(len(chunk) - 1, max(len(chunk) - 100, 0), -1):
            if chunk[i] in [" ", "，", ",", ";", "；", ":", "："]:
                return chunk[:i + 1]

        # 如果都找不到，返回原始块
        return chunk

    def _clean_text(self, text: str) -> str:
        """
        清理文本：移除多余的空白字符

        Args:
            text: 原始文本

        Returns:
            清理后的文本
        """
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)

        # 移除首尾空白
        text = text.strip()

        return text
