"""
Unit Tests for LLM Manager
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.core.llm.manager import LLMManager, ModelProvider, get_llm_manager
from src.core.llm.ollama import OllamaLLM, OllamaEmbedding
from src.constants import DEFAULT_LLM_MODEL, DEFAULT_EMBEDDING_MODEL


class TestLLMManager:
    """Test LLM Manager"""

    @pytest.fixture
    def manager(self):
        """Create a fresh manager instance"""
        return LLMManager()

    def test_create_llm_default(self, manager):
        """Test creating LLM with default settings"""
        llm = manager.create_llm()

        assert isinstance(llm, OllamaLLM)
        assert llm.model_name == DEFAULT_LLM_MODEL

    def test_create_llm_custom_model(self, manager):
        """Test creating LLM with custom model"""
        llm = manager.create_llm(model_name="qwen2.5:14b")

        assert isinstance(llm, OllamaLLM)
        assert llm.model_name == "qwen2.5:14b"

    def test_create_llm_caching(self, manager):
        """Test LLM instance caching"""
        llm1 = manager.create_llm(model_name="qwen2.5:7b")
        llm2 = manager.create_llm(model_name="qwen2.5:7b")

        # Should return the same cached instance
        assert llm1 is llm2

    def test_create_llm_different_models(self, manager):
        """Test creating different LLM models"""
        llm1 = manager.create_llm(model_name="qwen2.5:7b")
        llm2 = manager.create_llm(model_name="llama3.1:8b")

        # Should return different instances
        assert llm1 is not llm2
        assert llm1.model_name == "qwen2.5:7b"
        assert llm2.model_name == "llama3.1:8b"

    def test_create_embedding_default(self, manager):
        """Test creating Embedding with default settings"""
        embedding = manager.create_embedding()

        assert isinstance(embedding, OllamaEmbedding)
        assert embedding.model_name == DEFAULT_EMBEDDING_MODEL

    def test_create_embedding_custom_model(self, manager):
        """Test creating Embedding with custom model"""
        embedding = manager.create_embedding(model_name="nomic-embed-text")

        assert isinstance(embedding, OllamaEmbedding)
        assert embedding.model_name == "nomic-embed-text"

    def test_create_embedding_caching(self, manager):
        """Test Embedding instance caching"""
        emb1 = manager.create_embedding(model_name="bge-large-zh")
        emb2 = manager.create_embedding(model_name="bge-large-zh")

        # Should return the same cached instance
        assert emb1 is emb2

    def test_unsupported_provider(self, manager):
        """Test creating LLM with unsupported provider"""
        with pytest.raises(ValueError, match="Unsupported provider"):
            manager.create_llm(provider="openai")  # type: ignore

    @pytest.mark.asyncio
    async def test_health_check_all(self, manager):
        """Test health check for all models"""
        # Create some models
        llm = manager.create_llm(model_name="qwen2.5:7b")
        embedding = manager.create_embedding(model_name="bge-large-zh")

        # Mock health check methods
        llm.health_check = AsyncMock(return_value=True)
        embedding.health_check = AsyncMock(return_value=True)

        results = await manager.health_check_all()

        assert "llm:ollama:qwen2.5:7b" in results
        assert "embedding:ollama:bge-large-zh" in results
        assert results["llm:ollama:qwen2.5:7b"] is True
        assert results["embedding:ollama:bge-large-zh"] is True

    @pytest.mark.asyncio
    async def test_get_all_model_info(self, manager):
        """Test getting all model info"""
        from src.core.llm.base import ModelInfo, ModelType

        # Create a model
        llm = manager.create_llm(model_name="qwen2.5:7b")

        # Mock get_model_info
        mock_info = ModelInfo(
            name="qwen2.5:7b",
            model_type=ModelType.CHAT,
            size="4.7GB"
        )
        llm.get_model_info = AsyncMock(return_value=mock_info)

        results = await manager.get_all_model_info()

        assert "llm:ollama:qwen2.5:7b" in results
        assert results["llm:ollama:qwen2.5:7b"].name == "qwen2.5:7b"

    def test_get_supported_models(self, manager):
        """Test getting supported models"""
        models = manager.get_supported_models()

        assert "llm" in models
        assert "embedding" in models
        assert isinstance(models["llm"], list)
        assert isinstance(models["embedding"], list)
        assert len(models["llm"]) > 0
        assert len(models["embedding"]) > 0

    def test_clear_cache(self, manager):
        """Test clearing model cache"""
        # Create some models
        manager.create_llm(model_name="qwen2.5:7b")
        manager.create_embedding(model_name="bge-large-zh")

        assert len(manager._llm_cache) > 0
        assert len(manager._embedding_cache) > 0

        # Clear cache
        manager.clear_cache()

        assert len(manager._llm_cache) == 0
        assert len(manager._embedding_cache) == 0

    @pytest.mark.asyncio
    async def test_close_all(self, manager):
        """Test closing all model connections"""
        # Create some models
        llm = manager.create_llm(model_name="qwen2.5:7b")
        embedding = manager.create_embedding(model_name="bge-large-zh")

        # Mock close methods
        llm.close = AsyncMock()
        embedding.close = AsyncMock()

        await manager.close_all()

        # Verify close was called
        llm.close.assert_called_once()
        embedding.close.assert_called_once()

        # Verify cache is cleared
        assert len(manager._llm_cache) == 0
        assert len(manager._embedding_cache) == 0

    def test_get_llm_manager_singleton(self):
        """Test global manager singleton"""
        manager1 = get_llm_manager()
        manager2 = get_llm_manager()

        # Should return the same instance
        assert manager1 is manager2
