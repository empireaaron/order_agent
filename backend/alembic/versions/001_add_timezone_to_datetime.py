"""
Add timezone to all DateTime columns

Revision ID: 001
Revises: 
Create Date: 2026-04-09
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql, mysql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """
    将所有 DateTime 字段改为带时区的类型
    
    PostgreSQL: TIMESTAMP WITH TIME ZONE
    MySQL: DATETIME(fsp=6)  # MySQL 5.6.5+ 支持时区
    SQLite: 保持原样（SQLite 没有时区类型）
    """
    
    # 聊天相关表
    _upgrade_chat_tables()
    
    # 工单相关表
    _upgrade_ticket_tables()
    
    # 知识库相关表
    _upgrade_knowledge_tables()
    
    # 监控指标相关表
    _upgrade_metrics_tables()


def downgrade():
    """回滚：移时区信息"""
    pass  # SQLite 不支持，其他数据库谨慎回滚


def _upgrade_chat_tables():
    """聊天表时间字段升级"""
    tables_columns = {
        'chat_sessions': ['created_at', 'connected_at', 'closed_at', 'last_message_at'],
        'chat_messages': ['created_at', 'read_at'],
        'agent_status': ['last_heartbeat', 'updated_at'],
    }
    
    for table, columns in tables_columns.items():
        for column in columns:
            _alter_datetime_column(table, column)


def _upgrade_ticket_tables():
    """工单表时间字段升级"""
    tables_columns = {
        'users': ['last_login_at', 'created_at', 'updated_at'],
        'tickets': ['resolved_at', 'closed_at', 'created_at', 'updated_at'],
        'ticket_comments': ['read_at', 'created_at'],
        'ticket_activities': ['created_at'],
    }
    
    for table, columns in tables_columns.items():
        for column in columns:
            _alter_datetime_column(table, column)


def _upgrade_knowledge_tables():
    """知识库表时间字段升级"""
    tables_columns = {
        'knowledge_bases': ['created_at', 'updated_at'],
        'documents': ['created_at', 'updated_at'],
    }
    
    for table, columns in tables_columns.items():
        for column in columns:
            _alter_datetime_column(table, column)


def _upgrade_metrics_tables():
    """监控指标表时间字段升级"""
    tables_columns = {
        'intent_metrics': ['created_at', 'updated_at'],
        'api_metrics': ['created_at', 'updated_at'],
        'error_metrics': ['created_at', 'updated_at'],
        'intent_classification_logs': ['annotated_at', 'created_at'],
    }
    
    for table, columns in tables_columns.items():
        for column in columns:
            _alter_datetime_column(table, column)


def _table_exists(table_name: str) -> bool:
    """检查表是否存在"""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def _alter_datetime_column(table_name: str, column_name: str):
    """
    根据数据库类型修改 DateTime 列
    
    SQLite: 不执行（不支持 ALTER COLUMN TYPE）
    PostgreSQL: TIMESTAMP WITH TIME ZONE
    MySQL: DATETIME(6)
    """
    from alembic import context
    
    bind = op.get_bind()
    dialect = bind.dialect.name
    
    # 跳过不存在的表
    if not _table_exists(table_name):
        print(f"Skipping {table_name} - table does not exist")
        return
    
    if dialect == 'sqlite':
        # SQLite 没有时区类型，跳过
        return
    
    elif dialect == 'postgresql':
        # PostgreSQL: 改为带时区的时间戳
        op.alter_column(
            table_name, 
            column_name,
            type_=postgresql.TIMESTAMP(timezone=True),
            existing_nullable=True
        )
    
    elif dialect == 'mysql':
        # MySQL: DATETIME(6) 支持微秒
        # 注意：MySQL 的 DATETIME 不存储时区，需要应用层处理
        op.alter_column(
            table_name,
            column_name,
            type_=mysql.DATETIME(fsp=6),
            existing_nullable=True
        )
