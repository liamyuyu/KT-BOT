"""
TitleGenerator 单元测试
Story 5.1 Phase 5
"""

import pytest
from src.services.conversation.title_generator import TitleGenerator
from src.services.conversation.models import TitleGenerationConfig, TitleGenerationMethod


@pytest.fixture
def generator():
    """创建 TitleGenerator 实例"""
    return TitleGenerator()


class TestTitleGenerator:
    """测试 TitleGenerator"""

    def test_generate_title_from_question(self, generator):
        """测试从问句生成标题"""
        text = "如何优化 Python 程序的性能？有什么好的工具推荐吗？"

        title = generator.generate_title(text)

        assert title is not None
        assert len(title) > 0
        # 应该提取出问句
        assert "如何优化 Python 程序的性能" in title or "优化" in title or "Python" in title

    def test_generate_title_from_keywords(self, generator):
        """测试从关键词生成标题"""
        text = """
        Python 是一种高级编程语言，具有简洁的语法和强大的功能。
        在性能优化方面，可以使用 Cython 和 NumPy 等工具。
        同时，异步编程也能显著提升程序性能。
        """

        title = generator.generate_title(text)

        assert title is not None
        assert "关于" in title or len(title) > 0
        # 应该包含关键词
        assert any(keyword in title for keyword in ["Python", "性能", "优化", "异步", "编程"])

    def test_generate_title_short_text(self, generator):
        """测试短文本标题生成"""
        text = "Python"

        title = generator.generate_title(text)

        assert title is not None
        assert len(title) > 0

    def test_generate_title_empty_text(self, generator):
        """测试空文本"""
        text = ""

        title = generator.generate_title(text)

        assert title == "新对话"

    def test_generate_title_max_length(self, generator):
        """测试标题长度限制"""
        text = "这是一个非常长的文本，包含很多关键词和信息，目的是测试标题长度限制功能是否正常工作。" * 10

        config = TitleGenerationConfig(max_length=30)
        title = generator.generate_title(text, config)

        assert len(title) <= 33  # 30 + "..."

    def test_generate_title_with_config(self, generator):
        """测试使用自定义配置"""
        text = """
        Docker 是一个开源的容器化平台，可以用来打包、分发和运行应用程序。
        它通过容器技术实现了应用的隔离和标准化部署。
        """

        config = TitleGenerationConfig(
            method=TitleGenerationMethod.KEYWORD,
            keyword_count=2
        )

        title = generator.generate_title(text, config)

        assert title is not None
        assert len(title) > 0

    def test_extract_question(self, generator):
        """测试问句提取"""
        # 有效的问句
        text1 = "如何学习 Python？"
        question1 = generator._extract_question(text1)
        assert question1 is not None
        assert "如何学习 Python" in question1

        # 没有问句的文本
        text2 = "Python 是一种编程语言。"
        question2 = generator._extract_question(text2)
        assert question2 is None

        # 太短的问句
        text3 = "为什么？"
        question3 = generator._extract_question(text3)
        assert question3 is None

    def test_clean_text(self, generator):
        """测试文本清理"""
        text = "Python   性能\n\n优化  @#$%"

        cleaned = generator._clean_text(text)

        assert "Python" in cleaned
        assert "性能" in cleaned
        assert "优化" in cleaned
        # 特殊字符应被移除
        assert "@#$%" not in cleaned
        # 多余空白应被压缩
        assert "   " not in cleaned

    def test_extract_keywords(self, generator):
        """测试关键词提取"""
        text = """
        机器学习是人工智能的一个分支，通过算法让计算机从数据中学习模式。
        深度学习是机器学习的一个子领域，使用神经网络进行特征学习。
        """

        keywords = generator.extract_keywords(text, top_k=5)

        assert isinstance(keywords, list)
        assert len(keywords) <= 5
        # 应该包含重要关键词
        assert any(kw in ["机器学习", "深度学习", "神经网络", "算法"] for kw in keywords)

    def test_generate_title_from_keywords_list(self, generator):
        """测试根据关键词列表生成标题"""
        keywords = ["Python", "性能", "优化"]

        title = generator.generate_title_from_keywords(keywords)

        assert title is not None
        assert "关于" in title
        assert "Python" in title
        assert "性能" in title

    def test_generate_title_from_empty_keywords(self, generator):
        """测试空关键词列表"""
        keywords = []

        title = generator.generate_title_from_keywords(keywords)

        assert title == "新对话"

    def test_stopwords_filtering(self, generator):
        """测试停用词过滤"""
        text = "我的Python程序是如何运行的？"

        title = generator.generate_title(text)

        # 停用词应该被过滤掉
        assert "我的" not in title or "是" not in title

    def test_multiple_questions(self, generator):
        """测试包含多个问句的文本"""
        text = """
        什么是 Docker？它有什么优点？
        如何在生产环境中部署 Docker 容器？
        有哪些最佳实践可以参考？
        """

        title = generator.generate_title(text)

        assert title is not None
        # 应该提取第一个问句
        assert "Docker" in title or "什么" in title

    def test_chinese_and_english_mixed(self, generator):
        """测试中英文混合文本"""
        text = "如何使用 Python 和 NumPy 进行数据处理和 machine learning？"

        title = generator.generate_title(text)

        assert title is not None
        assert len(title) > 0
        # 应该包含中英文关键词
        assert any(word in title for word in ["Python", "NumPy", "数据", "processing", "learning"])

    def test_special_characters(self, generator):
        """测试包含特殊字符的文本"""
        text = "如何使用 <Python> 进行 [Web 开发]？！@#"

        title = generator.generate_title(text)

        assert title is not None
        # 特殊字符应被清理
        assert "<" not in title
        assert ">" not in title
        assert "[" not in title
        assert "]" not in title

    def test_long_question(self, generator):
        """测试过长的问句"""
        long_question = "如何在大规模分布式系统中使用 Python 和 Django 框架结合 Redis 缓存和 PostgreSQL 数据库来构建高性能的 Web 应用程序？" * 2

        config = TitleGenerationConfig(max_length=50)
        title = generator.generate_title(long_question, config)

        assert title is not None
        assert len(title) <= 53  # 50 + "..."
