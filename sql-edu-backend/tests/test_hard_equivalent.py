"""难题等价多解判题单元测试：使用 SQLite 验证 CTE/子查询/单层等写法判为正确。"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text
from sqlalchemy.pool import StaticPool

from core.sql_judge import SQLJudgeService


@pytest.fixture
async def session_with_students_scores():
    """创建 SQLite 内存库，含 Students、Scores 表及示例数据。"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.execute(text("""
            CREATE TABLE Students (id INT PRIMARY KEY, name TEXT, class_id INT)
        """))
        await conn.execute(text("""
            CREATE TABLE Scores (student_id INT, subject TEXT, degree INT)
        """))
        await conn.execute(text("""
            INSERT INTO Students VALUES (1,'A',1),(2,'B',1),(3,'C',2)
        """))
        await conn.execute(text("""
            INSERT INTO Scores VALUES (1,'数学',90),(1,'英语',85),(2,'数学',88),(2,'英语',82),(3,'数学',95),(3,'英语',90)
        """))
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_class_avg_equivalent_forms(session_with_students_scores: AsyncSession):
    """学霸班级题：单层、CTE、子查询、INNER JOIN、ON 交换五种等价形式应全部判对。"""
    judge = SQLJudgeService(session_with_students_scores)
    correct_sql = """SELECT s.class_id, AVG(sc.degree) AS class_avg
FROM Students s
JOIN Scores sc ON s.id = sc.student_id
GROUP BY s.class_id
HAVING AVG(sc.degree) > 85"""

    equivalents = [
        ("单层", correct_sql),
        ("CTE", """WITH ClassGrades AS (
    SELECT s.class_id, sc.degree
    FROM Students s
    JOIN Scores sc ON s.id = sc.student_id
)
SELECT class_id, AVG(degree) AS class_avg
FROM ClassGrades
GROUP BY class_id
HAVING AVG(degree) > 85"""),
        ("子查询", """SELECT class_id, AVG(degree) AS class_avg
FROM (
    SELECT s.class_id, sc.degree
    FROM Students s
    JOIN Scores sc ON s.id = sc.student_id
) t
GROUP BY class_id
HAVING AVG(degree) > 85"""),
        ("INNER JOIN", """SELECT s.class_id, AVG(sc.degree) AS class_avg
FROM Students s
INNER JOIN Scores sc ON s.id = sc.student_id
GROUP BY s.class_id
HAVING AVG(sc.degree) > 85"""),
        ("ON 交换", """SELECT s.class_id, AVG(sc.degree) AS class_avg
FROM Students s
JOIN Scores sc ON sc.student_id = s.id
GROUP BY s.class_id
HAVING AVG(sc.degree) > 85"""),
    ]

    for name, sql in equivalents:
        is_correct, err = await judge.judge_sql(sql, correct_sql, required_output_columns=None)
        assert is_correct, f"{name} 应判对，错误: {err}"
