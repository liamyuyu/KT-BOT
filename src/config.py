"""
KT-BOT Configuration Management
基于 pydantic-settings 的配置管理系统
"""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # ========== Application Settings ==========
    app_name: str = Field(default="KT-BOT", description="应用名称")
    app_version: str = Field(default="0.1.0", description="应用版本")
    environment: str = Field(default="development", description="运行环境")
    debug: bool = Field(default=False, description="调试模式")
    log_level: str = Field(default="INFO", description="日志级别")
    host: str = Field(default="0.0.0.0", description="服务监听地址")
    port: int = Field(default=7860, description="服务端口")

    # ========== Epic 1: Ollama Configuration ==========
    ollama_host: str = Field(
        default="http://localhost:11434",
        description="Ollama 服务地址"
    )
    ollama_model: str = Field(
        default="qwen2.5:7b",
        description="默认对话模型"
    )
    ollama_embedding_model: str = Field(
        default="bge-large-zh",
        description="默认 Embedding 模型"
    )
    ollama_timeout: int = Field(
        default=300,
        description="Ollama 请求超时时间（秒）"
    )

    # ========== Epic 2: Jira Configuration ==========
    jira_url: str = Field(
        default="",
        description="Jira 实例 URL (如: https://company.atlassian.net)"
    )
    jira_email: str = Field(
        default="",
        description="Jira 账号邮箱"
    )
    jira_api_token: str = Field(
        default="",
        description="Jira API Token"
    )
    jira_project_key: Optional[str] = Field(
        default=None,
        description="默认 Jira 项目 KEY（可选，留空则拉取所有项目）"
    )
    jira_max_results: int = Field(
        default=100,
        description="单次请求最大结果数"
    )
    jira_timeout: int = Field(
        default=30,
        description="Jira API 请求超时时间（秒）"
    )

    # ========== Epic 2: Confluence Configuration ==========
    confluence_url: str = Field(
        default="",
        description="Confluence 实例 URL (如: https://company.atlassian.net/wiki)"
    )
    confluence_email: str = Field(
        default="",
        description="Confluence 账号邮箱"
    )
    confluence_api_token: str = Field(
        default="",
        description="Confluence API Token"
    )
    confluence_space_key: Optional[str] = Field(
        default=None,
        description="默认 Confluence 空间 KEY（可选，留空则查询所有空间）"
    )
    confluence_timeout: int = Field(
        default=30,
        description="Confluence API 请求超时时间（秒）"
    )

    # ========== Database & Redis ==========
    database_url: str = Field(
        default="postgresql://localhost:5432/ktbot",
        description="数据库连接 URL"
    )
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis 连接 URL"
    )


# 创建全局配置实例
settings = Settings()


# 导出配置实例
__all__ = ["settings", "Settings"]
