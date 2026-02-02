"""Pytest 配置和共享 fixtures。"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from models import Base
from models.question import Question
from models.user import User
from models.submission import Submission


# 测试数据库 URL（使用 SQLite 内存数据库）
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="function")
async def test_db_session():
    """创建测试数据库会话。"""
    # 创建测试引擎
    engine = create_async_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # 创建表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 创建会话工厂
    async_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    # 创建会话
    async with async_session_maker() as session:
        yield session
    
    # 清理
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def test_user(test_db_session: AsyncSession):
    """创建测试用户。"""
    user = User(
        email="test@example.com",
        username="testuser",
        password="hashed_password"  # 实际测试中应该使用加密后的密码
    )
    test_db_session.add(user)
    await test_db_session.flush()
    await test_db_session.refresh(user)
    return user


@pytest.fixture
async def test_question(test_db_session: AsyncSession):
    """创建测试题目。"""
    question = Question(
        title="测试题目",
        content="查询所有年龄大于 18 的用户",
        difficulty=1,
        correct_sql="SELECT * FROM users WHERE age > 18"
    )
    test_db_session.add(question)
    await test_db_session.flush()
    await test_db_session.refresh(question)
    return question


@pytest.fixture
async def test_submission(test_db_session: AsyncSession, test_user, test_question):
    """创建测试提交记录。"""
    submission = Submission(
        user_id=test_user.id,
        question_id=test_question.id,
        student_sql="SELECT * FROM users WHERE age > 18",
        ai_hint="测试提示",
        is_correct=True,
        hint_level=1
    )
    test_db_session.add(submission)
    await test_db_session.flush()
    await test_db_session.refresh(submission)
    return submission
