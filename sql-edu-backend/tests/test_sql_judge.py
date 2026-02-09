"""测试 SQL 判题引擎。"""

import pytest
from core.sql_judge import SQLJudgeService, SQLJudgeError


class TestSQLSafetyCheck:
    """测试 SQL 安全检查。"""

    @pytest.fixture
    def judge_service(self, test_db_session):
        """创建判题服务实例。"""
        return SQLJudgeService(test_db_session)

    def test_safe_select(self, judge_service):
        """SELECT 语句应该通过安全检查。"""
        safe, _ = judge_service._check_sql_safety("SELECT * FROM users")
        assert safe is True

    def test_safe_select_with_leading_comment(self, judge_service):
        """带首部注释的 SELECT 不应误判。"""
        safe, _ = judge_service._check_sql_safety("-- comment\nSELECT * FROM users")
        assert safe is True

    def test_dangerous_drop(self, judge_service):
        """DROP 语句应该被拒绝。"""
        safe, kw = judge_service._check_sql_safety("DROP TABLE users")
        assert safe is False
        assert kw == "drop"

    def test_dangerous_delete(self, judge_service):
        """DELETE 语句应该被拒绝。"""
        safe, _ = judge_service._check_sql_safety("DELETE FROM users")
        assert safe is False

    def test_dangerous_update(self, judge_service):
        """UPDATE 语句应该被拒绝。"""
        safe, _ = judge_service._check_sql_safety("UPDATE users SET name = 'test'")
        assert safe is False

    def test_case_insensitive(self, judge_service):
        """安全检查应该不区分大小写。"""
        safe1, _ = judge_service._check_sql_safety("drop table users")
        safe2, _ = judge_service._check_sql_safety("DROP TABLE users")
        assert safe1 is False and safe2 is False

    def test_word_boundary(self, judge_service):
        """应该使用单词边界匹配，避免误判。"""
        # "deleted" 不应该匹配 "delete"
        safe, _ = judge_service._check_sql_safety("SELECT deleted FROM users")
        assert safe is True


class TestResultNormalization:
    """测试结果标准化。"""

    @pytest.fixture
    def judge_service(self, test_db_session):
        """创建判题服务实例。"""
        return SQLJudgeService(test_db_session)

    def test_normalize_numeric(self, judge_service):
        """数值应该转换为字符串。"""
        result = [{"id": 1, "age": 25}]
        normalized = judge_service._normalize_result(result)
        assert normalized[0]["id"] == "1"
        assert normalized[0]["age"] == "25"

    def test_normalize_none(self, judge_service):
        """None 值应该保留。"""
        result = [{"id": 1, "name": None}]
        normalized = judge_service._normalize_result(result)
        assert normalized[0]["name"] is None


class TestResultComparison:
    """测试结果对比。"""

    @pytest.fixture
    def judge_service(self, test_db_session):
        """创建判题服务实例。"""
        return SQLJudgeService(test_db_session)

    def test_identical_results(self, judge_service):
        """相同结果应该匹配。"""
        result1 = [{"id": 1, "name": "Alice"}]
        result2 = [{"id": 1, "name": "Alice"}]
        is_match, msg = judge_service.compare_results(result1, result2)
        assert is_match is True

    def test_different_row_count(self, judge_service):
        """不同行数应该不匹配。"""
        result1 = [{"id": 1}]
        result2 = [{"id": 1}, {"id": 2}]
        is_match, msg = judge_service.compare_results(result1, result2)
        assert is_match is False
        assert "行数" in msg

    def test_different_columns(self, judge_service):
        """不同列结构应该不匹配。"""
        result1 = [{"id": 1, "name": "Alice"}]
        result2 = [{"id": 1, "age": 25}]
        is_match, msg = judge_service.compare_results(result1, result2)
        assert is_match is False
        assert "列结构" in msg

    def test_different_data(self, judge_service):
        """不同数据应该不匹配。"""
        result1 = [{"id": 1, "name": "Alice"}]
        result2 = [{"id": 1, "name": "Bob"}]
        is_match, msg = judge_service.compare_results(result1, result2)
        assert is_match is False

    def test_order_independent(self, judge_service):
        """无序对比：顺序不同但数据相同应该匹配。"""
        result1 = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        result2 = [{"id": 2, "name": "Bob"}, {"id": 1, "name": "Alice"}]
        is_match, msg = judge_service.compare_results(result1, result2)
        assert is_match is True

    def test_order_sensitive_asc_vs_desc(self, judge_service):
        """有序对比：ORDER BY ASC 与 DESC 结果行序不同应判为错误。"""
        # 模拟「按 id 从大到小取 3 条」：标准答案顺序 [3, 2, 1]
        correct = [{"id": 3, "name": "C"}, {"id": 2, "name": "B"}, {"id": 1, "name": "A"}]
        # 学生写成 ASC：顺序 [1, 2, 3]
        student = [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}, {"id": 3, "name": "C"}]
        is_match, msg = judge_service.compare_results_ordered(student, correct)
        assert is_match is False
        assert "顺序" in msg or "ORDER BY" in msg or "不一致" in msg

    def test_order_sensitive_same_order(self, judge_service):
        """有序对比：行序与数据都一致应判为正确。"""
        result = [{"id": 3, "name": "C"}, {"id": 2, "name": "B"}]
        is_match, msg = judge_service.compare_results_ordered(result, result)
        assert is_match is True

    def test_sql_has_order_by(self, judge_service):
        """应正确识别 SQL 是否含 ORDER BY。"""
        assert judge_service._sql_has_order_by("SELECT * FROM users ORDER BY id DESC") is True
        assert judge_service._sql_has_order_by("select * from t order by a") is True
        assert judge_service._sql_has_order_by("SELECT * FROM users") is False
        assert judge_service._sql_has_order_by("SELECT * FROM order_items") is False
