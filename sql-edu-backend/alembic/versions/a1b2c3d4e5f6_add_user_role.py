"""add user.role column

本迁移作用：
  在 users 表上新增 role 列（如 teacher / student），用于区分教师端与学生端。
  新用户默认 role 为 student；可通过邀请码注册为 teacher。
  回滚时删除该列即可（alembic downgrade）。

Revision ID: a1b2c3d4e5f6
Revises: 4561426f301b
Create Date: 2026-01-28
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "4561426f301b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add role column to users table."""
    op.add_column(
        "users",
        sa.Column("role", sa.String(length=20), nullable=False, server_default="student"),
    )
    # 可选：移除 server_default，只保留 ORM 默认
    op.alter_column("users", "role", server_default=None)


def downgrade() -> None:
    """Remove role column from users table."""
    op.drop_column("users", "role")

