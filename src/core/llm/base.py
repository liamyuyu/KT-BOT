"""
LLM Base Classes
Epic 1: 本地模型集成与管理
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, AsyncIterator, Any
from dataclasses import dataclass
from enum import Enum


class ModelType(str, Enum):
    """模型类型枚举"""
    CHAT = "chat"
    EMBEDDING = "embedding"


@dataclass
class Message:
    """消息数据类"""
    role: str  # system, user, assistant
    content: str


@dataclass
class GenerateResponse:
    """生成响应数据类"""
    content: str
    model: str
    total_duration: Optional[int] = None  # nanoseconds
    load_duration: Optional[int] = None
    prompt_eval_count: Optional[int] = None
    eval_count: Optional[int] = None
    eval_duration: Optional[int] = None


@dataclass
class EmbeddingResponse:
    """Embedding 响应数据类"""
    embedding: List[float]
    model: str


@dataclass
class ModelInfo:
    """模型信息数据类"""
    name: str
    model_type: ModelType
    size: Optional[str] = None
    format: Optional[str] = None
    family: Optional[str] = None
    parameter_size: Optional[str] = None
    quantization_level: Optional[str] = None
    modified_at: Optional[str] = None


class BaseLLM(ABC):
    """
    LLM 基类
    定义所有 LLM 实现必须遵循的接口
    """

    def __init__(self, model_name: str, **kwargs):
        """
        初始化 LLM

        Args:
            model_name: 模型名称
            **kwargs: 额外的配置参数
        """
        self.model_name = model_name
        self.config = kwargs

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> GenerateResponse:
        """
        生成文本（非流式）

        Args:
            prompt: 用户提示
            system: 系统提示
            temperature: 温度参数
            top_p: Top-p 采样参数
            max_tokens: 最大生成 token 数
            **kwargs: 其他参数

        Returns:
            GenerateResponse: 生成响应
        """
        pass

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        生成文本（流式）

        Args:
            prompt: 用户提示
            system: 系统提示
            temperature: 温度参数
            top_p: Top-p 采样参数
            max_tokens: 最大生成 token 数
            **kwargs: 其他参数

        Yields:
            str: 生成的文本片段
        """
        pass

    @abstractmethod
    async def chat(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> GenerateResponse:
        """
        对话生成（非流式）

        Args:
            messages: 消息列表
            temperature: 温度参数
            top_p: Top-p 采样参数
            max_tokens: 最大生成 token 数
            **kwargs: 其他参数

        Returns:
            GenerateResponse: 生成响应
        """
        pass

    @abstractmethod
    async def chat_stream(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        对话生成（流式）

        Args:
            messages: 消息列表
            temperature: 温度参数
            top_p: Top-p 采样参数
            max_tokens: 最大生成 token 数
            **kwargs: 其他参数

        Yields:
            str: 生成的文本片段
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            bool: 是否健康
        """
        pass

    @abstractmethod
    async def get_model_info(self) -> ModelInfo:
        """
        获取模型信息

        Returns:
            ModelInfo: 模型信息
        """
        pass


class BaseEmbedding(ABC):
    """
    Embedding 基类
    定义所有 Embedding 实现必须遵循的接口
    """

    def __init__(self, model_name: str, **kwargs):
        """
        初始化 Embedding

        Args:
            model_name: 模型名称
            **kwargs: 额外的配置参数
        """
        self.model_name = model_name
        self.config = kwargs

    @abstractmethod
    async def embed(self, text: str) -> EmbeddingResponse:
        """
        生成文本的 Embedding

        Args:
            text: 输入文本

        Returns:
            EmbeddingResponse: Embedding 响应
        """
        pass

    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[EmbeddingResponse]:
        """
        批量生成 Embedding

        Args:
            texts: 输入文本列表

        Returns:
            List[EmbeddingResponse]: Embedding 响应列表
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            bool: 是否健康
        """
        pass

    @abstractmethod
    async def get_model_info(self) -> ModelInfo:
        """
        获取模型信息

        Returns:
            ModelInfo: 模型信息
        """
        pass
