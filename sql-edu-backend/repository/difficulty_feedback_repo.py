"""题目难度反馈数据访问层。"""

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.question_feedback import QuestionDifficultyFeedback


class DifficultyFeedbackRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, user_id: int, question_id: int, rating: int) -> QuestionDifficultyFeedback:
        """记录一次难度评分（1～10）。同一用户对同一题可多次评分（每次正确完成可评一次）。"""
        row = QuestionDifficultyFeedback(
            user_id=user_id,
            question_id=question_id,
            rating=max(1, min(10, rating)),
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def get_question_stats(self, question_id: int) -> dict:
        """返回该题的主观评分统计。"""
        count_stmt = select(func.count(QuestionDifficultyFeedback.id)).where(
            QuestionDifficultyFeedback.question_id == question_id
        )
        count = await self.session.scalar(count_stmt) or 0
        if count == 0:
            return {"feedback_count": 0, "avg_rating": None}

        avg_stmt = select(func.avg(QuestionDifficultyFeedback.rating)).where(
            QuestionDifficultyFeedback.question_id == question_id
        )
        avg = await self.session.scalar(avg_stmt)
        return {"feedback_count": count, "avg_rating": float(avg) if avg is not None else None}

    async def get_feedback_stats_by_question_ids(
        self, question_ids: list[int]
    ) -> dict[int, dict]:
        """批量查询多题的主观评分统计。"""
        if not question_ids:
            return {}
        count_stmt = (
            select(
                QuestionDifficultyFeedback.question_id,
                func.count(QuestionDifficultyFeedback.id).label("feedback_count"),
                func.avg(QuestionDifficultyFeedback.rating).label("avg_rating"),
            )
            .where(QuestionDifficultyFeedback.question_id.in_(question_ids))
            .group_by(QuestionDifficultyFeedback.question_id)
        )
        rows = (await self.session.execute(count_stmt)).all()
        return {
            r.question_id: {
                "feedback_count": r.feedback_count,
                "avg_rating": float(r.avg_rating) if r.avg_rating is not None else None,
            }
            for r in rows
        }


__all__ = ["DifficultyFeedbackRepository"]
