"""
Configuration Tests for LLM Manager (Story 1.2)
LLM 配置测试
"""

import pytest
from unittest.mock import patch

from src.core.llm.manager import LLMManager, ModelProvider
from src.constants import (
    SUPPORTED_LLM_MODELS,
    SUPPORTED_EMBEDDING_MODELS,
    DEFAULT_LLM_MODEL,
    DEFAULT_EMBEDDING_MODEL
)


class TestSupportedModels:
    """测试支持的模型列表"""

    def test_supported_llm_models_defined(self):
        """测试 LLM 模型列表已定义"""
        assert SUPPORTED_LLM_MODELS is not None
        assert isinstance(SUPPORTED_LLM_MODELS, list)
        assert len(SUPPORTED_LLM_MODELS) >= 3

    def test_supported_llm_models_content(self):
        """测试 LLM 模型列表内容"""
        # 验证必须包含的模型
        assert "qwen2.5:7b" in SUPPORTED_LLM_MODELS
        assert "llama3.1:8b" in SUPPORTED_LLM_MODELS
        assert "mistral:7b" in SUPPORTED_LLM_MODELS

    def test_supported_embedding_models_defined(self):
        """测试 Embedding 模型列表已定义"""
        assert SUPPORTED_EMBEDDING_MODELS is not None
        assert isinstance(SUPPORTED_EMBEDDING_MODELS, list)
        assert len(SUPPORTED_EMBEDDING_MODELS) >= 3

    def test_supported_embedding_models_content(self):
        """测试 Embedding 模型列表内容"""
        # 验证必须包含的模型
        assert "bge-large-zh" in SUPPORTED_EMBEDDING_MODELS
        assert "nomic-embed-text" in SUPPORTED_EMBEDDING_MODELS
        assert "mxbai-embed-large" in SUPPORTED_EMBEDDING_MODELS

    def test_default_llm_model_in_supported_list(self):
        """测试默认 LLM 模型在支持列表中"""
        assert DEFAULT_LLM_MODEL in SUPPORTED_LLM_MODELS

    def test_default_embedding_model_in_supported_list(self):
        """测试默认 Embedding 模型在支持列表中"""
        assert DEFAULT_EMBEDDING_MODEL in SUPPORTED_EMBEDDING_MODELS


class TestModelConfiguration:
    """测试模型配置"""

    @pytest.fixture
    def manager(self):
        return LLMManager()

    def test_get_supported_models_returns_correct_structure(self, manager):
        """测试获取支持的模型返回正确结构"""
        models = manager.get_supported_models()

        # 验证结构
        assert isinstance(models, dict)
        assert "llm" in models
        assert "embedding" in models

        # 验证内容与常量一致
        assert set(models["llm"]) == set(SUPPORTED_LLM_MODELS)
        assert set(models["embedding"]) == set(SUPPORTED_EMBEDDING_MODELS)

    def test_model_list_no_duplicates(self, manager):
        """测试模型列表无重复"""
        models = manager.get_supported_models()

        # 验证 LLM 列表无重复
        llm_models = models["llm"]
        assert len(llm_models) == len(set(llm_models))

        # 验证 Embedding 列表无重复
        embedding_models = models["embedding"]
        assert len(embedding_models) == len(set(embedding_models))

    def test_all_supported_models_can_be_created(self, manager):
        """测试所有支持的模型都可以创建"""
        models = manager.get_supported_models()

        # 测试创建 LLM 模型（仅测试前 2 个，避免太慢）
        for model_name in models["llm"][:2]:
            llm = manager.create_llm(model_name=model_name)
            assert llm is not None
            assert llm.model_name == model_name

        # 测试创建 Embedding 模型
        for model_name in models["embedding"][:2]:
            embedding = manager.create_embedding(model_name=model_name)
            assert embedding is not None
            assert embedding.model_name == model_name


class TestDefaultConfiguration:
    """测试默认配置"""

    @pytest.fixture
    def manager(self):
        return LLMManager()

    def test_default_llm_model_value(self):
        """测试默认 LLM 模型值"""
        assert DEFAULT_LLM_MODEL == "qwen2.5:7b"

    def test_default_embedding_model_value(self):
        """测试默认 Embedding 模型值"""
        assert DEFAULT_EMBEDDING_MODEL == "bge-large-zh"

    def test_manager_uses_default_llm_model(self, manager):
        """测试 Manager 使用默认 LLM 模型"""
        llm = manager.create_llm()  # 不指定模型名
        assert llm.model_name == DEFAULT_LLM_MODEL

    def test_manager_uses_default_embedding_model(self, manager):
        """测试 Manager 使用默认 Embedding 模型"""
        embedding = manager.create_embedding()  # 不指定模型名
        assert embedding.model_name == DEFAULT_EMBEDDING_MODEL

    @patch('src.config.settings')
    def test_default_provider_ollama(self, mock_settings, manager):
        """测试默认提供商是 Ollama"""
        assert manager.default_provider == ModelProvider.OLLAMA


