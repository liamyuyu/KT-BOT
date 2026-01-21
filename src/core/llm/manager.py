"""
LLM Model Manager
Epic 1: 本地模型集成与管理
"""

import logging
from typing import Dict, Optional, List
from enum import Enum

from .base import BaseLLM, BaseEmbedding, ModelInfo
from .ollama import OllamaLLM, OllamaEmbedding
from .config import ModelsConfig, ModelConfigLoader
from ...config import settings
from ...constants import (
    SUPPORTED_LLM_MODELS,
    SUPPORTED_EMBEDDING_MODELS,
    DEFAULT_LLM_MODEL,
    DEFAULT_EMBEDDING_MODEL,
)

logger = logging.getLogger(__name__)


class ModelProvider(str, Enum):
    """模型提供商枚举"""
    OLLAMA = "ollama"
    # 未来可扩展: OPENAI, ANTHROPIC, etc.


class LLMManager:
    """
    LLM 模型管理器
    负责模型的创建、缓存和生命周期管理
    """

    def __init__(self):
        """初始化 LLM 管理器"""
        self._llm_cache: Dict[str, BaseLLM] = {}
        self._embedding_cache: Dict[str, BaseEmbedding] = {}
        self.default_provider = ModelProvider.OLLAMA
        self.config = self._load_config()

    def _load_config(self) -> ModelsConfig:
        """
        加载配置：优先级 YAML > ENV

        Returns:
            ModelsConfig: 模型配置对象
        """
        return ModelConfigLoader.load_config()

    def reload_config(self) -> ModelsConfig:
        """
        重新加载配置（支持热加载）

        Returns:
            ModelsConfig: 新的模型配置对象
        """
        logger.info("Reloading models configuration...")
        self.config = self._load_config()
        return self.config

    def get_enabled_llm_models(self) -> List[str]:
        """
        获取启用的 LLM 模型列表

        Returns:
            List[str]: 启用的模型名称列表
        """
        models = self.config.llm.get("models", [])
        return [m["name"] for m in models if m.get("enabled", True)]

    def get_enabled_embedding_models(self) -> List[str]:
        """
        获取启用的 Embedding 模型列表

        Returns:
            List[str]: 启用的模型名称列表
        """
        models = self.config.embedding.get("models", [])
        return [m["name"] for m in models if m.get("enabled", True)]

    def create_llm(
        self,
        model_name: Optional[str] = None,
        provider: ModelProvider = ModelProvider.OLLAMA,
        **kwargs
    ) -> BaseLLM:
        """
        创建或获取 LLM 实例

        Args:
            model_name: 模型名称，默认使用配置中的模型
            provider: 模型提供商
            **kwargs: 额外的配置参数

        Returns:
            BaseLLM: LLM 实例

        Raises:
            ValueError: 不支持的模型或提供商
        """
        model_name = model_name or settings.ollama_model or DEFAULT_LLM_MODEL

        # 检查模型是否支持
        if model_name not in SUPPORTED_LLM_MODELS:
            logger.warning(
                f"Model {model_name} not in supported list: {SUPPORTED_LLM_MODELS}"
            )

        # 使用缓存
        cache_key = f"{provider}:{model_name}"
        if cache_key in self._llm_cache:
            logger.debug(f"Using cached LLM: {cache_key}")
            return self._llm_cache[cache_key]

        # 创建新实例
        if provider == ModelProvider.OLLAMA:
            llm = OllamaLLM(
                model_name=model_name,
                host=settings.ollama_host,
                timeout=settings.ollama_timeout,
                **kwargs
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        # 缓存实例
        self._llm_cache[cache_key] = llm
        logger.info(f"Created LLM: {cache_key}")

        return llm

    def create_embedding(
        self,
        model_name: Optional[str] = None,
        provider: ModelProvider = ModelProvider.OLLAMA,
        **kwargs
    ) -> BaseEmbedding:
        """
        创建或获取 Embedding 实例

        Args:
            model_name: 模型名称，默认使用配置中的模型
            provider: 模型提供商
            **kwargs: 额外的配置参数

        Returns:
            BaseEmbedding: Embedding 实例

        Raises:
            ValueError: 不支持的模型或提供商
        """
        model_name = model_name or settings.ollama_embedding_model or DEFAULT_EMBEDDING_MODEL

        # 检查模型是否支持
        if model_name not in SUPPORTED_EMBEDDING_MODELS:
            logger.warning(
                f"Embedding model {model_name} not in supported list: {SUPPORTED_EMBEDDING_MODELS}"
            )

        # 使用缓存
        cache_key = f"{provider}:{model_name}"
        if cache_key in self._embedding_cache:
            logger.debug(f"Using cached Embedding: {cache_key}")
            return self._embedding_cache[cache_key]

        # 从配置读取 batch_size
        batch_size = 32  # 默认值
        if self.config and self.config.embedding:
            embedding_models = self.config.embedding.get("models", [])
            for model_cfg in embedding_models:
                if model_cfg.get("name") == model_name:
                    batch_size = model_cfg.get("batch_size", 32)
                    break

        # 创建新实例
        if provider == ModelProvider.OLLAMA:
            embedding = OllamaEmbedding(
                model_name=model_name,
                host=settings.ollama_host,
                timeout=settings.ollama_timeout,
                batch_size=batch_size,
                **kwargs
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        # 缓存实例
        self._embedding_cache[cache_key] = embedding
        logger.info(f"Created Embedding: {cache_key}")

        return embedding

    async def health_check_all(self) -> Dict[str, bool]:
        """
        检查所有已缓存模型的健康状态

        Returns:
            Dict[str, bool]: 模型名称 -> 健康状态
        """
        results = {}

        # 检查 LLM 模型
        for cache_key, llm in self._llm_cache.items():
            try:
                is_healthy = await llm.health_check()
                results[f"llm:{cache_key}"] = is_healthy
            except Exception as e:
                logger.error(f"Health check failed for {cache_key}: {e}")
                results[f"llm:{cache_key}"] = False

        # 检查 Embedding 模型
        for cache_key, embedding in self._embedding_cache.items():
            try:
                is_healthy = await embedding.health_check()
                results[f"embedding:{cache_key}"] = is_healthy
            except Exception as e:
                logger.error(f"Health check failed for {cache_key}: {e}")
                results[f"embedding:{cache_key}"] = False

        return results

    async def get_all_model_info(self) -> Dict[str, ModelInfo]:
        """
        获取所有已缓存模型的信息

        Returns:
            Dict[str, ModelInfo]: 模型名称 -> 模型信息
        """
        results = {}

        # 获取 LLM 模型信息
        for cache_key, llm in self._llm_cache.items():
            try:
                model_info = await llm.get_model_info()
                results[f"llm:{cache_key}"] = model_info
            except Exception as e:
                logger.error(f"Failed to get model info for {cache_key}: {e}")

        # 获取 Embedding 模型信息
        for cache_key, embedding in self._embedding_cache.items():
            try:
                model_info = await embedding.get_model_info()
                results[f"embedding:{cache_key}"] = model_info
            except Exception as e:
                logger.error(f"Failed to get model info for {cache_key}: {e}")

        return results

    def get_supported_models(self) -> Dict[str, List[str]]:
        """
        获取支持的模型列表

        Returns:
            Dict[str, List[str]]: 模型类型 -> 模型列表
        """
        return {
            "llm": SUPPORTED_LLM_MODELS,
            "embedding": SUPPORTED_EMBEDDING_MODELS,
        }

    def clear_cache(self):
        """清空模型缓存"""
        self._llm_cache.clear()
        self._embedding_cache.clear()
        logger.info("Model cache cleared")

    async def close_all(self):
        """关闭所有模型连接"""
        # 关闭所有 LLM 连接
        for cache_key, llm in self._llm_cache.items():
            try:
                if hasattr(llm, 'close'):
                    await llm.close()
                logger.info(f"Closed LLM: {cache_key}")
            except Exception as e:
                logger.error(f"Failed to close LLM {cache_key}: {e}")

        # 关闭所有 Embedding 连接
        for cache_key, embedding in self._embedding_cache.items():
            try:
                if hasattr(embedding, 'close'):
                    await embedding.close()
                logger.info(f"Closed Embedding: {cache_key}")
            except Exception as e:
                logger.error(f"Failed to close Embedding {cache_key}: {e}")

        # 清空缓存
        self.clear_cache()


# 全局单例
_manager: Optional[LLMManager] = None


def get_llm_manager() -> LLMManager:
    """
    获取全局 LLM 管理器单例

    Returns:
        LLMManager: LLM 管理器实例
    """
    global _manager
    if _manager is None:
        _manager = LLMManager()
    return _manager
