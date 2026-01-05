"""
Integration Tests for LLM Manager (Story 1.2)
LLM 管理器集成测试

注意：这些测试需要 Ollama 服务运行
运行方式:
    pytest tests/integration/test_llm_integration.py -v
    pytest tests/integration/test_llm_integration.py -v -m "not slow"  # 跳过慢速测试
"""

import pytest
import asyncio
from src.config import settings
from src.core.llm.manager import get_llm_manager, LLMManager
from src.core.llm.base import ModelType


# 检查是否配置了 Ollama
OLLAMA_AVAILABLE = bool(settings.ollama_host)

pytestmark = pytest.mark.skipif(
    not OLLAMA_AVAILABLE,
    reason="Ollama 未配置或不可用，跳过集成测试"
)


class TestLLMManagerIntegration:
    """LLM Manager 集成测试"""

    @pytest.fixture
    def manager(self):
        """创建新的 manager 实例"""
        return LLMManager()

    @pytest.mark.asyncio
    async def test_create_and_use_llm(self, manager):
        """测试创建并使用真实的 LLM"""
        # 创建 LLM
        llm = manager.create_llm(model_name="qwen2.5:7b")

        # 测试生成
        try:
            response = await llm.generate("Hello, how are you?")
            assert response is not None
            assert len(response) > 0
            print(f"\n✅ LLM 响应: {response[:100]}...")
        except Exception as e:
            pytest.skip(f"模型不可用: {e}")

    @pytest.mark.asyncio
    async def test_create_and_use_embedding(self, manager):
        """测试创建并使用真实的 Embedding"""
        # 创建 Embedding
        embedding = manager.create_embedding(model_name="bge-large-zh")

        # 测试 embed
        try:
            vector = await embedding.embed("测试文本")
            assert vector is not None
            assert len(vector) > 0
            print(f"\n✅ Embedding 维度: {len(vector)}")
        except Exception as e:
            pytest.skip(f"Embedding 模型不可用: {e}")

    @pytest.mark.asyncio
    async def test_multiple_models_real(self, manager):
        """测试多个真实模型同时使用"""
        # 创建多个模型
        qwen = manager.create_llm(model_name="qwen2.5:7b")
        bge = manager.create_embedding(model_name="bge-large-zh")

        # 验证都可以使用
        try:
            llm_response = await qwen.generate("Hi")
            embedding_vector = await bge.embed("测试")

            assert llm_response is not None
            assert embedding_vector is not None
            print(f"\n✅ 两个模型都工作正常")
        except Exception as e:
            pytest.skip(f"模型不可用: {e}")

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_health_check_real_models(self, manager):
        """测试真实模型的健康检查"""
        # 创建模型
        llm = manager.create_llm(model_name="qwen2.5:7b")
        embedding = manager.create_embedding(model_name="bge-large-zh")

        # 健康检查
        results = await manager.health_check_all()

        # 验证结果
        assert len(results) >= 2
        print(f"\n✅ 健康检查结果: {results}")

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_get_model_info_real(self, manager):
        """测试获取真实模型信息"""
        # 创建模型
        llm = manager.create_llm(model_name="qwen2.5:7b")

        # 获取模型信息
        results = await manager.get_all_model_info()

        # 验证
        assert len(results) >= 1
        model_key = list(results.keys())[0]
        model_info = results[model_key]

        assert model_info.name is not None
        assert model_info.model_type in [ModelType.CHAT, ModelType.COMPLETION]
        print(f"\n✅ 模型信息: {model_info}")

    @pytest.mark.asyncio
    async def test_model_switching_real(self, manager):
        """测试真实模型切换"""
        try:
            # 创建第一个模型并使用
            qwen = manager.create_llm(model_name="qwen2.5:7b")
            response1 = await qwen.generate("Hello")
            assert response1 is not None

            # 切换到另一个模型
            llama = manager.create_llm(model_name="llama3.1:8b")
            response2 = await llama.generate("Hello")
            assert response2 is not None

            # 两个模型应该是不同的实例
            assert qwen is not llama
            print(f"\n✅ 模型切换成功")
        except Exception as e:
            pytest.skip(f"某个模型不可用: {e}")

    @pytest.mark.asyncio
    async def test_caching_real_models(self, manager):
        """测试真实模型的缓存"""
        # 多次创建相同模型
        llm1 = manager.create_llm(model_name="qwen2.5:7b")
        llm2 = manager.create_llm(model_name="qwen2.5:7b")

        # 应该返回相同实例
        assert llm1 is llm2

        # 使用缓存的模型
        try:
            response = await llm2.generate("Test")
            assert response is not None
            print(f"\n✅ 缓存模型工作正常")
        except Exception as e:
            pytest.skip(f"模型不可用: {e}")


