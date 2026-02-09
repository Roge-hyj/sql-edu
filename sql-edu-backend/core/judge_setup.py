"""判题前自动建表：根据题目的 schema_preview 在判题库中创建表并插入示例数据。"""

import json
import logging
import re
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

logger = logging.getLogger(__name__)


def _infer_mysql_type(col_name: str, sample_value: Any) -> str:
    """根据列名和示例值推断 MySQL 类型。"""
    name_lower = (col_name or "").lower()
    if name_lower == "id":
        return "INT NOT NULL AUTO_INCREMENT PRIMARY KEY"
    if name_lower.endswith("_id"):
        return "INT NOT NULL"
    if "amount" in name_lower or "price" in name_lower or "sum" in name_lower:
        return "DECIMAL(12,2) DEFAULT NULL"
    if name_lower.endswith("_at") or name_lower in ("created_at", "updated_at", "date", "time"):
        return "DATETIME DEFAULT NULL"
    if sample_value is None:
        return "VARCHAR(255) DEFAULT NULL"
    if isinstance(sample_value, bool):
        return "TINYINT(1) DEFAULT NULL"
    if isinstance(sample_value, int):
        return "INT DEFAULT NULL"
    if isinstance(sample_value, (float,)):
        return "DECIMAL(12,2) DEFAULT NULL"
    if isinstance(sample_value, str) and re.match(r"^\d{4}-\d{2}-\d{2}[T ]?\d{2}:\d{2}", sample_value):
        return "DATETIME DEFAULT NULL"
    return "VARCHAR(255) DEFAULT NULL"


def _escape_sql_value(v: Any) -> str:
    """将 Python 值转成 SQL 字面量（防注入、引号转义）。"""
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v).replace("\\", "\\\\").replace("'", "''")
    return f"'{s}'"


def generate_init_sql_from_schema_preview(schema_preview: str | None) -> str | None:
    """从 schema_preview JSON 生成建表与插入 SQL（DROP TABLE + CREATE TABLE + INSERT）。

    schema_preview 格式: {"tables":[{"name":"orders","columns":["id",...],"rows":[{...}]}]}
    每次判题前先删除旧表再重建，确保表结构与 schema_preview 一致。
    """
    if not schema_preview or not schema_preview.strip():
        return None
    try:
        data = json.loads(schema_preview)
    except json.JSONDecodeError:
        return None
    tables = data.get("tables")
    if not isinstance(tables, list) or not tables:
        return None

    statements: list[str] = []
    for tbl in tables:
        if not isinstance(tbl, dict):
            continue
        name = tbl.get("name")
        columns = tbl.get("columns")
        rows = tbl.get("rows")
        if not name or not isinstance(columns, list) or not columns:
            continue
        if not isinstance(rows, list):
            rows = []
        # 表名、列名仅允许字母数字下划线，防止注入
        safe_name = re.sub(r"[^\w]", "", str(name))
        if not safe_name:
            continue
        col_defs: list[str] = []
        for i, col in enumerate(columns):
            if not isinstance(col, str):
                continue
            safe_col = re.sub(r"[^\w]", "", col)
            if not safe_col:
                continue
            sample = None
            for row in rows:
                if isinstance(row, dict) and col in row:
                    sample = row[col]
                    break
            type_str = _infer_mysql_type(safe_col, sample)
            col_defs.append(f"`{safe_col}` {type_str}")
        if not col_defs:
            continue
        # 先删除旧表，确保使用最新的表结构（避免旧表缺少新列导致判题失败）
        drop_sql = f"DROP TABLE IF EXISTS `{safe_name}`"
        statements.append(drop_sql)
        create_sql = f"CREATE TABLE `{safe_name}` (\n  " + ",\n  ".join(col_defs) + "\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"
        statements.append(create_sql)

        if not rows:
            continue
        # INSERT ... ON DUPLICATE KEY UPDATE 保证重复执行不报错
        insert_cols = [c for c in columns if isinstance(c, str) and re.match(r"^\w+$", c)]
        if not insert_cols:
            continue
        cols_str = ", ".join(f"`{c}`" for c in insert_cols)
        value_rows: list[str] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            vals = [_escape_sql_value(row.get(c)) for c in insert_cols]
            value_rows.append("(" + ", ".join(vals) + ")")
        if not value_rows:
            continue
        has_pk = "id" in [c.lower() for c in insert_cols]
        if has_pk:
            update_parts = [f"`{c}`=VALUES(`{c}`)" for c in insert_cols]
            insert_sql = (
                f"INSERT INTO `{safe_name}` ({cols_str}) VALUES\n  "
                + ",\n  ".join(value_rows)
                + "\nON DUPLICATE KEY UPDATE " + ", ".join(update_parts)
            )
        else:
            insert_sql = (
                f"INSERT IGNORE INTO `{safe_name}` ({cols_str}) VALUES\n  "
                + ",\n  ".join(value_rows)
            )
        statements.append(insert_sql)

    if not statements:
        return None
    return ";\n".join(statements) + ";"


def _is_safe_setup_statement(stmt: str) -> bool:
    """只允许 DROP TABLE IF EXISTS、CREATE TABLE 和 INSERT [IGNORE] INTO，且表名仅字母数字下划线。"""
    s = stmt.strip()
    if not s:
        return False
    lower = s.lower()
    # 允许 DROP TABLE IF EXISTS（仅用于判题前重建表）
    if lower.startswith("drop table if exists"):
        return bool(re.match(r"drop\s+table\s+if\s+exists\s+`?\w+`?\s*$", lower))
    if lower.startswith("create table"):
        return bool(re.match(r"create\s+table\s+(?:if\s+not\s+exists\s+)?`?\w+`?\s*\(", lower))
    if "insert" in lower[:20] and "into" in lower[:25]:
        return bool(re.match(r"insert\s+(?:ignore\s+)?into\s+`?\w+`?\s*\(", lower))
    return False


async def execute_setup_sql(session: AsyncSession, init_sql: str) -> None:
    """在判题库中执行建表/插入 SQL。仅允许 DROP TABLE IF EXISTS、CREATE TABLE 与 INSERT INTO。"""
    if not init_sql or not init_sql.strip():
        return
    # 按分号拆分，忽略空语句和注释
    parts = re.split(r";\s*(?=(?:[^']*'[^']*')*[^']*$)", init_sql)
    for part in parts:
        stmt = part.strip()
        if not stmt or stmt.startswith("--"):
            continue
        if not _is_safe_setup_statement(stmt):
            continue
        try:
            await session.execute(text(stmt))
        except Exception as e:
            # 记录错误但继续执行，判题时若表结构有问题会报错
            logger.warning(f"执行建表/插入语句失败: {stmt[:100]}... 错误: {e}")
    await session.flush()
