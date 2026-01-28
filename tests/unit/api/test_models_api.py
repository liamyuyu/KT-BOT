"""
模型管理 API 测试
Story 4.6: 模型切换 UI
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient

from src.api.main import app
from src.core.llm.manager import LLMManager


# ========================================================================
# Fixtures
# ========================================================================

@pytest.fixture
def mock_llm_manager():
    """模拟 LLM 管理器"""
    manager = Mock(spec=LLMManager)
    manager.get_current_llm_model = Mock(return_value="qwen2.5:7b")
    manager.get_current_embedding_model = Mock(return_value="nomic-embed-text")
    manager.switch_llm_model = Mock()
    manager.switch_embedding_model = Mock()
    manager.check_model_health = AsyncMock(return_value=True)
    return manager


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


# ========================================================================
# GET /api/v1/models/list Tests
# ========================================================================

class TestListModelsAPI:
    """测试模型列表 API"""

    def test_list_models_success(self, client, mock_llm_manager):
        """测试成功获取模型列表"""
        with patch("src.api.routes.models.get_llm_manager", return_value=mock_llm_manager):
            response = client.get("/api/v1/models/list")

            assert response.status_code == 200
            data = response.json()

            assert "data" in data
            assert "models" in data["data"]
            assert "current" in data["data"]

            # 验证模型列表
            assert "llm" in data["data"]["models"]
            assert "embedding" in data["data"]["models"]

            # 验证当前模型
            assert data["data"]["current"]["llm"] == "qwen2.5:7b"
            assert data["data"]["current"]["embedding"] == "nomic-embed-text"


# ========================================================================
# GET /api/v1/models/status Tests
# ========================================================================

class TestModelStatusAPI:
    """测试模型状态 API"""

    @pytest.mark.asyncio
    async def test_get_status_success(self, client, mock_llm_manager):
        """测试成功获取模型状态"""
        with patch("src.api.routes.models.get_llm_manager", return_value=mock_llm_manager):
            response = client.get("/api/v1/models/status")

            assert response.status_code == 200
            data = response.json()

            assert "data" in data
            assert "current_models" in data["data"]
            assert "health" in data["data"]

            # 验证当前模型
            assert data["data"]["current_models"]["llm"] == "qwen2.5:7b"
            assert data["data"]["current_models"]["embedding"] == "nomic-embed-text"

    @pytest.mark.asyncio
    async def test_get_status_health_check_failure(self, client, mock_llm_manager):
        """测试健康检查失败"""
        mock_llm_manager.check_model_health = AsyncMock(side_effect=Exception("Health check failed"))

        with patch("src.api.routes.models.get_llm_manager", return_value=mock_llm_manager):
            response = client.get("/api/v1/models/status")

            # 应该仍然返回200，但包含错误信息
            assert response.status_code == 200
            data = response.json()
            assert "data" in data


# ========================================================================
# POST /api/v1/models/switch-llm Tests
# ========================================================================

class TestSwitchLLMAPI:
    """测试切换 LLM 模型 API"""

    @pytest.mark.asyncio
    async def test_switch_llm_success(self, client, mock_llm_manager):
        """测试成功切换 LLM 模型"""
        mock_llm = Mock()
        mock_llm_manager.switch_llm_model = Mock(return_value=mock_llm)

        with patch("src.api.routes.models.get_llm_manager", return_value=mock_llm_manager):
            response = client.post(
                "/api/v1/models/switch-llm",
                json={"model_name": "qwen2.5:14b"}
            )

            assert response.status_code == 200
            data = response.json()

            assert "data" in data
            assert data["data"]["model_name"] == "qwen2.5:14b"
            assert data["data"]["model_type"] == "llm"

            # 验证管理器方法被调用
            mock_llm_manager.switch_llm_model.assert_called_once_with("qwen2.5:14b")

    def test_switch_llm_unsupported_model(self, client, mock_llm_manager):
        """测试切换不支持的模型"""
        with patch("src.api.routes.models.get_llm_manager", return_value=mock_llm_manager):
            response = client.post(
                "/api/v1/models/switch-llm",
                json={"model_name": "invalid-model"}
            )

            assert response.status_code == 400
            assert "Unsupported model" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_switch_llm_manager_error(self, client, mock_llm_manager):
        """测试管理器切换失败"""
        mock_llm_manager.switch_llm_model = Mock(side_effect=ValueError("Switch failed"))

        with patch("src.api.routes.models.get_llm_manager", return_value=mock_llm_manager):
            response = client.post(
                "/api/v1/models/switch-llm",
                json={"model_name": "qwen2.5:7b"}
            )

            assert response.status_code == 400


# ========================================================================
# POST /api/v1/models/switch-embedding Tests
# ========================================================================

class TestSwitchEmbeddingAPI:
    """测试切换 Embedding 模型 API"""

    @pytest.mark.asyncio
    async def test_switch_embedding_success(self, client, mock_llm_manager):
        """测试成功切换 Embedding 模型"""
        mock_embedding = Mock()
        mock_llm_manager.switch_embedding_model = Mock(return_value=mock_embedding)

        with patch("src.api.routes.models.get_llm_manager", return_value=mock_llm_manager):
            response = client.post(
                "/api/v1/models/switch-embedding",
                json={"model_name": "mxbai-embed-large"}
            )

            assert response.status_code == 200
            data = response.json()

            assert "data" in data
            assert data["data"]["model_name"] == "mxbai-embed-large"
            assert data["data"]["model_type"] == "embedding"

            # 验证包含警告信息
            assert "warning" in data["data"]
            assert "rebuild" in data["data"]["warning"].lower()

            # 验证管理器方法被调用
            mock_llm_manager.switch_embedding_model.assert_called_once_with("mxbai-embed-large")

    def test_switch_embedding_unsupported_model(self, client, mock_llm_manager):
        """测试切换不支持的 Embedding 模型"""
        with patch("src.api.routes.models.get_llm_manager", return_value=mock_llm_manager):
            response = client.post(
                "/api/v1/models/switch-embedding",
                json={"model_name": "invalid-embedding"}
            )

            assert response.status_code == 400
            assert "Unsupported embedding model" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_switch_embedding_manager_error(self, client, mock_llm_manager):
        """测试管理器切换失败"""
        mock_llm_manager.switch_embedding_model = Mock(side_effect=ValueError("Switch failed"))

        with patch("src.api.routes.models.get_llm_manager", return_value=mock_llm_manager):
            response = client.post(
                "/api/v1/models/switch-embedding",
                json={"model_name": "nomic-embed-text"}
            )

            assert response.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
