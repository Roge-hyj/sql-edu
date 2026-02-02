"""测试 Repository 层。"""

import pytest
from repository import QuestionRepository, SubmissionRepository
from schemas.submission import SubmissionCreate


class TestQuestionRepository:
    """测试题目 Repository。"""

    @pytest.mark.asyncio
    async def test_get_by_id(self, test_db_session, test_question):
        """测试根据 ID 查询题目。"""
        repo = QuestionRepository(test_db_session)
        question = await repo.get_by_id(test_question.id)
        
        assert question is not None
        assert question.id == test_question.id
        assert question.title == "测试题目"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, test_db_session):
        """测试查询不存在的题目。"""
        repo = QuestionRepository(test_db_session)
        question = await repo.get_by_id(99999)
        
        assert question is None

    @pytest.mark.asyncio
    async def test_get_all(self, test_db_session, test_question):
        """测试查询所有题目。"""
        repo = QuestionRepository(test_db_session)
        questions = await repo.get_all()
        
        assert len(questions) >= 1
        assert any(q.id == test_question.id for q in questions)


class TestSubmissionRepository:
    """测试提交记录 Repository。"""

    @pytest.mark.asyncio
    async def test_create(self, test_db_session, test_user, test_question):
        """测试创建提交记录。"""
        repo = SubmissionRepository(test_db_session)
        
        submission_data = SubmissionCreate(
            user_id=test_user.id,
            question_id=test_question.id,
            student_sql="SELECT * FROM users",
            ai_hint="测试提示",
            is_correct=False,
            hint_level=1
        )
        
        submission = await repo.create(submission_data)
        await test_db_session.commit()
        
        assert submission.id is not None
        assert submission.student_sql == "SELECT * FROM users"
        assert submission.is_correct is False
        assert submission.hint_level == 1

    @pytest.mark.asyncio
    async def test_get_failure_count(self, test_db_session, test_user, test_question):
        """测试统计失败次数。"""
        repo = SubmissionRepository(test_db_session)
        
        # 创建几条失败的提交记录
        for i in range(3):
            submission_data = SubmissionCreate(
                user_id=test_user.id,
                question_id=test_question.id,
                student_sql=f"SELECT * FROM users WHERE id = {i}",
                is_correct=False,
                hint_level=1
            )
            await repo.create(submission_data)
        
        # 创建一条成功的提交记录（不应该计入失败次数）
        submission_data = SubmissionCreate(
            user_id=test_user.id,
            question_id=test_question.id,
            student_sql="SELECT * FROM users",
            is_correct=True,
            hint_level=1
        )
        await repo.create(submission_data)
        
        await test_db_session.commit()
        
        # 统计失败次数
        failure_count = await repo.get_failure_count(test_user.id, test_question.id)
        assert failure_count == 3

    @pytest.mark.asyncio
    async def test_get_failure_count_zero(self, test_db_session, test_user, test_question):
        """测试没有失败记录时返回 0。"""
        repo = SubmissionRepository(test_db_session)
        failure_count = await repo.get_failure_count(test_user.id, test_question.id)
        assert failure_count == 0

    @pytest.mark.asyncio
    async def test_get_user_submissions(self, test_db_session, test_user, test_question):
        """测试查询用户提交记录。"""
        repo = SubmissionRepository(test_db_session)
        
        # 创建几条提交记录
        for i in range(3):
            submission_data = SubmissionCreate(
                user_id=test_user.id,
                question_id=test_question.id,
                student_sql=f"SELECT * FROM users WHERE id = {i}",
                is_correct=False,
                hint_level=1
            )
            await repo.create(submission_data)
        
        await test_db_session.commit()
        
        # 查询提交记录
        submissions = await repo.get_user_submissions(test_user.id, test_question.id)
        assert len(submissions) == 3
