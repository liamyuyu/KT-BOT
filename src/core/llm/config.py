"""
LLM Model Configuration Management
Epic 1: 本地模型集成与管理 - 配置文件管理
"""

import logging
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class LLMModelConfig(BaseModel):
    """LLM 模型配置"""
    name: str
    enabled: bool = True
    capabilities: List[str] = Field(default_factory=lambda: ["chat"])
    max_tokens: int = 8192
    temperature: float = 0.7
    top_p: float = 0.9


class EmbeddingModelConfig(BaseModel):
    """Embedding 模型配置"""
    name: str
    enabled: bool = True
    dimension: int
    batch_size: int = 32  # 批处理大小
    max_batch_size: int = 100
    timeout: int = 60


class HealthCheckConfig(BaseModel):
    """健康检查配置"""
    enabled: bool = True
    startup_check: bool = True
    check_interval: int = 300
    timeout: int = 10
    retry_count: int = 3


class ModelsConfig(BaseModel):
    """模型总配置"""
    version: str = "1.0"
    llm: Dict[str, Any]
    embedding: Dict[str, Any]
    health_check: HealthCheckConfig = Field(default_factory=HealthCheckConfig)


class ModelConfigLoader:
    """模型配置加载器"""

    @staticmethod
    def load_from_yaml(path: str) -> ModelsConfig:
        """
        从 YAML 加载配置

        Args:
            path: YAML 文件路径

        Returns:
            ModelsConfig: 模型配置对象

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 配置格式错误
        """
        yaml_path = Path(path)
        if not yaml_path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if not data:
            raise ValueError(f"Empty config file: {path}")

        return ModelsConfig(**data)

    @staticmethod
    def load_from_env() -> ModelsConfig:
        """
        从环境变量加载（向后兼容）

        Returns:
            ModelsConfig: 从环境变量构建的配置对象
        """
        from src.config import settings

        return ModelsConfig(
            version="1.0",
            llm={
                "provider": "ollama",
                "default_model": settings.ollama_model,
                "models": [
                    {
                        "name": settings.ollama_model,
                        "enabled": True,
                        "capabilities": ["chat", "completion"]
                    }
                ]
            },
            embedding={
                "provider": "ollama",
                "default_model": settings.ollama_embedding_model,
                "models": [
                    {
                        "name": settings.ollama_embedding_model,
                        "enabled": True,
                        "dimension": 1024,
                        "batch_size": 32
                    }
                ]
            },
            health_check=HealthCheckConfig()
        )

    @staticmethod
    def load_config(yaml_path: Optional[str] = None) -> ModelsConfig:
        """
        智能加载配置：优先级 YAML > ENV

        Args:
            yaml_path: YAML 文件路径，默认为 config/models.yaml

        Returns:
            ModelsConfig: 模型配置对象
        """
        if yaml_path is None:
            yaml_path = "config/models.yaml"

        yaml_file = Path(yaml_path)

        # 尝试从 YAML 加载
        if yaml_file.exists() and yaml_file.stat().st_size > 10:
            try:
                logger.info(f"Loading models config from YAML: {yaml_path}")
                return ModelConfigLoader.load_from_yaml(str(yaml_file))
            except Exception as e:
                logger.warning(f"Failed to load YAML config: {e}, falling back to environment variables")

        # 回退到环境变量
        logger.info("Loading models config from environment variables")
        return ModelConfigLoader.load_from_env()


def get_model_config(yaml_path: Optional[str] = None) -> ModelsConfig:
    """
    获取模型配置（便捷函数）

    Args:
        yaml_path: YAML 文件路径

    Returns:
        ModelsConfig: 模型配置对象
    """
    return ModelConfigLoader.load_config(yaml_path)
