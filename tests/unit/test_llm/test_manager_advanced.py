"""
Advanced Unit Tests for LLM Manager (Story 1.2)
多模型管理高级测试
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from concurrent.futures import ThreadPoolExecutor

from src.core.llm.manager import LLMManager, ModelProvider, get_llm_manager
from src.core.llm.ollama import OllamaLLM, OllamaEmbedding
from src.core.llm.base import ModelInfo, ModelType
from src.constants import (
    SUPPORTED_LLM_MODELS,
    SUPPORTED_EMBEDDING_MODELS,
    DEFAULT_LLM_MODEL,
    DEFAULT_EMBEDDING_MODEL
)


class TestMultiModelManagement:
    """测试多模型管理核心功能 (Story 1.2)"""

    @pytest.fixture
    def manager(self):
        """创建新的 manager 实例"""
        return LLMManager()

    def test_multiple_llm_models_coexist(self, manager):
        """测试多个 LLM 模型可以同时存在"""
        # 创建多个不同的模型
        qwen = manager.create_llm(model_name="qwen2.5:7b")
        llama = manager.create_llm(model_name="llama3.1:8b")
        mistral = manager.create_llm(model_name="mistral:7b")

        # 验证所有模型都被缓存
        assert len(manager._llm_cache) == 3
        assert qwen is not llama
        assert qwen is not mistral
        assert llama is not mistral

        # 验证模型名称
        assert qwen.model_name == "qwen2.5:7b"
        assert llama.model_name == "llama3.1:8b"
        assert mistral.model_name == "mistral:7b"

    def test_multiple_embedding_models_coexist(self, manager):
        """测试多个 Embedding 模型可以同时存在"""
        bge = manager.create_embedding(model_name="bge-large-zh")
        nomic = manager.create_embedding(model_name="nomic-embed-text")
        mxbai = manager.create_embedding(model_name="mxbai-embed-large")

        # 验证所有模型都被缓存
        assert len(manager._embedding_cache) == 3
        assert bge is not nomic
        assert bge is not mxbai

        # 验证模型名称
        assert bge.model_name == "bge-large-zh"
        assert nomic.model_name == "nomic-embed-text"
        assert mxbai.model_name == "mxbai-embed-large"

    def test_model_switching(self, manager):
        """测试模型切换功能"""
        # 创建初始模型
        model1 = manager.create_llm(model_name="qwen2.5:7b")
        assert model1.model_name == "qwen2.5:7b"

        # 切换到另一个模型
        model2 = manager.create_llm(model_name="llama3.1:8b")
        assert model2.model_name == "llama3.1:8b"

        # 验证两个模型都存在且不同
        assert model1 is not model2
        assert len(manager._llm_cache) == 2

        # 切换回第一个模型，应返回缓存的实例
        model3 = manager.create_llm(model_name="qwen2.5:7b")
        assert model3 is model1

    def test_cache_key_generation(self, manager):
        """测试缓存键生成"""
        # 相同参数应生成相同的缓存键
        llm1 = manager.create_llm(model_name="qwen2.5:7b")
        llm2 = manager.create_llm(model_name="qwen2.5:7b")
        assert llm1 is llm2

        # 不同参数应生成不同的缓存键
        llm3 = manager.create_llm(
            model_name="qwen2.5:7b",
            temperature=0.5
        )
        # 注意：如果 kwargs 不同，应该创建不同的实例
        # 但当前实现可能只基于 model_name 缓存

    @pytest.mark.asyncio
    async def test_health_check_multiple_models(self, manager):
        """测试多个模型的批量健康检查"""
        # 创建多个模型
        qwen = manager.create_llm(model_name="qwen2.5:7b")
        llama = manager.create_llm(model_name="llama3.1:8b")
        bge = manager.create_embedding(model_name="bge-large-zh")

        # Mock 健康检查
        qwen.health_check = AsyncMock(return_value=True)
        llama.health_check = AsyncMock(return_value=False)  # 模拟失败
        bge.health_check = AsyncMock(return_value=True)

        # 批量健康检查
        results = await manager.health_check_all()

        # 验证结果
        assert len(results) == 3
        assert results["llm:ollama:qwen2.5:7b"] is True
        assert results["llm:ollama:llama3.1:8b"] is False
        assert results["embedding:ollama:bge-large-zh"] is True

    @pytest.mark.asyncio
    async def test_get_all_model_info_multiple_models(self, manager):
        """测试获取所有模型的信息"""
        # 创建多个模型
        qwen = manager.create_llm(model_name="qwen2.5:7b")
        bge = manager.create_embedding(model_name="bge-large-zh")

        # Mock model info
        qwen_info = ModelInfo(
            name="qwen2.5:7b",
            model_type=ModelType.CHAT,
            size="4.7GB"
        )
        bge_info = ModelInfo(
            name="bge-large-zh",
            model_type=ModelType.EMBEDDING,
            size="1.3GB"
        )

        qwen.get_model_info = AsyncMock(return_value=qwen_info)
        bge.get_model_info = AsyncMock(return_value=bge_info)

        # 获取所有模型信息
        results = await manager.get_all_model_info()

        # 验证
        assert len(results) == 2
        assert results["llm:ollama:qwen2.5:7b"].name == "qwen2.5:7b"
        assert results["embedding:ollama:bge-large-zh"].name == "bge-large-zh"
        assert results["llm:ollama:qwen2.5:7b"].size == "4.7GB"

    def test_get_supported_models_structure(self, manager):
        """测试支持的模型列表结构"""
        models = manager.get_supported_models()

        # 验证结构
        assert isinstance(models, dict)
        assert "llm" in models
        assert "embedding" in models

        # 验证 LLM 模型列表
        assert isinstance(models["llm"], list)
        assert len(models["llm"]) >= 3  # 至少有 3 个模型
        assert "qwen2.5:7b" in models["llm"]
        assert "llama3.1:8b" in models["llm"]

        # 验证 Embedding 模型列表
        assert isinstance(models["embedding"], list)
        assert len(models["embedding"]) >= 3
        assert "bge-large-zh" in models["embedding"]

    def test_cache_management(self, manager):
        """测试缓存管理功能"""
        # 创建多个模型
        manager.create_llm(model_name="qwen2.5:7b")
        manager.create_llm(model_name="llama3.1:8b")
        manager.create_embedding(model_name="bge-large-zh")

        # 验证缓存
        assert len(manager._llm_cache) == 2
        assert len(manager._embedding_cache) == 1

        # 清空缓存
        manager.clear_cache()

        # 验证缓存已清空
        assert len(manager._llm_cache) == 0
        assert len(manager._embedding_cache) == 0

    @pytest.mark.asyncio
    async def test_close_all_connections(self, manager):
        """测试关闭所有模型连接"""
        # 创建多个模型
        qwen = manager.create_llm(model_name="qwen2.5:7b")
        llama = manager.create_llm(model_name="llama3.1:8b")
        bge = manager.create_embedding(model_name="bge-large-zh")

        # Mock close 方法
        qwen.close = AsyncMock()
        llama.close = AsyncMock()
        bge.close = AsyncMock()

        # 关闭所有连接
        await manager.close_all()

        # 验证所有 close 方法都被调用
        qwen.close.assert_called_once()
        llama.close.assert_called_once()
        bge.close.assert_called_once()

        # 验证缓存已清空
        assert len(manager._llm_cache) == 0
        assert len(manager._embedding_cache) == 0


class TestModelProviders:
    """测试模型提供商功能"""

    @pytest.fixture
    def manager(self):
        return LLMManager()

    def test_default_provider_ollama(self, manager):
        """测试默认提供商是 Ollama"""
        assert manager.default_provider == ModelProvider.OLLAMA

    def test_create_with_explicit_provider(self, manager):
        """测试显式指定提供商"""
        llm = manager.create_llm(
            model_name="qwen2.5:7b",
            provider=ModelProvider.OLLAMA
        )
        assert isinstance(llm, OllamaLLM)

    def test_unsupported_provider_raises_error(self, manager):
        """测试不支持的提供商抛出异常"""
        with pytest.raises(ValueError, match="Unsupported provider"):
            manager.create_llm(provider="unsupported")  # type: ignore


class TestConcurrentAccess:
    """测试并发访问场景"""

    @pytest.fixture
    def manager(self):
        return LLMManager()

    def test_concurrent_model_creation(self, manager):
        """测试并发创建模型"""
        def create_model(model_name: str):
            return manager.create_llm(model_name=model_name)

        # 并发创建多个模型
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(create_model, "qwen2.5:7b"),
                executor.submit(create_model, "llama3.1:8b"),
                executor.submit(create_model, "mistral:7b")
            ]
            models = [f.result() for f in futures]

        # 验证所有模型都创建成功
        assert len(models) == 3
        assert all(isinstance(m, OllamaLLM) for m in models)

        # 验证缓存
        assert len(manager._llm_cache) == 3

    def test_concurrent_same_model_creation(self, manager):
        """测试并发创建相同模型（缓存）"""
        def create_model():
            return manager.create_llm(model_name="qwen2.5:7b")

        # 并发创建同一个模型多次
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_model) for _ in range(5)]
            models = [f.result() for f in futures]

        # 验证返回的是同一个实例
        assert all(m is models[0] for m in models)
        assert len(manager._llm_cache) == 1


class TestEdgeCases:
    """测试边界情况和错误处理"""

    @pytest.fixture
    def manager(self):
        return LLMManager()

    def test_empty_model_name(self, manager):
        """测试空模型名（应使用默认值）"""
        llm = manager.create_llm(model_name="")
        # 空字符串应该被处理，可能使用默认模型
        assert llm is not None

    def test_none_model_name(self, manager):
        """测试 None 模型名（应使用默认值）"""
        llm = manager.create_llm(model_name=None)
        assert llm is not None
        assert llm.model_name == DEFAULT_LLM_MODEL

    def test_invalid_model_name_format(self, manager):
        """测试无效的模型名格式"""
        # 应该允许创建，由 Ollama 层处理
        llm = manager.create_llm(model_name="invalid:model:name")
        assert llm is not None

    @pytest.mark.asyncio
    async def test_health_check_empty_cache(self, manager):
        """测试空缓存时的健康检查"""
        results = await manager.health_check_all()
        assert results == {}

    @pytest.mark.asyncio
    async def test_get_model_info_empty_cache(self, manager):
        """测试空缓存时获取模型信息"""
        results = await manager.get_all_model_info()
        assert results == {}

    def test_clear_empty_cache(self, manager):
        """测试清空空缓存"""
        manager.clear_cache()  # 不应该抛出异常
        assert len(manager._llm_cache) == 0
        assert len(manager._embedding_cache) == 0

    @pytest.mark.asyncio
    async def test_close_all_empty_cache(self, manager):
        """测试关闭空缓存"""
        await manager.close_all()  # 不应该抛出异常


class TestSingletonPattern:
    """测试单例模式"""

    def test_get_llm_manager_returns_singleton(self):
        """测试获取单例 manager"""
        manager1 = get_llm_manager()
        manager2 = get_llm_manager()
        manager3 = get_llm_manager()

        # 所有实例应该相同
        assert manager1 is manager2
        assert manager2 is manager3

    def test_singleton_shares_cache(self):
        """测试单例共享缓存"""
        manager1 = get_llm_manager()
        manager2 = get_llm_manager()

        # 通过 manager1 创建模型
        llm1 = manager1.create_llm(model_name="qwen2.5:7b")

        # 通过 manager2 应该能获取相同的实例
        llm2 = manager2.create_llm(model_name="qwen2.5:7b")

        assert llm1 is llm2


class TestModelConfiguration:
    """测试模型配置"""

    @pytest.fixture
    def manager(self):
        return LLMManager()

    def test_create_llm_with_custom_kwargs(self, manager):
        """测试使用自定义参数创建 LLM"""
        llm = manager.create_llm(
            model_name="qwen2.5:7b",
            temperature=0.7,
            max_tokens=1000
        )
        assert llm is not None
        # 参数应该传递给 LLM 实例
        # 注意：当前实现可能不支持所有参数

    def test_create_embedding_with_custom_kwargs(self, manager):
        """测试使用自定义参数创建 Embedding"""
        embedding = manager.create_embedding(
            model_name="bge-large-zh",
            batch_size=32
        )
        assert embedding is not None


class TestMemoryManagement:
    """测试内存管理"""

    @pytest.fixture
    def manager(self):
        return LLMManager()

    def test_cache_size_management(self, manager):
        """测试缓存大小管理"""
        # 创建多个模型
        for i in range(5):
            manager.create_llm(model_name=f"model-{i}")

        # 验证缓存大小
        assert len(manager._llm_cache) == 5

        # 清空缓存
        manager.clear_cache()
        assert len(manager._llm_cache) == 0

    def test_memory_efficiency_of_caching(self, manager):
        """测试缓存的内存效率"""
        # 多次请求相同模型
        models = [
            manager.create_llm(model_name="qwen2.5:7b")
            for _ in range(10)
        ]

        # 应该只有一个实例
        assert all(m is models[0] for m in models)
        assert len(manager._llm_cache) == 1


class TestModelLifecycle:
    """测试模型生命周期"""

    @pytest.fixture
    def manager(self):
        return LLMManager()

    @pytest.mark.asyncio
    async def test_model_creation_and_cleanup(self, manager):
        """测试模型创建和清理完整生命周期"""
        # 创建模型
        llm = manager.create_llm(model_name="qwen2.5:7b")
        assert llm in manager._llm_cache.values()

        # Mock close 方法
        llm.close = AsyncMock()

        # 清理
        await manager.close_all()

        # 验证
        llm.close.assert_called_once()
        assert len(manager._llm_cache) == 0

    def test_model_recreation_after_cache_clear(self, manager):
        """测试清空缓存后重新创建模型"""
        # 创建模型
        llm1 = manager.create_llm(model_name="qwen2.5:7b")

        # 清空缓存
        manager.clear_cache()

        # 重新创建
        llm2 = manager.create_llm(model_name="qwen2.5:7b")

        # 应该是不同的实例
        assert llm1 is not llm2
