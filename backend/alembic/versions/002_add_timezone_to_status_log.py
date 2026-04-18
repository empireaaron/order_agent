"""
Add timezone to ticket_status_logs.created_at

Revision ID: 002
Revises: 001
Create Date: 2026-04-18
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    """将 ticket_status_logs.created_at 改为带时区的 DateTime 类型"""
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == 'sqlite':
        # SQLite 没有时区类型，跳过
        return

    elif dialect == 'postgresql':
        op.alter_column(
            'ticket_status_logs',
            'created_at',
            type_=sa.TIMESTAMP(timezone=True),
            existing_nullable=True
        )

    elif dialect == 'mysql':
        op.alter_column(
            'ticket_status_logs',
            'created_at',
            type_=mysql.DATETIME(fsp=6),
            existing_nullable=True
        )


def downgrade():
    """回滚：移时区信息"""
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == 'sqlite':
        return

    elif dialect == 'postgresql':
        op.alter_column(
            'ticket_status_logs',
            'created_at',
            type_=sa.TIMESTAMP(timezone=False),
            existing_nullable=True
        )

    elif dialect == 'mysql':
        op.alter_column(
            'ticket_status_logs',
            'created_at',
            type_=mysql.DATETIME(fsp=0),
            existing_nullable=True
        )
