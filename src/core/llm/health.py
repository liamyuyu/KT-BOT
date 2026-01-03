"""
LLM Health Check
Epic 1: 本地模型集成与管理
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

import httpx

from .manager import get_llm_manager, ModelProvider
from ...config import settings

logger = logging.getLogger(__name__)


@dataclass
class HealthStatus:
    """健康状态数据类"""
    service: str
    status: str  # "healthy", "unhealthy", "degraded"
    timestamp: str
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class LLMHealthChecker:
    """
    LLM 健康检查器
    检查 Ollama 服务和模型的健康状态
    """

    def __init__(self):
        """初始化健康检查器"""
        self.manager = get_llm_manager()

    async def check_ollama_service(self) -> HealthStatus:
        """
        检查 Ollama 服务健康状态

        Returns:
            HealthStatus: 健康状态
        """
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                # 检查版本接口
                version_url = f"{settings.ollama_host}/api/version"
                response = await client.get(version_url)

                if response.status_code == 200:
                    version_data = response.json()

                    # 检查标签接口（列出模型）
                    tags_url = f"{settings.ollama_host}/api/tags"
                    tags_response = await client.get(tags_url)

                    models = []
                    if tags_response.status_code == 200:
                        tags_data = tags_response.json()
                        models = [
                            model.get("name")
                            for model in tags_data.get("models", [])
                        ]

                    return HealthStatus(
                        service="ollama",
                        status="healthy",
                        timestamp=datetime.utcnow().isoformat(),
                        details={
                            "version": version_data.get("version"),
                            "host": settings.ollama_host,
                            "available_models": models,
                            "model_count": len(models),
                        }
                    )
                else:
                    return HealthStatus(
                        service="ollama",
                        status="unhealthy",
                        timestamp=datetime.utcnow().isoformat(),
                        error=f"HTTP {response.status_code}",
                        details={"host": settings.ollama_host}
                    )

        except httpx.ConnectError as e:
            logger.error(f"Cannot connect to Ollama service: {e}")
            return HealthStatus(
                service="ollama",
                status="unhealthy",
                timestamp=datetime.utcnow().isoformat(),
                error=f"Connection failed: {str(e)}",
                details={"host": settings.ollama_host}
            )
        except Exception as e:
            logger.error(f"Ollama health check error: {e}")
            return HealthStatus(
                service="ollama",
                status="unhealthy",
                timestamp=datetime.utcnow().isoformat(),
                error=str(e),
                details={"host": settings.ollama_host}
            )

    async def check_llm_model(self, model_name: Optional[str] = None) -> HealthStatus:
        """
        检查 LLM 模型健康状态

        Args:
            model_name: 模型名称，默认使用配置中的模型

        Returns:
            HealthStatus: 健康状态
        """
        try:
            llm = self.manager.create_llm(model_name=model_name)
            is_healthy = await llm.health_check()

            if is_healthy:
                # 获取模型信息
                try:
                    model_info = await llm.get_model_info()
                    return HealthStatus(
                        service=f"llm_model:{llm.model_name}",
                        status="healthy",
                        timestamp=datetime.utcnow().isoformat(),
                        details={
                            "model_name": model_info.name,
                            "model_type": model_info.model_type,
                            "size": model_info.size,
                            "family": model_info.family,
                        }
                    )
                except Exception as e:
                    # 健康检查通过但获取信息失败，降级为 degraded
                    logger.warning(f"Model info fetch failed: {e}")
                    return HealthStatus(
                        service=f"llm_model:{llm.model_name}",
                        status="degraded",
                        timestamp=datetime.utcnow().isoformat(),
                        details={"model_name": llm.model_name},
                        error=f"Info fetch failed: {str(e)}"
                    )
            else:
                return HealthStatus(
                    service=f"llm_model:{llm.model_name}",
                    status="unhealthy",
                    timestamp=datetime.utcnow().isoformat(),
                    details={"model_name": llm.model_name},
                    error="Health check failed"
                )

        except Exception as e:
            logger.error(f"LLM model health check error: {e}")
            return HealthStatus(
                service=f"llm_model:{model_name or 'default'}",
                status="unhealthy",
                timestamp=datetime.utcnow().isoformat(),
                error=str(e)
            )

    async def check_embedding_model(self, model_name: Optional[str] = None) -> HealthStatus:
        """
        检查 Embedding 模型健康状态

        Args:
            model_name: 模型名称，默认使用配置中的模型

        Returns:
            HealthStatus: 健康状态
        """
        try:
            embedding = self.manager.create_embedding(model_name=model_name)
            is_healthy = await embedding.health_check()

            if is_healthy:
                # 获取模型信息
                try:
                    model_info = await embedding.get_model_info()
                    return HealthStatus(
                        service=f"embedding_model:{embedding.model_name}",
                        status="healthy",
                        timestamp=datetime.utcnow().isoformat(),
                        details={
                            "model_name": model_info.name,
                            "model_type": model_info.model_type,
                            "size": model_info.size,
                            "family": model_info.family,
                        }
                    )
                except Exception as e:
                    logger.warning(f"Embedding model info fetch failed: {e}")
                    return HealthStatus(
                        service=f"embedding_model:{embedding.model_name}",
                        status="degraded",
                        timestamp=datetime.utcnow().isoformat(),
                        details={"model_name": embedding.model_name},
                        error=f"Info fetch failed: {str(e)}"
                    )
            else:
                return HealthStatus(
                    service=f"embedding_model:{embedding.model_name}",
                    status="unhealthy",
                    timestamp=datetime.utcnow().isoformat(),
                    details={"model_name": embedding.model_name},
                    error="Health check failed"
                )

        except Exception as e:
            logger.error(f"Embedding model health check error: {e}")
            return HealthStatus(
                service=f"embedding_model:{model_name or 'default'}",
                status="unhealthy",
                timestamp=datetime.utcnow().isoformat(),
                error=str(e)
            )

    async def check_all(self) -> Dict[str, HealthStatus]:
        """
        检查所有组件的健康状态

        Returns:
            Dict[str, HealthStatus]: 组件名称 -> 健康状态
        """
        results = {}

        # 检查 Ollama 服务
        ollama_status = await self.check_ollama_service()
        results["ollama_service"] = ollama_status

        # 只有 Ollama 服务健康时才检查模型
        if ollama_status.status == "healthy":
            # 检查默认 LLM 模型
            llm_status = await self.check_llm_model()
            results["default_llm"] = llm_status

            # 检查默认 Embedding 模型
            embedding_status = await self.check_embedding_model()
            results["default_embedding"] = embedding_status
        else:
            logger.warning("Ollama service unhealthy, skipping model checks")

        return results

    def get_overall_status(self, health_results: Dict[str, HealthStatus]) -> str:
        """
        根据各组件健康状态计算总体状态

        Args:
            health_results: 各组件健康状态

        Returns:
            str: 总体状态 ("healthy", "degraded", "unhealthy")
        """
        statuses = [status.status for status in health_results.values()]

        if all(s == "healthy" for s in statuses):
            return "healthy"
        elif any(s == "unhealthy" for s in statuses):
            return "unhealthy"
        else:
            return "degraded"


# 全局单例
_health_checker: Optional[LLMHealthChecker] = None


def get_health_checker() -> LLMHealthChecker:
    """
    获取全局健康检查器单例

    Returns:
        LLMHealthChecker: 健康检查器实例
    """
    global _health_checker
    if _health_checker is None:
        _health_checker = LLMHealthChecker()
    return _health_checker
