"""
LLM Module
Epic 1: 本地模型集成与管理
"""

from .base import (
    BaseLLM,
    BaseEmbedding,
    Message,
    GenerateResponse,
    EmbeddingResponse,
    ModelInfo,
    ModelType,
)

from .ollama import (
    OllamaLLM,
    OllamaEmbedding,
)

from .manager import (
    LLMManager,
    ModelProvider,
    get_llm_manager,
)

from .health import (
    LLMHealthChecker,
    HealthStatus,
    get_health_checker,
)

__all__ = [
    # Base classes
    "BaseLLM",
    "BaseEmbedding",
    "Message",
    "GenerateResponse",
    "EmbeddingResponse",
    "ModelInfo",
    "ModelType",
    # Ollama implementations
    "OllamaLLM",
    "OllamaEmbedding",
    # Manager
    "LLMManager",
    "ModelProvider",
    "get_llm_manager",
    # Health
    "LLMHealthChecker",
    "HealthStatus",
    "get_health_checker",
]
