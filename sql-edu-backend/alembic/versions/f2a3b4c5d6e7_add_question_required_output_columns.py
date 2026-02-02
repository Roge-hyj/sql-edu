"""add question required_output_columns for output spec display

本迁移作用：
  在 questions 表上新增 required_output_columns 列（文本），用于存储判题时要求的输出列规范
  （如列名、顺序等），便于前端展示「输出要求」与判题逻辑对齐。

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-02-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f2a3b4c5d6e7"
down_revision: Union[str, Sequence[str], None] = "e1f2a3b4c5d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "questions",
        sa.Column("required_output_columns", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("questions", "required_output_columns")
