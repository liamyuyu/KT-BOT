"""
Ollama LLM Integration
Epic 1: 本地模型集成与管理
"""

import json
import logging
from typing import List, Optional, AsyncIterator, Dict, Any

import httpx

from .base import (
    BaseLLM,
    BaseEmbedding,
    Message,
    GenerateResponse,
    EmbeddingResponse,
    ModelInfo,
    ModelType,
)
from ...config import settings

logger = logging.getLogger(__name__)


class OllamaLLM(BaseLLM):
    """
    Ollama LLM 实现
    支持本地部署的 Ollama 模型
    """

    def __init__(
        self,
        model_name: str,
        host: Optional[str] = None,
        timeout: int = 300,
        **kwargs
    ):
        """
        初始化 Ollama LLM

        Args:
            model_name: 模型名称
            host: Ollama 服务地址
            timeout: 请求超时时间（秒）
            **kwargs: 其他配置参数
        """
        super().__init__(model_name, **kwargs)
        self.host = host or settings.ollama_host
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> GenerateResponse:
        """生成文本（非流式）"""
        url = f"{self.host}/api/generate"

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": top_p,
            }
        }

        if system:
            payload["system"] = system

        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        # Add any additional options from kwargs
        payload["options"].update(kwargs)

        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

            return GenerateResponse(
                content=data.get("response", ""),
                model=data.get("model", self.model_name),
                total_duration=data.get("total_duration"),
                load_duration=data.get("load_duration"),
                prompt_eval_count=data.get("prompt_eval_count"),
                eval_count=data.get("eval_count"),
                eval_duration=data.get("eval_duration"),
            )
        except httpx.HTTPError as e:
            logger.error(f"Ollama generate error: {e}")
            raise

    async def generate_stream(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """生成文本（流式）"""
        url = f"{self.host}/api/generate"

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
                "top_p": top_p,
            }
        }

        if system:
            payload["system"] = system

        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        payload["options"].update(kwargs)

        try:
            async with self.client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]
        except httpx.HTTPError as e:
            logger.error(f"Ollama stream error: {e}")
            raise

    async def chat(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> GenerateResponse:
        """对话生成（非流式）"""
        url = f"{self.host}/api/chat"

        payload = {
            "model": self.model_name,
            "messages": [{"role": msg.role, "content": msg.content} for msg in messages],
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": top_p,
            }
        }

        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        payload["options"].update(kwargs)

        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

            message = data.get("message", {})
            return GenerateResponse(
                content=message.get("content", ""),
                model=data.get("model", self.model_name),
                total_duration=data.get("total_duration"),
                load_duration=data.get("load_duration"),
                prompt_eval_count=data.get("prompt_eval_count"),
                eval_count=data.get("eval_count"),
                eval_duration=data.get("eval_duration"),
            )
        except httpx.HTTPError as e:
            logger.error(f"Ollama chat error: {e}")
            raise

    async def chat_stream(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """对话生成（流式）"""
        url = f"{self.host}/api/chat"

        payload = {
            "model": self.model_name,
            "messages": [{"role": msg.role, "content": msg.content} for msg in messages],
            "stream": True,
            "options": {
                "temperature": temperature,
                "top_p": top_p,
            }
        }

        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        payload["options"].update(kwargs)

        try:
            async with self.client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            logger.info(f"Ollama response data: {data}")
                            message = data.get("message", {})
                            logger.info(f"Message type: {type(message)}, message: {message}")
                            if "content" in message:
                                content = message["content"]
                                logger.info(f"Yielding chunk: type={type(content)}, value={repr(content[:50] if len(content) > 50 else content)}")
                                yield content
                        except Exception as e:
                            logger.error(f"Error processing line: {line}, error: {e}", exc_info=True)
                            raise
        except httpx.HTTPError as e:
            logger.error(f"Ollama chat stream error: {e}")
            raise

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            url = f"{self.host}/api/version"
            response = await self.client.get(url)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False

    async def get_model_info(self) -> ModelInfo:
        """获取模型信息"""
        try:
            url = f"{self.host}/api/show"
            response = await self.client.post(
                url,
                json={"name": self.model_name}
            )
            response.raise_for_status()
            data = response.json()

            # Parse model details
            details = data.get("details", {})

            return ModelInfo(
                name=self.model_name,
                model_type=ModelType.CHAT,
                size=data.get("size"),
                format=details.get("format"),
                family=details.get("family"),
                parameter_size=details.get("parameter_size"),
                quantization_level=details.get("quantization_level"),
                modified_at=data.get("modified_at"),
            )
        except httpx.HTTPError as e:
            logger.error(f"Failed to get model info: {e}")
            raise

    async def close(self):
        """关闭连接"""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


class OllamaEmbedding(BaseEmbedding):
    """
    Ollama Embedding 实现
    支持本地部署的 Ollama Embedding 模型
    """

    def __init__(
        self,
        model_name: str,
        host: Optional[str] = None,
        timeout: int = 300,
        batch_size: int = 32,
        **kwargs
    ):
        """
        初始化 Ollama Embedding

        Args:
            model_name: 模型名称
            host: Ollama 服务地址
            timeout: 请求超时时间（秒）
            batch_size: 批处理大小
            **kwargs: 其他配置参数
        """
        super().__init__(model_name, **kwargs)
        self.host = host or settings.ollama_host
        self.timeout = timeout
        self.batch_size = batch_size
        self.client = httpx.AsyncClient(timeout=timeout)

    async def embed(self, text: str) -> EmbeddingResponse:
        """生成文本的 Embedding"""
        url = f"{self.host}/api/embed"

        payload = {
            "model": self.model_name,
            "input": text,
        }

        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

            # Ollama API returns "embeddings" as an array, we take the first one
            embeddings = data.get("embeddings", [])
            embedding = embeddings[0] if embeddings else []

            return EmbeddingResponse(
                embedding=embedding,
                model=self.model_name,
            )
        except httpx.HTTPError as e:
            logger.error(f"Ollama embedding error: {e}")
            raise

    async def embed_batch(
        self,
        texts: List[str],
        batch_size: Optional[int] = None
    ) -> List[EmbeddingResponse]:
        """
        批量生成 Embedding（并发优化）

        Args:
            texts: 文本列表
            batch_size: 批次大小，默认从配置读取

        Returns:
            List[EmbeddingResponse]: Embedding 响应列表
        """
        import asyncio

        # 使用配置的批次大小
        if batch_size is None:
            batch_size = self.batch_size

        # 空列表直接返回
        if not texts:
            return []

        # 小批量：直接并发
        if len(texts) < 10:
            tasks = [self.embed(text) for text in texts]
            return await asyncio.gather(*tasks)

        # 大批量：分批并发
        results = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            tasks = [self.embed(text) for text in batch]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)

            # 添加小延迟避免过载
            if i + batch_size < len(texts):
                await asyncio.sleep(0.1)

        return results

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            url = f"{self.host}/api/version"
            response = await self.client.get(url)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False

    async def get_model_info(self) -> ModelInfo:
        """获取模型信息"""
        try:
            url = f"{self.host}/api/show"
            response = await self.client.post(
                url,
                json={"name": self.model_name}
            )
            response.raise_for_status()
            data = response.json()

            details = data.get("details", {})

            return ModelInfo(
                name=self.model_name,
                model_type=ModelType.EMBEDDING,
                size=data.get("size"),
                format=details.get("format"),
                family=details.get("family"),
                parameter_size=details.get("parameter_size"),
                quantization_level=details.get("quantization_level"),
                modified_at=data.get("modified_at"),
            )
        except httpx.HTTPError as e:
            logger.error(f"Failed to get model info: {e}")
            raise

    async def close(self):
        """关闭连接"""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
