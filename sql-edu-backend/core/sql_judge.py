"""SQL 判题引擎：安全执行 SQL 并对比结果。"""

from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import re


class SQLJudgeError(Exception):
    """SQL 判题过程中的自定义异常。"""
    pass


class SQLJudgeService:
    """SQL 判题服务，负责安全执行 SQL 并对比结果。"""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _check_sql_safety(self, sql: str) -> bool:
        """检查 SQL 语句的安全性（白名单机制）。

        :param sql: SQL 语句
        :return: 如果安全返回 True，否则返回 False
        """
        # 转换为小写以便检查
        sql_lower = sql.lower().strip()

        # 禁止的危险操作
        dangerous_keywords = [
            "drop",
            "delete",
            "truncate",
            "alter",
            "create",
            "insert",
            "update",
            "grant",
            "revoke",
            "exec",
            "execute",
        ]

        # 检查是否包含危险关键字
        for keyword in dangerous_keywords:
            # 使用单词边界匹配，避免误判（如 "deleted" 不会匹配 "delete"）
            pattern = r"\b" + re.escape(keyword) + r"\b"
            if re.search(pattern, sql_lower):
                return False

        # 只允许 SELECT 语句
        if not sql_lower.startswith("select"):
            return False

        return True

    async def execute_sql_safely(self, sql: str) -> list[dict[str, Any]]:
        """安全执行 SQL 语句并返回结果。

        :param sql: SQL 语句
        :return: 查询结果列表（每行是一个字典）
        :raises SQLJudgeError: 如果 SQL 不安全或执行失败
        """
        # 安全检查
        if not self._check_sql_safety(sql):
            raise SQLJudgeError(
                "SQL 语句包含危险操作，仅允许 SELECT 查询语句。"
            )

        try:
            # 执行 SQL（使用 text() 包装原始 SQL）
            result = await self.session.execute(text(sql))
            rows = result.fetchall()

            # 转换为字典列表
            columns = result.keys()
            result_list = [dict(zip(columns, row)) for row in rows]

            return result_list
        except Exception as e:
            raise SQLJudgeError(f"SQL 执行失败: {str(e)}")

    def _sql_has_order_by(self, sql: str) -> bool:
        """粗略判断 SQL 是否包含 ORDER BY（标准答案若要求顺序，则判题需按行序比较）。"""
        sql_lower = sql.lower().strip()
        sql_lower = re.sub(r"--[^\n]*", " ", sql_lower)
        sql_lower = re.sub(r"/\*[\s\S]*?\*/", " ", sql_lower)
        return "order" in sql_lower and " by " in sql_lower

    def _normalize_row(self, row: dict[str, Any]) -> dict[str, Any]:
        """单行标准化：数值转字符串；字符串去首尾空格并统一小写比较，避免 name='Laptop' 与 'laptop'/'Laptop ' 误判。"""
        out = {}
        for key, value in row.items():
            if value is None:
                out[key] = None
            elif isinstance(value, (int, float)):
                out[key] = str(value)
            else:
                s = str(value).strip()
                # 字符串列（如 name）统一按小写比较，避免大小写/空格导致误判
                out[key] = s.lower() if s else ""
        return out

    def _normalize_result(self, result: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """标准化结果集（用于无序对比）：统一值类型并按行排序，使顺序无关。"""
        normalized = [self._normalize_row(row) for row in result]
        try:
            normalized.sort(key=lambda x: tuple(
                str(v) if v is not None else "" for v in x.values()
            ))
        except Exception:
            pass
        return normalized

    def _normalize_result_keep_order(self, result: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """标准化结果集但保持行序（用于 ORDER BY 题目的顺序敏感对比）。"""
        return [self._normalize_row(row) for row in result]

    def compare_results(
        self, student_result: list[dict[str, Any]], correct_result: list[dict[str, Any]]
    ) -> tuple[bool, str]:
        """对比学生结果和标准答案（无序，向后兼容）。含 ORDER BY 的题目请用 judge_sql 自动按序比较。"""
        return self.compare_results_unordered(student_result, correct_result)

    def _compare_normalized(
        self,
        student_norm: list[dict[str, Any]],
        correct_norm: list[dict[str, Any]],
        *,
        ordered: bool,
    ) -> tuple[bool, str]:
        """在已标准化后的结果上做对比。ordered=True 时要求行序一致（等价性+逻辑性）。"""
        if len(student_norm) != len(correct_norm):
            return (
                False,
                f"结果行数不匹配：期望 {len(correct_norm)} 行，实际 {len(student_norm)} 行。",
            )
        if student_norm and correct_norm:
            sk = set(student_norm[0].keys())
            ck = set(correct_norm[0].keys())
            if sk != ck:
                missing = ck - sk
                extra = sk - ck
                error_msg = "列结构不匹配。"
                if missing:
                    error_msg += f" 缺少列: {', '.join(missing)}"
                if extra:
                    error_msg += f" 多余列: {', '.join(extra)}"
                return False, error_msg
        if ordered:
            for i, (sr, cr) in enumerate(zip(student_norm, correct_norm)):
                if sr != cr:
                    return False, f"第 {i + 1} 行与标准答案不一致（顺序或数据有误，如 ORDER BY 方向相反）。"
            return True, "结果匹配（含顺序）。"
        try:
            student_set = {tuple(sorted(row.items())) for row in student_norm}
            correct_set = {tuple(sorted(row.items())) for row in correct_norm}
            if student_set != correct_set:
                return False, "结果数据不匹配（可能顺序不同或数据有误）。"
        except Exception:
            if student_norm != correct_norm:
                return False, "结果数据不匹配。"
        return True, "结果匹配。"

    def compare_results_unordered(
        self, student_result: list[dict[str, Any]], correct_result: list[dict[str, Any]]
    ) -> tuple[bool, str]:
        """对比学生结果和标准答案（无序：行集相等即可）。"""
        student_norm = self._normalize_result(student_result)
        correct_norm = self._normalize_result(correct_result)
        return self._compare_normalized(student_norm, correct_norm, ordered=False)

    def compare_results_ordered(
        self, student_result: list[dict[str, Any]], correct_result: list[dict[str, Any]]
    ) -> tuple[bool, str]:
        """按行序严格对比（用于含 ORDER BY 的题目：等价性+逻辑性+顺序一致）。"""
        student_norm = self._normalize_result_keep_order(student_result)
        correct_norm = self._normalize_result_keep_order(correct_result)
        return self._compare_normalized(student_norm, correct_norm, ordered=True)

    async def judge_sql(
        self, student_sql: str, correct_sql: str
    ) -> tuple[bool, str]:
        """完整的 SQL 判题流程。

        :param student_sql: 学生的 SQL 语句
        :param correct_sql: 标准答案 SQL 语句
        :return: (是否正确, 错误描述)
        """
        try:
            # 执行学生 SQL
            student_result = await self.execute_sql_safely(student_sql)
        except SQLJudgeError as e:
            return False, f"学生 SQL 执行失败: {str(e)}"

        try:
            # 执行标准答案 SQL
            correct_result = await self.execute_sql_safely(correct_sql)
        except SQLJudgeError as e:
            return False, f"标准答案 SQL 执行失败: {str(e)}"

        # 对比结果：标准答案含 ORDER BY 时按行序严格比较（等价性+逻辑性+顺序），否则按行集比较
        if self._sql_has_order_by(correct_sql):
            is_correct, error_msg = self.compare_results_ordered(student_result, correct_result)
        else:
            is_correct, error_msg = self.compare_results_unordered(student_result, correct_result)

        return is_correct, error_msg


__all__ = ["SQLJudgeService", "SQLJudgeError"]
