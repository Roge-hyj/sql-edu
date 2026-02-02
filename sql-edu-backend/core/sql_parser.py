"""从标准答案 SQL 中解析 SELECT 输出列名，用于自动填充「要求的结果列名」。"""

import re
from typing import List


def infer_output_columns_from_sql(sql: str) -> str | None:
    """从 SELECT 语句中解析输出列名（含别名），返回逗号分隔的列名字符串。

    例如：SELECT id AS order_id, user_id, amount AS order_amount, sum(amount) OVER(...) AS cumulative_amount
    返回：order_id, user_id, order_amount, cumulative_amount
    SELECT * 或无法解析时返回 None。
    """
    if not sql or not sql.strip():
        return None
    s = sql.strip()
    # 去掉单行/多行注释，减少干扰
    s = re.sub(r"--[^\n]*", " ", s)
    s = re.sub(r"/\*[\s\S]*?\*/", " ", s)
    s = re.sub(r"\s+", " ", s)
    lower = s.lower()
    if not lower.startswith("select"):
        return None
    # 找到 SELECT 与 FROM 之间的部分（考虑括号深度，避免子查询中的 FROM）
    start = 6  # len("select")
    depth = 0
    i = start
    end_from = -1
    while i < len(s):
        c = s[i]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
        elif depth == 0 and lower[i : i + 5] == " from":
            # 确保 FROM 前是空白或逗号等
            end_from = i
            break
        i += 1
    if end_from < 0:
        return None
    select_list = s[start:end_from].strip()
    if not select_list or select_list.strip() == "*":
        return None
    # 按逗号分割（只在外层深度 0 处分割）
    segments: List[str] = []
    depth = 0
    start_idx = 0
    for i, c in enumerate(select_list):
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
        elif c == "," and depth == 0:
            segments.append(select_list[start_idx:i].strip())
            start_idx = i + 1
    segments.append(select_list[start_idx:].strip())
    names: List[str] = []
    for seg in segments:
        if not seg:
            continue
        # 是否有 AS 别名（不区分大小写）
        as_match = re.search(r"\s+[Aa][Ss]\s+", seg)
        if as_match:
            alias_part = seg[as_match.end() :].strip()
            # 去掉引号、反引号
            alias_part = re.sub(r"^[\"`']|[\"`']$", "", alias_part.strip())
            if alias_part and re.match(r"^[\w]+$", alias_part):
                names.append(alias_part)
                continue
        # 无 AS：取最后一个标识符（如 orders.id -> id, id -> id）
        seg_clean = seg.strip()
        if re.match(r"^\*$", seg_clean):
            return None
        # 去掉尾部括号内容后的最后一个标识符，或整段若为单一标识符
        last_id = re.findall(r"[\w]+", seg_clean)
        if last_id:
            names.append(last_id[-1])
    if not names:
        return None
    return ", ".join(names)
