"""
Unit Tests for TextChunker
测试文本分块器
"""

import pytest
from src.core.rag.chunker import TextChunker
from src.core.rag.models import ChunkingConfig
from src.core.rag.exceptions import ChunkingError, InvalidConfigError


class TestTextChunker:
    """TextChunker 单元测试"""

    def test_basic_chunking(self):
        """测试基础分块功能"""
        config = ChunkingConfig(chunk_size=100, chunk_overlap=20, min_chunk_size=10)
        chunker = TextChunker(config)

        text = "This is a test document. " * 20  # ~500 字符
        chunks = chunker.chunk_text(text, parent_id="TEST-001")

        # 验证
        assert len(chunks) > 0
        assert all(chunk.parent_id == "TEST-001" for chunk in chunks)
        assert all(chunk.chunk_id.startswith("TEST-001_chunk_") for chunk in chunks)
        assert chunks[0].chunk_index == 0

    def test_small_text(self):
        """测试短文本（小于最小块大小）"""
        config = ChunkingConfig(chunk_size=1000, chunk_overlap=200, min_chunk_size=50)
        chunker = TextChunker(config)

        text = "Short text"  # 10 字符，小于 min_chunk_size
        chunks = chunker.chunk_text(text, parent_id="TEST-002")

        # 应该返回单个块
        assert len(chunks) == 1
        assert chunks[0].content == text
        assert chunks[0].chunk_index == 0

    def test_empty_text(self):
        """测试空文本"""
        chunker = TextChunker()
        chunks = chunker.chunk_text("", parent_id="TEST-003")

        # 应该返回空列表
        assert len(chunks) == 0

    def test_whitespace_text(self):
        """测试只有空白字符的文本"""
        chunker = TextChunker()
        chunks = chunker.chunk_text("   \n  \t  ", parent_id="TEST-004")

        # 应该返回空列表
        assert len(chunks) == 0

    def test_missing_parent_id(self):
        """测试缺少 parent_id"""
        chunker = TextChunker()

        with pytest.raises(ChunkingError, match="parent_id is required"):
            chunker.chunk_text("Some text", parent_id="")

    def test_metadata_preservation(self):
        """测试元数据保留"""
        chunker = TextChunker()
        metadata = {"source": "jira", "issue_type": "Story"}

        text = "Test document " * 100
        chunks = chunker.chunk_text(text, parent_id="TEST-005", metadata=metadata)

        # 验证所有块都有元数据
        for chunk in chunks:
            assert chunk.metadata == metadata

    def test_chunk_overlap(self):
        """测试块重叠"""
        config = ChunkingConfig(chunk_size=100, chunk_overlap=20, min_chunk_size=10)
        chunker = TextChunker(config)

        text = "A" * 250  # 250 个字符
        chunks = chunker.chunk_text(text, parent_id="TEST-006")

        # 验证有多个块
        assert len(chunks) > 1

        # 验证块大小
        for chunk in chunks[:-1]:  # 除了最后一块
            assert len(chunk.content) <= config.chunk_size

    def test_invalid_config(self):
        """测试无效配置"""
        # overlap >= chunk_size
        with pytest.raises(InvalidConfigError):
            config = ChunkingConfig(chunk_size=100, chunk_overlap=100)
            chunker = TextChunker(config)

        # min_chunk_size > chunk_size
        with pytest.raises(InvalidConfigError):
            config = ChunkingConfig(chunk_size=100, chunk_overlap=20, min_chunk_size=200)
            chunker = TextChunker(config)

    def test_chinese_text(self):
        """测试中文文本分块"""
        config = ChunkingConfig(chunk_size=100, chunk_overlap=20, min_chunk_size=10)
        chunker = TextChunker(config)

        text = "这是一个测试文档。" * 50
        chunks = chunker.chunk_text(text, parent_id="TEST-007")

        assert len(chunks) > 0
        for chunk in chunks:
            assert chunk.content.strip()  # 内容不为空

    def test_mixed_language_text(self):
        """测试中英文混合文本"""
        chunker = TextChunker()

        text = "This is a test document. 这是一个测试文档。" * 20
        chunks = chunker.chunk_text(text, parent_id="TEST-008")

        assert len(chunks) > 0
        for chunk in chunks:
            assert chunk.parent_id == "TEST-008"

    def test_special_characters(self):
        """测试特殊字符"""
        chunker = TextChunker()

        text = "Test with special chars: @#$%^&*() \n\t 测试特殊字符：，。！？" * 20
        chunks = chunker.chunk_text(text, parent_id="TEST-009")

        assert len(chunks) > 0

    def test_chunk_positions(self):
        """测试块的位置索引"""
        config = ChunkingConfig(chunk_size=100, chunk_overlap=20, min_chunk_size=10)
        chunker = TextChunker(config)

        text = "A" * 250
        chunks = chunker.chunk_text(text, parent_id="TEST-010")

        # 验证位置
        for idx, chunk in enumerate(chunks):
            assert chunk.chunk_index == idx
            assert chunk.start_index >= 0
            assert chunk.end_index > chunk.start_index
            assert chunk.end_index <= len(text)