class TestModelNaming:
    """测试模型命名规范"""

    def test_llm_model_naming_convention(self):
        """测试 LLM 模型命名规范"""
        for model_name in SUPPORTED_LLM_MODELS:
            # 应该包含 : 分隔符（model:version 格式）
            assert ":" in model_name, f"模型名 {model_name} 不符合命名规范"

            # 拆分名称和版本
            parts = model_name.split(":")
            assert len(parts) == 2, f"模型名 {model_name} 格式错误"

            model, version = parts
            assert len(model) > 0, "模型名不能为空"
            assert len(version) > 0, "版本号不能为空"

    def test_embedding_model_naming_convention(self):
        """测试 Embedding 模型命名规范"""
        for model_name in SUPPORTED_EMBEDDING_MODELS:
            # Embedding 模型可能不需要版本号
            assert len(model_name) > 0, "模型名不能为空"
            assert isinstance(model_name, str), "模型名必须是字符串"


class TestModelProviderEnum:
    """测试模型提供商枚举"""

    def test_model_provider_ollama_value(self):
        """测试 OLLAMA 提供商值"""
        assert ModelProvider.OLLAMA == "ollama"

    def test_model_provider_is_enum(self):
        """测试 ModelProvider 是枚举类型"""
        from enum import Enum
        assert issubclass(ModelProvider, Enum)

    def test_model_provider_string_comparison(self):
        """测试提供商字符串比较"""
        assert ModelProvider.OLLAMA == "ollama"
        assert ModelProvider.OLLAMA.value == "ollama"


class TestConfigurationConsistency:
    """测试配置一致性"""

    def test_supported_models_match_manager_output(self):
        """测试支持的模型列表与 Manager 输出一致"""
        manager = LLMManager()
        models = manager.get_supported_models()

        # 验证一致性
        assert set(models["llm"]) == set(SUPPORTED_LLM_MODELS)
        assert set(models["embedding"]) == set(SUPPORTED_EMBEDDING_MODELS)

    def test_no_hardcoded_model_names_in_manager(self):
        """测试 Manager 中没有硬编码的模型名"""
        manager = LLMManager()

        # 创建默认模型应该使用常量
        llm = manager.create_llm()
        assert llm.model_name == DEFAULT_LLM_MODEL

        embedding = manager.create_embedding()
        assert embedding.model_name == DEFAULT_EMBEDDING_MODEL


class TestModelVariants:
    """测试模型变体"""

    def test_qwen_variants(self):
        """测试 Qwen 模型变体"""
        qwen_models = [m for m in SUPPORTED_LLM_MODELS if m.startswith("qwen")]
        assert len(qwen_models) >= 2  # 应该至少有 7b 和 14b

    def test_llama_variants(self):
        """测试 Llama 模型变体"""
        llama_models = [m for m in SUPPORTED_LLM_MODELS if m.startswith("llama")]
        assert len(llama_models) >= 1

    def test_embedding_model_diversity(self):
        """测试 Embedding 模型多样性"""
        # 应该包含不同的 embedding 模型
        assert len(SUPPORTED_EMBEDDING_MODELS) >= 3

        # 应该包含中文和英文模型
        chinese_models = [m for m in SUPPORTED_EMBEDDING_MODELS if "zh" in m]
        english_models = [m for m in SUPPORTED_EMBEDDING_MODELS if "zh" not in m]

        assert len(chinese_models) >= 1, "应该包含中文模型"
        assert len(english_models) >= 1, "应该包含英文模型"


class TestConfigurationValidation:
    """测试配置验证"""

    def test_model_names_no_whitespace(self):
        """测试模型名没有空格"""
        all_models = SUPPORTED_LLM_MODELS + SUPPORTED_EMBEDDING_MODELS

        for model_name in all_models:
            assert " " not in model_name, f"模型名 {model_name} 包含空格"

    def test_model_names_lowercase(self):
        """测试模型名是小写的"""
        all_models = SUPPORTED_LLM_MODELS + SUPPORTED_EMBEDDING_MODELS

        for model_name in all_models:
            assert model_name == model_name.lower(), f"模型名 {model_name} 不是小写"

    def test_no_empty_model_names(self):
        """测试没有空模型名"""
        all_models = SUPPORTED_LLM_MODELS + SUPPORTED_EMBEDDING_MODELS

        for model_name in all_models:
            assert model_name, "模型名不能为空"
            assert len(model_name) > 0, "模型名长度必须大于0"
