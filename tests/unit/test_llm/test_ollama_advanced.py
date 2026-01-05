"""
Advanced Unit Tests for Ollama Integration (Story 1.1)
Ollama 集成高级测试
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
import json

from src.core.llm.ollama import OllamaLLM, OllamaEmbedding
from src.core.llm.base import Message, GenerateResponse, EmbeddingResponse, ModelInfo


class TestOllamaLLMAdvanced:
    """Ollama LLM 高级测试"""

    @pytest.fixture
    def llm(self):
        """创建 Ollama LLM 实例"""
        return OllamaLLM(
            model_name="qwen2.5:7b",
            host="http://localhost:11434",
            timeout=60
        )

    @pytest.mark.asyncio
    async def test_generate_with_parameters(self, llm):
        """测试带参数的生成"""
        mock_response = {
            "response": "Response with custom params",
            "model": "qwen2.5:7b"
        }

        llm.client.post = AsyncMock(
            return_value=MagicMock(
                status_code=200,
                json=lambda: mock_response,
                raise_for_status=lambda: None
            )
        )

        response = await llm.generate(
            prompt="Test",
            temperature=0.7,
            max_tokens=100,
            top_p=0.9
        )

        assert response.content == "Response with custom params"

    @pytest.mark.asyncio
    async def test_generate_empty_prompt(self, llm):
        """测试空 prompt"""
        mock_response = {
            "response": "",
            "model": "qwen2.5:7b"
        }

        llm.client.post = AsyncMock(
            return_value=MagicMock(
                status_code=200,
                json=lambda: mock_response,
                raise_for_status=lambda: None
            )
        )

        response = await llm.generate(prompt="")
        assert response.content == ""

    @pytest.mark.asyncio
    async def test_chat_with_system_message(self, llm):
        """测试带系统消息的聊天"""
        messages = [
            Message(role="system", content="You are a helpful assistant."),
            Message(role="user", content="Hello")
        ]

        mock_response = {
            "message": {"content": "Hi! How can I assist you?"},
            "model": "qwen2.5:7b"
        }

        llm.client.post = AsyncMock(
            return_value=MagicMock(
                status_code=200,
                json=lambda: mock_response,
                raise_for_status=lambda: None
            )
        )

        response = await llm.chat(messages=messages)
        assert "assist" in response.content.lower()

    @pytest.mark.asyncio
    async def test_chat_empty_messages(self, llm):
        """测试空消息列表"""
        with pytest.raises(Exception):  # 应该抛出异常
            await llm.chat(messages=[])

    @pytest.mark.asyncio
    async def test_generate_stream_partial_response(self, llm):
        """测试流式响应的部分内容"""
        mock_lines = [
            '{"response": "Hello"}',
            '{"response": " "}',
            '{"response": "world"}',
            '{"response": "!"}',
        ]

        async def mock_aiter_lines():
            for line in mock_lines:
                yield line

        mock_response = MagicMock()
        mock_response.aiter_lines = mock_aiter_lines
        mock_response.raise_for_status = lambda: None

        llm.client.stream = MagicMock(
            return_value=MagicMock(
                __aenter__=AsyncMock(return_value=mock_response),
                __aexit__=AsyncMock()
            )
        )

        full_response = ""
        async for chunk in llm.generate_stream(prompt="Test"):
            full_response += chunk

        assert full_response == "Hello world!"

    @pytest.mark.asyncio
    async def test_generate_stream_empty(self, llm):
        """测试空流式响应"""
        async def mock_aiter_lines():
            return
            yield  # pragma: no cover

        mock_response = MagicMock()
        mock_response.aiter_lines = mock_aiter_lines
        mock_response.raise_for_status = lambda: None

        llm.client.stream = MagicMock(
            return_value=MagicMock(
                __aenter__=AsyncMock(return_value=mock_response),
                __aexit__=AsyncMock()
            )
        )

        chunks = []
        async for chunk in llm.generate_stream(prompt="Test"):
            chunks.append(chunk)

        assert chunks == []

    @pytest.mark.asyncio
    async def test_http_error_handling(self, llm):
        """测试 HTTP 错误处理"""
        llm.client.post = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Server error",
                request=MagicMock(),
                response=MagicMock(status_code=500)
            )
        )

        with pytest.raises(Exception):
            await llm.generate(prompt="Test")

    @pytest.mark.asyncio
    async def test_connection_timeout(self, llm):
        """测试连接超时"""
        llm.client.post = AsyncMock(
            side_effect=httpx.TimeoutException("Request timeout")
        )

        with pytest.raises(Exception):
            await llm.generate(prompt="Test")

    @pytest.mark.asyncio
    async def test_get_model_info_detailed(self, llm):
        """测试获取详细模型信息"""
        mock_response = {
            "size": "4.7GB",
            "modified_at": "2024-01-01T00:00:00Z",
            "details": {
                "format": "gguf",
                "family": "qwen2",
                "parameter_size": "7B",
                "quantization_level": "Q4_0"
            },
            "template": "{{.System}}\n{{.Prompt}}",
            "parameters": {
                "num_ctx": 2048,
                "num_predict": -1
            }
        }

        llm.client.post = AsyncMock(
            return_value=MagicMock(
                status_code=200,
                json=lambda: mock_response,
                raise_for_status=lambda: None
            )
        )

        model_info = await llm.get_model_info()

        assert model_info.name == "qwen2.5:7b"
        assert model_info.size == "4.7GB"
        assert model_info.family == "qwen2"
        assert model_info.parameter_size == "7B"

    @pytest.mark.asyncio
    async def test_close(self, llm):
        """测试关闭连接"""
        llm.client.aclose = AsyncMock()
        await llm.close()
        llm.client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager_with_operations(self):
        """测试上下文管理器使用"""
        async with OllamaLLM(model_name="qwen2.5:7b") as llm:
            llm.client.post = AsyncMock(
                return_value=MagicMock(
                    status_code=200,
                    json=lambda: {"response": "Test response"},
                    raise_for_status=lambda: None
                )
            )
            response = await llm.generate(prompt="Test")
            assert response.content == "Test response"


class TestOllamaEmbeddingAdvanced:
    """Ollama Embedding 高级测试"""

    @pytest.fixture
    def embedding(self):
        """创建 Ollama Embedding 实例"""
        return OllamaEmbedding(
            model_name="bge-large-zh",
            host="http://localhost:11434"
        )

    @pytest.mark.asyncio
    async def test_embed_chinese_text(self, embedding):
        """测试中文文本 embedding"""
        mock_response = {
            "embedding": [0.1] * 768  # 模拟 768 维向量
        }

        embedding.client.post = AsyncMock(
            return_value=MagicMock(
                status_code=200,
                json=lambda: mock_response,
                raise_for_status=lambda: None
            )
        )

        response = await embedding.embed(text="这是一段中文文本")

        assert len(response.embedding) == 768
        assert response.model == "bge-large-zh"

    @pytest.mark.asyncio
    async def test_embed_empty_text(self, embedding):
        """测试空文本"""
        mock_response = {
            "embedding": []
        }

        embedding.client.post = AsyncMock(
            return_value=MagicMock(
                status_code=200,
                json=lambda: mock_response,
                raise_for_status=lambda: None
            )
        )

        response = await embedding.embed(text="")
        assert response.embedding == []

    @pytest.mark.asyncio
    async def test_embed_batch_large(self, embedding):
        """测试大批量 embedding"""
        texts = [f"Text {i}" for i in range(100)]

        call_count = 0

        async def mock_post(*args, **kwargs):
            nonlocal call_count
            result = MagicMock(
                status_code=200,
                json=lambda: {"embedding": [call_count * 0.1] * 10},
                raise_for_status=lambda: None
            )
            call_count += 1
            return result

        embedding.client.post = mock_post

        responses = await embedding.embed_batch(texts)

        assert len(responses) == 100
        assert all(len(r.embedding) == 10 for r in responses)

    @pytest.mark.asyncio
    async def test_embed_batch_empty_list(self, embedding):
        """测试空列表批量 embedding"""
        responses = await embedding.embed_batch([])
        assert responses == []

    @pytest.mark.asyncio
    async def test_embed_special_characters(self, embedding):
        """测试特殊字符 embedding"""
        mock_response = {
            "embedding": [0.1, 0.2, 0.3]
        }

        embedding.client.post = AsyncMock(
            return_value=MagicMock(
                status_code=200,
                json=lambda: mock_response,
                raise_for_status=lambda: None
            )
        )

        special_text = "!@#$%^&*()_+-=[]{}|;':\"<>?,./`~"
        response = await embedding.embed(text=special_text)

        assert len(response.embedding) == 3

    @pytest.mark.asyncio
    async def test_embedding_error_handling(self, embedding):
        """测试 embedding 错误处理"""
        embedding.client.post = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Model not found",
                request=MagicMock(),
                response=MagicMock(status_code=404)
            )
        )

        with pytest.raises(Exception):
            await embedding.embed(text="Test")


class TestOllamaConfiguration:
    """Ollama 配置测试"""

    def test_llm_default_configuration(self):
        """测试 LLM 默认配置"""
        llm = OllamaLLM(model_name="qwen2.5:7b")

        assert llm.model_name == "qwen2.5:7b"
        assert llm.host == "http://localhost:11434"
        assert llm.timeout == 300

    def test_llm_custom_configuration(self):
        """测试 LLM 自定义配置"""
        llm = OllamaLLM(
            model_name="llama3.1:8b",
            host="http://custom-host:11434",
            timeout=120
        )

        assert llm.model_name == "llama3.1:8b"
        assert llm.host == "http://custom-host:11434"
        assert llm.timeout == 120

    def test_embedding_default_configuration(self):
        """测试 Embedding 默认配置"""
        embedding = OllamaEmbedding(model_name="bge-large-zh")

        assert embedding.model_name == "bge-large-zh"
        assert embedding.host == "http://localhost:11434"

    def test_embedding_custom_configuration(self):
        """测试 Embedding 自定义配置"""
        embedding = OllamaEmbedding(
            model_name="nomic-embed-text",
            host="http://custom-host:11434"
        )

        assert embedding.model_name == "nomic-embed-text"
        assert embedding.host == "http://custom-host:11434"


class TestOllamaPerformance:
    """Ollama 性能测试"""

    @pytest.fixture
    def llm(self):
        return OllamaLLM(model_name="qwen2.5:7b")

    @pytest.mark.asyncio
    async def test_generate_response_time(self, llm):
        """测试生成响应时间"""
        import time

        mock_response = {
            "response": "Quick response",
            "model": "qwen2.5:7b",
            "total_duration": 500000000,  # 0.5 seconds in nanoseconds
            "prompt_eval_duration": 100000000,
            "eval_duration": 400000000
        }

        llm.client.post = AsyncMock(
            return_value=MagicMock(
                status_code=200,
                json=lambda: mock_response,
                raise_for_status=lambda: None
            )
        )

        start = time.time()
        response = await llm.generate(prompt="Test")
        end = time.time()

        # Mock调用应该很快
        assert end - start < 1.0  # 应该在1秒内完成
        assert response.total_duration == 500000000

    @pytest.mark.asyncio
    async def test_concurrent_generation(self, llm):
        """测试并发生成"""
        import asyncio

        mock_response = {
            "response": "Concurrent response",
            "model": "qwen2.5:7b"
        }

        llm.client.post = AsyncMock(
            return_value=MagicMock(
                status_code=200,
                json=lambda: mock_response,
                raise_for_status=lambda: None
            )
        )

        # 并发执行多个请求
        tasks = [llm.generate(prompt=f"Test {i}") for i in range(5)]
        responses = await asyncio.gather(*tasks)

        assert len(responses) == 5
        assert all(r.content == "Concurrent response" for r in responses)


class TestOllamaResponseParsing:
    """Ollama 响应解析测试"""

    @pytest.fixture
    def llm(self):
        return OllamaLLM(model_name="qwen2.5:7b")

    @pytest.mark.asyncio
    async def test_parse_response_with_metadata(self, llm):
        """测试解析带元数据的响应"""
        mock_response = {
            "response": "Test response",
            "model": "qwen2.5:7b",
            "created_at": "2024-01-01T00:00:00Z",
            "done": True,
            "total_duration": 1000000000,
            "load_duration": 100000000,
            "prompt_eval_count": 10,
            "prompt_eval_duration": 200000000,
            "eval_count": 20,
            "eval_duration": 700000000
        }

        llm.client.post = AsyncMock(
            return_value=MagicMock(
                status_code=200,
                json=lambda: mock_response,
                raise_for_status=lambda: None
            )
        )

        response = await llm.generate(prompt="Test")

        assert response.content == "Test response"
        assert response.model == "qwen2.5:7b"
        assert response.total_duration == 1000000000
        assert response.eval_count == 20

    @pytest.mark.asyncio
    async def test_parse_minimal_response(self, llm):
        """测试解析最小响应"""
        mock_response = {
            "response": "Minimal",
            "model": "qwen2.5:7b"
        }

        llm.client.post = AsyncMock(
            return_value=MagicMock(
                status_code=200,
                json=lambda: mock_response,
                raise_for_status=lambda: None
            )
        )

        response = await llm.generate(prompt="Test")

        assert response.content == "Minimal"
        assert response.model == "qwen2.5:7b"
        # 可选字段应该有默认值
        assert response.total_duration is None or response.total_duration == 0
