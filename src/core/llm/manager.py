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

        # 跟踪当前激活的模型
        self._current_llm_model: Optional[str] = None
        self._current_embedding_model: Optional[str] = None

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

        # 设置为当前模型（如果还没有设置）
        if self._current_llm_model is None:
            self._current_llm_model = model_name

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

        # 设置为当前模型（如果还没有设置）
        if self._current_embedding_model is None:
            self._current_embedding_model = model_name

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

    def get_current_llm_model(self) -> Optional[str]:
        """
        获取当前激活的 LLM 模型

        Returns:
            Optional[str]: 当前模型名称
        """
        return self._current_llm_model

    def get_current_embedding_model(self) -> Optional[str]:
        """
        获取当前激活的 Embedding 模型

        Returns:
            Optional[str]: 当前模型名称
        """
        return self._current_embedding_model

    def switch_llm_model(self, model_name: str, provider: ModelProvider = ModelProvider.OLLAMA) -> BaseLLM:
        """
        切换 LLM 模型

        Args:
            model_name: 新模型名称
            provider: 模型提供商

        Returns:
            BaseLLM: 新的 LLM 实例

        Raises:
            ValueError: 不支持的模型
        """
        if model_name not in SUPPORTED_LLM_MODELS:
            raise ValueError(f"Unsupported model: {model_name}. Supported models: {SUPPORTED_LLM_MODELS}")

        logger.info(f"Switching LLM model from {self._current_llm_model} to {model_name}")

        # 创建或获取新模型实例
        llm = self.create_llm(model_name=model_name, provider=provider)

        # 更新当前模型
        self._current_llm_model = model_name

        logger.info(f"LLM model switched to {model_name}")
        return llm

    def switch_embedding_model(
        self,
        model_name: str,
        provider: ModelProvider = ModelProvider.OLLAMA
    ) -> BaseEmbedding:
        """
        切换 Embedding 模型

        Args:
            model_name: 新模型名称
            provider: 模型提供商

        Returns:
            BaseEmbedding: 新的 Embedding 实例

        Raises:
            ValueError: 不支持的模型
        """
        if model_name not in SUPPORTED_EMBEDDING_MODELS:
            raise ValueError(
                f"Unsupported embedding model: {model_name}. "
                f"Supported models: {SUPPORTED_EMBEDDING_MODELS}"
            )

        logger.info(f"Switching Embedding model from {self._current_embedding_model} to {model_name}")

        # 创建或获取新模型实例
        embedding = self.create_embedding(model_name=model_name, provider=provider)

        # 更新当前模型
        self._current_embedding_model = model_name

        logger.info(f"Embedding model switched to {model_name}")
        return embedding

    async def check_model_health(self, model_name: str, model_type: str = "llm") -> bool:
        """
        检查指定模型的健康状态

        Args:
            model_name: 模型名称
            model_type: 模型类型（llm 或 embedding）

        Returns:
            bool: 是否健康
        """
        cache_key = f"{self.default_provider}:{model_name}"

        try:
            if model_type == "llm":
                if cache_key in self._llm_cache:
                    return await self._llm_cache[cache_key].health_check()
                else:
                    # 尝试创建并检查
                    llm = self.create_llm(model_name=model_name)
                    return await llm.health_check()
            elif model_type == "embedding":
                if cache_key in self._embedding_cache:
                    return await self._embedding_cache[cache_key].health_check()
                else:
                    # 尝试创建并检查
                    embedding = self.create_embedding(model_name=model_name)
                    return await embedding.health_check()
            else:
                raise ValueError(f"Invalid model_type: {model_type}")
        except Exception as e:
            logger.error(f"Health check failed for {model_type}:{model_name}: {e}")
            return False

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
