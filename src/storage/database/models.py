"""
数据库模型定义

包含同步历史记录、配置表和对话历史的 SQLAlchemy 模型。
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Boolean, Text, JSON, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class SyncHistory(Base):
    """
    同步历史记录表

    记录每次同步任务的执行详情，用于：
    - 查询历史同步记录
    - 统计同步性能
    - 获取上次同步时间
    - 错误追踪和诊断
    """
    __tablename__ = "sync_history"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 任务基本信息
    task_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # jira, confluence
    sync_type: Mapped[str] = mapped_column(String(20), nullable=False)  # full, incremental

    # 执行状态
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # pending, running, completed, failed, cancelled

    # 时间信息
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # 数据统计
    total_items: Mapped[int] = mapped_column(Integer, default=0)
    synced_items: Mapped[int] = mapped_column(Integer, default=0)
    failed_items: Mapped[int] = mapped_column(Integer, default=0)
    progress_percentage: Mapped[float] = mapped_column(Integer, default=0)

    # 错误信息
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # 元数据
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        nullable=False
    )

    # 索引
    __table_args__ = (
        Index('idx_sync_history_source_status', 'source', 'status'),
        Index('idx_sync_history_source_start_time', 'source', 'start_time'),
    )

    def __repr__(self) -> str:
        return (
            f"<SyncHistory(id={self.id}, task_id={self.task_id}, "
            f"source={self.source}, status={self.status})>"
        )


class SyncConfig(Base):
    """
    同步配置表

    持久化存储同步配置，支持：
    - 运行时配置修改
    - 配置历史追踪
    - 多环境配置管理
    """
    __tablename__ = "sync_config"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 配置标识
    source: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)

    # 启用状态
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # 调度配置
    schedule_type: Mapped[str] = mapped_column(String(20), nullable=False)  # cron, interval
    schedule_value: Mapped[str] = mapped_column(String(100), nullable=False)

    # 同步策略
    incremental: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    batch_size: Mapped[int] = mapped_column(Integer, default=50, nullable=False)

    # 重试配置
    retry_attempts: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    retry_delay: Mapped[int] = mapped_column(Integer, default=60, nullable=False)

    # 额外参数（JSON）
    extra_params: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # 上次同步时间（用于增量同步）
    last_sync_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    last_sync_task_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<SyncConfig(id={self.id}, source={self.source}, "
            f"enabled={self.enabled}, schedule={self.schedule_value})>"
        )


class Conversation(Base):
    """
    对话会话表

    记录用户的对话会话，用于：
    - 对话历史管理
    - 对话搜索和检索
    - 对话导出和分享
    - 用户行为分析
    """
    __tablename__ = "conversations"

    # 主键
    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID

    # 用户信息
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # 对话信息
    title: Mapped[str] = mapped_column(String(500), nullable=False)

    # 统计信息
    message_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # 元数据（存储模型配置、参数等）
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # 软删除标记
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        nullable=False,
        index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        nullable=False
    )

    # 关系：一个对话包含多条消息
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # 索引
    __table_args__ = (
        Index('idx_conversations_user_created', 'user_id', 'created_at'),
        Index('idx_conversations_user_deleted', 'user_id', 'is_deleted'),
    )

    def __repr__(self) -> str:
        return (
            f"<Conversation(id={self.id}, user_id={self.user_id}, "
            f"title={self.title[:50]}, messages={self.message_count})>"
        )


class Message(Base):
    """
    对话消息表

    记录对话中的每条消息，包括：
    - 用户消息
    - 助手回复
    - 系统消息
    - RAG 检索上下文
    - 引用信息
    """
    __tablename__ = "messages"

    # 主键
    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID

    # 外键：关联对话
    conversation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 消息角色
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user, assistant, system

    # 消息内容
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # RAG 检索上下文（JSON 数组）
    contexts: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # 引用信息（JSON 数组）
    citations: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # 模型信息
    model_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Token 统计
    token_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # 元数据（存储额外信息）
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        nullable=False,
        index=True
    )

    # 关系：消息属于一个对话
    conversation: Mapped["Conversation"] = relationship(
        "Conversation",
        back_populates="messages"
    )

    # 索引
    __table_args__ = (
        Index('idx_messages_conversation_created', 'conversation_id', 'created_at'),
        Index('idx_messages_role', 'role'),
    )

    def __repr__(self) -> str:
        content_preview = self.content[:50] if self.content else ""
        return (
            f"<Message(id={self.id}, conversation_id={self.conversation_id}, "
            f"role={self.role}, content={content_preview}...)>"
        )
