"""
数据库模型定义

包含同步历史记录和配置表的 SQLAlchemy 模型。
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Boolean, Text, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column

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
