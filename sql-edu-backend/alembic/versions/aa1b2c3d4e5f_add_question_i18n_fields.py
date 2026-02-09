"""add question i18n fields (title/content translations)

本迁移作用：
  在 questions 表上新增多语言字段：title_en, content_en, title_zh_tw, content_zh_tw。
  用于题目题面的英文、繁体中文翻译，配合前端语言切换与 AI 生成/补全翻译接口。

Revision ID: aa1b2c3d4e5f
Revises: f2a3b4c5d6e7
Create Date: 2026-02-02

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "aa1b2c3d4e5f"
down_revision: Union[str, Sequence[str], None] = "f2a3b4c5d6e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("questions", sa.Column("title_en", sa.String(length=200), nullable=True))
    op.add_column("questions", sa.Column("content_en", sa.Text(), nullable=True))
    op.add_column("questions", sa.Column("title_zh_tw", sa.String(length=200), nullable=True))
    op.add_column("questions", sa.Column("content_zh_tw", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("questions", "content_zh_tw")
    op.drop_column("questions", "title_zh_tw")
    op.drop_column("questions", "content_en")
    op.drop_column("questions", "title_en")

