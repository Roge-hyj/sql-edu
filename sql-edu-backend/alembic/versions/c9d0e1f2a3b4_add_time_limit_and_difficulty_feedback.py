"""add time_limit_seconds and question_difficulty_feedback

本迁移作用：
  1) 在 questions 表上新增 time_limit_seconds：题目限时（秒），用于限时挑战。
  2) 新建 question_difficulty_feedback 表：用户对题目难度的评分（user_id, question_id, rating），
     用于难度评估与动态支架。

Revision ID: c9d0e1f2a3b4
Revises: b7c8d9e0f1a2
Create Date: 2026-01-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c9d0e1f2a3b4"
down_revision: Union[str, Sequence[str], None] = "b7c8d9e0f1a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("questions", sa.Column("time_limit_seconds", sa.Integer(), nullable=True))

    op.create_table(
        "question_difficulty_feedback",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["question_id"],
            ["questions.id"],
            name=op.f("fk_question_difficulty_feedback_question_id_questions"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_question_difficulty_feedback_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_question_difficulty_feedback")),
    )
    op.create_index(
        op.f("ix_question_difficulty_feedback_question_id"),
        "question_difficulty_feedback",
        ["question_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_question_difficulty_feedback_user_id"),
        "question_difficulty_feedback",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_question_difficulty_feedback_user_id"),
        table_name="question_difficulty_feedback",
    )
    op.drop_index(
        op.f("ix_question_difficulty_feedback_question_id"),
        table_name="question_difficulty_feedback",
    )
    op.drop_table("question_difficulty_feedback")
    op.drop_column("questions", "time_limit_seconds")
