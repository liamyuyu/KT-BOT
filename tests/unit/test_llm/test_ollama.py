"""
Unit Tests for Ollama Integration
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from src.core.llm.ollama import OllamaLLM, OllamaEmbedding
from src.core.llm.base import Message, GenerateResponse, EmbeddingResponse


class TestOllamaLLM:
    """Test Ollama LLM"""

    @pytest.fixture
    def llm(self):
        """Create an Ollama LLM instance"""
        return OllamaLLM(
            model_name="qwen2.5:7b",
            host="http://localhost:11434"
        )

    @pytest.mark.asyncio
    async def test_generate(self, llm):
        """Test generate method"""
        mock_response = {
            "response": "Hello! How can I help you?",
            "model": "qwen2.5:7b",
            "total_duration": 1000000000,
            "eval_count": 10
        }

        # Mock the HTTP client
        llm.client.post = AsyncMock(
            return_value=MagicMock(
                status_code=200,
                json=lambda: mock_response,
                raise_for_status=lambda: None
            )
        )

        response = await llm.generate(prompt="Hello")

        assert isinstance(response, GenerateResponse)
        assert response.content == "Hello! How can I help you?"
        assert response.model == "qwen2.5:7b"
        assert response.eval_count == 10

    @pytest.mark.asyncio
    async def test_generate_with_system(self, llm):
        """Test generate with system prompt"""
        mock_response = {
            "response": "I am a helpful assistant.",
            "model": "qwen2.5:7b",
        }

        llm.client.post = AsyncMock(
            return_value=MagicMock(
                status_code=200,
                json=lambda: mock_response,
                raise_for_status=lambda: None
            )
        )

        response = await llm.generate(
            prompt="Who are you?",
            system="You are a helpful assistant."
        )

        assert response.content == "I am a helpful assistant."

    @pytest.mark.asyncio
    async def test_chat(self, llm):
        """Test chat method"""
        messages = [
            Message(role="user", content="Hello"),
            Message(role="assistant", content="Hi! How can I help?"),
            Message(role="user", content="Tell me a joke"),
        ]

        mock_response = {
            "message": {"content": "Why did the chicken cross the road?"},
            "model": "qwen2.5:7b",
            "eval_count": 15
        }

        llm.client.post = AsyncMock(
            return_value=MagicMock(
                status_code=200,
                json=lambda: mock_response,
                raise_for_status=lambda: None
            )
        )

        response = await llm.chat(messages=messages)

        assert isinstance(response, GenerateResponse)
        assert "chicken" in response.content.lower()

    @pytest.mark.asyncio
    async def test_generate_stream(self, llm):
        """Test generate_stream method"""
        mock_lines = [
            '{"response": "Hello"}',
            '{"response": " there"}',
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

        chunks = []
        async for chunk in llm.generate_stream(prompt="Hello"):
            chunks.append(chunk)

        assert chunks == ["Hello", " there", "!"]

    @pytest.mark.asyncio
    async def test_health_check_success(self, llm):
        """Test successful health check"""
        llm.client.get = AsyncMock(
            return_value=MagicMock(status_code=200)
        )

        is_healthy = await llm.health_check()

        assert is_healthy is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, llm):
        """Test failed health check"""
        llm.client.get = AsyncMock(
            side_effect=httpx.ConnectError("Connection failed")
        )

        is_healthy = await llm.health_check()

        assert is_healthy is False

    @pytest.mark.asyncio
    async def test_get_model_info(self, llm):
        """Test get_model_info method"""
        mock_response = {
            "size": "4.7GB",
            "modified_at": "2024-01-01T00:00:00Z",
            "details": {
                "format": "gguf",
                "family": "qwen2",
                "parameter_size": "7B",
                "quantization_level": "Q4_0"
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


class TestOllamaEmbedding:
    """Test Ollama Embedding"""

    @pytest.fixture
    def embedding(self):
        """Create an Ollama Embedding instance"""
        return OllamaEmbedding(
            model_name="bge-large-zh",
            host="http://localhost:11434"
        )

    @pytest.mark.asyncio
    async def test_embed(self, embedding):
        """Test embed method"""
        mock_response = {
            "embedding": [0.1, 0.2, 0.3, 0.4, 0.5]
        }

        embedding.client.post = AsyncMock(
            return_value=MagicMock(
                status_code=200,
                json=lambda: mock_response,
                raise_for_status=lambda: None
            )
        )

        response = await embedding.embed(text="Hello world")

        assert isinstance(response, EmbeddingResponse)
        assert response.embedding == [0.1, 0.2, 0.3, 0.4, 0.5]
        assert response.model == "bge-large-zh"

    @pytest.mark.asyncio
    async def test_embed_batch(self, embedding):
        """Test embed_batch method"""
        texts = ["Hello", "World", "Test"]

        mock_embeddings = [
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6],
            [0.7, 0.8, 0.9]
        ]

        call_count = 0

        async def mock_post(*args, **kwargs):
            nonlocal call_count
            result = MagicMock(
                status_code=200,
                json=lambda: {"embedding": mock_embeddings[call_count]},
                raise_for_status=lambda: None
            )
            call_count += 1
            return result

        embedding.client.post = mock_post

        responses = await embedding.embed_batch(texts)

        assert len(responses) == 3
        assert all(isinstance(r, EmbeddingResponse) for r in responses)
        assert responses[0].embedding == [0.1, 0.2, 0.3]
        assert responses[1].embedding == [0.4, 0.5, 0.6]
        assert responses[2].embedding == [0.7, 0.8, 0.9]

    @pytest.mark.asyncio
    async def test_health_check(self, embedding):
        """Test health check"""
        embedding.client.get = AsyncMock(
            return_value=MagicMock(status_code=200)
        )

        is_healthy = await embedding.health_check()

        assert is_healthy is True

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test using Ollama as context manager"""
        async with OllamaLLM(model_name="qwen2.5:7b") as llm:
            assert llm.model_name == "qwen2.5:7b"

        # Client should be closed after exiting context
        # (in real implementation, we'd verify this)
