"""
Alembic 环境配置

用于数据库迁移的配置和设置。
"""

from logging.config import fileConfig
import asyncio

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# 导入 Base 和所有模型
from src.storage.database.base import Base, DATABASE_URL
from src.storage.database.models import SyncHistory, SyncConfig

# Alembic Config 对象
config = context.config

# 设置 SQLAlchemy URL
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 元数据对象
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    离线模式运行迁移

    在此模式下，不需要实际的数据库连接。
    只会生成 SQL 脚本。
    """
    url = DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """执行迁移"""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """异步运行迁移"""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = DATABASE_URL

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """
    在线模式运行迁移

    在此模式下，需要实际的数据库连接。
    """
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
