"""Initial sync tables

Revision ID: 001
Revises:
Create Date: 2026-01-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建同步相关表"""

    # 创建 sync_history 表
    op.create_table(
        'sync_history',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('task_id', sa.String(length=36), nullable=False),
        sa.Column('source', sa.String(length=20), nullable=False),
        sa.Column('sync_type', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('total_items', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('synced_items', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_items', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('progress_percentage', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_code', sa.String(length=50), nullable=True),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.Column('metadata_json', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_sync_history'))
    )

    # 创建索引
    op.create_index(op.f('ix_sync_history_task_id'), 'sync_history', ['task_id'], unique=True)
    op.create_index(op.f('ix_sync_history_source'), 'sync_history', ['source'], unique=False)
    op.create_index(op.f('ix_sync_history_start_time'), 'sync_history', ['start_time'], unique=False)
    op.create_index('idx_sync_history_source_status', 'sync_history', ['source', 'status'], unique=False)
    op.create_index('idx_sync_history_source_start_time', 'sync_history', ['source', 'start_time'], unique=False)

    # 创建 sync_config 表
    op.create_table(
        'sync_config',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('source', sa.String(length=20), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('schedule_type', sa.String(length=20), nullable=False),
        sa.Column('schedule_value', sa.String(length=100), nullable=False),
        sa.Column('incremental', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('batch_size', sa.Integer(), nullable=False, server_default='50'),
        sa.Column('retry_attempts', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('retry_delay', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('extra_params', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('last_sync_time', sa.DateTime(), nullable=True),
        sa.Column('last_sync_task_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_sync_config'))
    )

    # 创建索引
    op.create_index(op.f('ix_sync_config_source'), 'sync_config', ['source'], unique=True)
    op.create_index(op.f('ix_sync_config_last_sync_time'), 'sync_config', ['last_sync_time'], unique=False)


def downgrade() -> None:
    """删除同步相关表"""

    # 删除 sync_config 表
    op.drop_index(op.f('ix_sync_config_last_sync_time'), table_name='sync_config')
    op.drop_index(op.f('ix_sync_config_source'), table_name='sync_config')
    op.drop_table('sync_config')

    # 删除 sync_history 表
    op.drop_index('idx_sync_history_source_start_time', table_name='sync_history')
    op.drop_index('idx_sync_history_source_status', table_name='sync_history')
    op.drop_index(op.f('ix_sync_history_start_time'), table_name='sync_history')
    op.drop_index(op.f('ix_sync_history_source'), table_name='sync_history')
    op.drop_index(op.f('ix_sync_history_task_id'), table_name='sync_history')
    op.drop_table('sync_history')
