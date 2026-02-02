"""add question schema_preview for table display

本迁移作用：
  在 questions 表上新增 schema_preview 列（文本），用于存储题目相关表结构的预览内容，
  便于前端展示「表结构」说明（如建表 SQL 或表格描述）。

Revision ID: e1f2a3b4c5d6
Revises: d0e1f2a3b4c5
Create Date: 2026-01-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e1f2a3b4c5d6"
down_revision: Union[str, Sequence[str], None] = "d0e1f2a3b4c5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "questions",
        sa.Column("schema_preview", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("questions", "schema_preview")