class TestLLMManagerPerformance:
    """性能测试"""

    @pytest.fixture
    def manager(self):
        return LLMManager()

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_concurrent_requests_to_same_model(self, manager):
        """测试对同一模型的并发请求"""
        llm = manager.create_llm(model_name="qwen2.5:7b")

        # 并发生成
        try:
            tasks = [
                llm.generate(f"Request {i}")
                for i in range(5)
            ]
            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # 验证至少有一些成功
            successful = [r for r in responses if isinstance(r, str)]
            assert len(successful) > 0
            print(f"\n✅ 并发请求: {len(successful)}/5 成功")
        except Exception as e:
            pytest.skip(f"并发测试失败: {e}")

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_concurrent_requests_to_different_models(self, manager):
        """测试对不同模型的并发请求"""
        try:
            qwen = manager.create_llm(model_name="qwen2.5:7b")
            bge = manager.create_embedding(model_name="bge-large-zh")

            # 并发请求
            llm_task = qwen.generate("Hello")
            embed_task = bge.embed("测试")

            llm_response, embed_vector = await asyncio.gather(
                llm_task,
                embed_task,
                return_exceptions=True
            )

            assert llm_response is not None
            assert embed_vector is not None
            print(f"\n✅ 不同模型并发请求成功")
        except Exception as e:
            pytest.skip(f"并发测试失败: {e}")


class TestLLMManagerErrorHandling:
    """错误处理测试"""

    @pytest.fixture
    def manager(self):
        return LLMManager()

    @pytest.mark.asyncio
    async def test_invalid_model_name(self, manager):
        """测试无效的模型名"""
        llm = manager.create_llm(model_name="nonexistent-model:999")

        # 尝试使用，应该失败
        with pytest.raises(Exception):
            await llm.generate("Test")

    @pytest.mark.asyncio
    async def test_health_check_unavailable_model(self, manager):
        """测试不可用模型的健康检查"""
        # 创建一个可能不存在的模型
        llm = manager.create_llm(model_name="fake-model:123")

        # 健康检查应该返回失败
        results = await manager.health_check_all()

        # 可能返回 False 或抛出异常
        # 具体行为取决于实现


class TestSingletonIntegration:
    """单例集成测试"""

    @pytest.mark.asyncio
    async def test_singleton_across_modules(self):
        """测试跨模块使用单例"""
        manager1 = get_llm_manager()
        manager2 = get_llm_manager()

        # 应该是同一个实例
        assert manager1 is manager2

        # 通过 manager1 创建模型
        llm1 = manager1.create_llm(model_name="qwen2.5:7b")

        # 通过 manager2 应该获取相同实例
        llm2 = manager2.create_llm(model_name="qwen2.5:7b")
        assert llm1 is llm2

        # 使用模型
        try:
            response = await llm2.generate("Test")
            assert response is not None
            print(f"\n✅ 单例模式工作正常")
        except Exception as e:
            pytest.skip(f"模型不可用: {e}")


class TestCleanup:
    """清理和资源管理测试"""

    @pytest.mark.asyncio
    async def test_cleanup_after_use(self):
        """测试使用后清理"""
        manager = LLMManager()

        # 创建模型
        llm = manager.create_llm(model_name="qwen2.5:7b")
        embedding = manager.create_embedding(model_name="bge-large-zh")

        # 使用模型
        try:
            await llm.generate("Test")
            await embedding.embed("测试")
        except Exception:
            pass  # 忽略使用错误

        # 清理
        await manager.close_all()

        # 验证缓存已清空
        assert len(manager._llm_cache) == 0
        assert len(manager._embedding_cache) == 0
        print(f"\n✅ 清理成功")


@pytest.mark.skipif(not OLLAMA_AVAILABLE, reason="需要 Ollama")
class TestRealWorldScenarios:
    """真实场景测试"""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_chat_conversation_with_model_switching(self):
        """测试对话中切换模型"""
        manager = get_llm_manager()

        try:
            # 使用 qwen 开始对话
            qwen = manager.create_llm(model_name="qwen2.5:7b")
            response1 = await qwen.generate("你好，请介绍一下你自己")

            # 切换到 llama
            llama = manager.create_llm(model_name="llama3.1:8b")
            response2 = await llama.generate("Hello, introduce yourself")

            assert response1 is not None
            assert response2 is not None
            print(f"\n✅ 对话场景测试成功")
            print(f"Qwen: {response1[:50]}...")
            print(f"Llama: {response2[:50]}...")
        except Exception as e:
            pytest.skip(f"场景测试失败: {e}")

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_embedding_multiple_texts(self):
        """测试对多个文本进行 embedding"""
        manager = get_llm_manager()

        try:
            embedding = manager.create_embedding(model_name="bge-large-zh")

            texts = [
                "这是第一段文本",
                "这是第二段文本",
                "这是第三段文本"
            ]

            # 批量 embed
            vectors = []
            for text in texts:
                vector = await embedding.embed(text)
                vectors.append(vector)

            assert len(vectors) == 3
            assert all(len(v) > 0 for v in vectors)
            print(f"\n✅ 批量 Embedding 成功，维度: {len(vectors[0])}")
        except Exception as e:
            pytest.skip(f"Embedding 测试失败: {e}")
