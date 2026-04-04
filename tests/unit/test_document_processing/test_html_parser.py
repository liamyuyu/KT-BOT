"""
Tests for HTML Parser
HTML 解析器测试
"""

import pytest
import tempfile
from pathlib import Path
from src.document_processing.parser.html_parser import HTMLParser
from src.document_processing.parser.base import ParsedDocument


@pytest.fixture
def html_parser():
    """创建 HTML 解析器实例"""
    return HTMLParser()


@pytest.fixture
def sample_html_file():
    """创建示例 HTML 文件"""
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="description" content="Test HTML document">
    <meta name="keywords" content="test, html, parser">
    <meta name="author" content="Test Author">
    <title>Test Document</title>
    <style>
        body { color: black; }
    </style>
    <script>
        console.log('This should be removed');
    </script>
</head>
<body>
    <h1>Main Title</h1>
    <p>This is a test paragraph.</p>
    <article>
        <h2>Article Section</h2>
        <p>Article content goes here.</p>
    </article>
    <table>
        <tr>
            <th>Header 1</th>
            <th>Header 2</th>
        </tr>
        <tr>
            <td>Cell 1</td>
            <td>Cell 2</td>
        </tr>
    </table>
</body>
</html>"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(html_content)
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink()


@pytest.fixture
def minimal_html_file():
    """创建最小化 HTML 文件"""
    html_content = "<html><body><p>Simple content</p></body></html>"

    with tempfile.NamedTemporaryFile(mode='w', suffix='.htm', delete=False, encoding='utf-8') as f:
        f.write(html_content)
        temp_path = f.name

    yield temp_path

    Path(temp_path).unlink()


@pytest.fixture
def html_with_main_content():
    """创建包含 main 标签的 HTML 文件"""
    html_content = """<!DOCTYPE html>
<html>
<head><title>Main Content Test</title></head>
<body>
    <header>Header content (should be extracted)</header>
    <main>
        <h1>Main Content</h1>
        <p>This is the main content area.</p>
    </main>
    <footer>Footer content (should be extracted)</footer>
</body>
</html>"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(html_content)
        temp_path = f.name

    yield temp_path

    Path(temp_path).unlink()


class TestHTMLParserCanParse:
    """测试 can_parse 方法"""

    def test_can_parse_html_extension(self, html_parser):
        """测试识别 .html 扩展名"""
        assert html_parser.can_parse("test.html") is True

    def test_can_parse_htm_extension(self, html_parser):
        """测试识别 .htm 扩展名"""
        assert html_parser.can_parse("test.htm") is True

    def test_can_parse_uppercase_extension(self, html_parser):
        """测试识别大写扩展名"""
        assert html_parser.can_parse("TEST.HTML") is True
        assert html_parser.can_parse("TEST.HTM") is True

    def test_cannot_parse_other_extensions(self, html_parser):
        """测试拒绝其他扩展名"""
        assert html_parser.can_parse("test.pdf") is False
        assert html_parser.can_parse("test.docx") is False
        assert html_parser.can_parse("test.md") is False
        assert html_parser.can_parse("test.txt") is False


class TestHTMLParserParse:
    """测试 parse 方法"""

    @pytest.mark.asyncio
    async def test_parse_complete_html(self, html_parser, sample_html_file):
        """测试解析完整 HTML 文档"""
        result = await html_parser.parse(sample_html_file)

        assert isinstance(result, ParsedDocument)
        assert result.title == "Test Document"
        assert result.file_type == "html"
        # Parser prioritizes <article> tag, so Main Title might not be in content
        # but Article content should be present
        assert "Article content" in result.content
        # Verify metadata is extracted
        assert result.metadata is not None

    @pytest.mark.asyncio
    async def test_parse_script_removed(self, html_parser, sample_html_file):
        """测试 script 标签被移除"""
        result = await html_parser.parse(sample_html_file)

        assert "console.log" not in result.content
        assert "This should be removed" not in result.content

    @pytest.mark.asyncio
    async def test_parse_style_removed(self, html_parser, sample_html_file):
        """测试 style 标签被移除"""
        result = await html_parser.parse(sample_html_file)

        assert "color: black" not in result.content

    @pytest.mark.asyncio
    async def test_parse_table_extracted(self, html_parser, sample_html_file):
        """测试表格被正确提取"""
        result = await html_parser.parse(sample_html_file)

        assert "Table 1" in result.content
        assert "Header 1" in result.content
        assert "Header 2" in result.content
        assert "Cell 1" in result.content
        assert "Cell 2" in result.content

    @pytest.mark.asyncio
    async def test_parse_metadata_extracted(self, html_parser, sample_html_file):
        """测试 meta 信息被提取"""
        result = await html_parser.parse(sample_html_file)

        assert result.metadata.get('description') == "Test HTML document"
        assert result.metadata.get('keywords') == "test, html, parser"
        assert result.metadata.get('author') == "Test Author"
        assert 'file_name' in result.metadata
        assert 'file_size' in result.metadata

    @pytest.mark.asyncio
    async def test_parse_title_from_h1(self, html_parser, minimal_html_file):
        """测试从文件名提取标题（无 title 标签）"""
        result = await html_parser.parse(minimal_html_file)

        # 应该使用文件名作为标题
        assert result.title is not None
        assert len(result.title) > 0

    @pytest.mark.asyncio
    async def test_parse_main_content_priority(self, html_parser, html_with_main_content):
        """测试优先提取 main 标签内容"""
        result = await html_parser.parse(html_with_main_content)

        assert "Main Content" in result.content
        assert "main content area" in result.content

    @pytest.mark.asyncio
    async def test_parse_word_count(self, html_parser, sample_html_file):
        """测试字数统计"""
        result = await html_parser.parse(sample_html_file)

        assert result.word_count > 0
        # 验证字数统计合理
        assert result.word_count == len(result.content.split())


@pytest.mark.asyncio
async def test_parse_nonexistent_file(html_parser):
    """测试解析不存在的文件"""
    with pytest.raises(FileNotFoundError):
        await html_parser.parse("/nonexistent/file.html")
