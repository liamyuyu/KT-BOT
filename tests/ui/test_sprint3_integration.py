"""
Sprint 3 UI 集成测试
测试引用溯源和文档上传功能
"""
import pytest
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestCitationIntegration:
    """测试引用溯源 UI 集成"""

    def test_citation_badge_function_exists(self):
        """测试引用标签组件存在"""
        from src.ui.components.citation import create_citation_badge, highlight_content

        # 测试引用标签创建
        citation = {
            "source_id": "TEST-123",
            "source_type": "JIRA",
            "source_url": "https://jira.example.com/browse/TEST-123",
            "relevance_score": 0.85
        }

        badge_html = create_citation_badge(citation)
        assert badge_html is not None
        assert "TEST-123" in badge_html
        assert "JIRA" in badge_html
        assert "85" in badge_html  # 85% relevance

    def test_highlight_content_function(self):
        """测试内容高亮功能"""
        from src.ui.components.citation import highlight_content

        content = "这是一段测试文本，包含关键词。"
        highlights = [(5, 7), (13, 16)]  # 高亮"测试"和"关键词"

        highlighted = highlight_content(content, highlights)
        assert highlighted is not None
        assert "<mark" in highlighted  # 包含高亮标记

    def test_chat_page_imports_citation_components(self):
        """测试 ChatPage 导入引用组件"""
        import importlib.util
        import ast

        spec = importlib.util.spec_from_file_location(
            "chat_page",
            project_root / "src/ui/pages/chat_page.py"
        )
        with open(spec.origin, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())

        # 检查是否导入了 citation 组件
        imports = [node for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        citation_imports = [
            imp for imp in imports
            if imp.module and "citation" in imp.module
        ]

        assert len(citation_imports) > 0, "ChatPage 应该导入 citation 组件"

    def test_chat_service_returns_citation_field(self):
        """测试 ChatService 返回 citation 字段"""
        from src.api.schemas.chat import RetrievedContext

        # 测试 RetrievedContext 模型包含 citation 字段
        context = RetrievedContext(
            chunk_id="test-chunk-1",
            content="测试内容",
            score=0.9,
            source={
                "issue_key": "TEST-123",
                "url": "https://test.example.com"
            },
            citation={
                "source_id": "TEST-123",
                "source_type": "jira",
                "relevance_score": 0.9
            }
        )

        assert context.citation is not None
        assert context.citation["source_id"] == "TEST-123"


class TestFileUploadIntegration:
    """测试文档上传 UI 集成"""

    def test_api_client_has_upload_file_method(self):
        """测试 API Client 包含文件上传方法"""
        from src.ui.utils.api_client import ChatAPIClient

        client = ChatAPIClient()
        assert hasattr(client, 'upload_document_file'), "API Client 应该有 upload_document_file 方法"

    def test_document_parsers_exist(self):
        """测试文档解析器存在"""
        from src.document_processing.parser.factory import ParserFactory

        factory = ParserFactory()
        assert factory is not None
        assert len(factory.parsers) >= 3  # PDF, DOCX, Markdown

    def test_parser_can_identify_file_types(self):
        """测试解析器能识别文件类型"""
        from src.document_processing.parser.factory import ParserFactory

        factory = ParserFactory()

        # 测试能识别各种文件类型
        try:
            pdf_parser = factory.get_parser("test.pdf")
            assert pdf_parser is not None
        except ValueError:
            pytest.fail("应该能识别 PDF 文件")

        try:
            docx_parser = factory.get_parser("test.docx")
            assert docx_parser is not None
        except ValueError:
            pytest.fail("应该能识别 DOCX 文件")

        try:
            md_parser = factory.get_parser("test.md")
            assert md_parser is not None
        except ValueError:
            pytest.fail("应该能识别 Markdown 文件")

    def test_document_page_has_file_upload_ui(self):
        """测试 DocumentPage 包含文件上传 UI"""
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "document_page",
            project_root / "src/ui/pages/document_page.py"
        )
        with open(spec.origin, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查是否包含文件上传相关代码
        assert "gr.File" in content, "应该包含 Gradio File 组件"
        assert "upload_file" in content, "应该包含文件上传函数"
        assert "upload_file_btn" in content, "应该包含文件上传按钮"
        assert "📤 文件上传" in content, "应该包含文件上传 Tab"


class TestBackwardCompatibility:
    """测试向后兼容性"""

    def test_retrieved_context_without_citation(self):
        """测试 RetrievedContext 在没有 citation 时仍然工作"""
        from src.api.schemas.chat import RetrievedContext

        # 不带 citation 字段应该也能正常工作
        context = RetrievedContext(
            chunk_id="test-chunk-1",
            content="测试内容",
            score=0.9,
            source={
                "issue_key": "TEST-123",
                "url": "https://test.example.com"
            }
        )

        assert context.citation is None  # citation 应该是可选的

    def test_chat_format_response_handles_no_citation(self):
        """测试 _format_response 处理没有 citation 的情况"""
        from src.ui.pages.chat_page import ChatPage

        # 测试没有 citation 的上下文
        contexts = [
            {
                "chunk_id": "test-1",
                "content": "测试内容",
                "score": 0.9,
                "source": {
                    "source_type": "jira_issue",
                    "issue_key": "TEST-123",
                    "title": "测试标题"
                }
            }
        ]

        formatted = ChatPage._format_response("测试回答", contexts)
        assert formatted is not None
        assert "测试回答" in formatted
        assert "参考来源" in formatted


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
