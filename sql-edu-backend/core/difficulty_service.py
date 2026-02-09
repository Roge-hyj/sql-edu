"""题目难度动态计算：教师基础难度 + 客观数据（提交/对话） + 学生主观评分，波动尽量小，数据量大时可较大幅度调整。难度统一为 1～10。"""


def compute_display_difficulty(
    teacher_difficulty: int,
    total_submissions: int,
    correct_submissions: int,
    total_chat_messages: int,
    feedback_count: int,
    avg_student_rating: float | None,
) -> float:
    """计算展示用难度（1～10），用于前端显示与限时推算。

    - 教师创建时的 difficulty（1～10）奠定基础。
    - 客观：该题历史提交次数、AI 对话次数（越多往往越难）。
    - 主观：学生正确完成后的 1～10 评分，直接采用。
    - 波动尽量小：数据少时以教师难度为主；数据多时可较大幅度采纳客观+主观。
    """
    base = float(max(1, min(10, teacher_difficulty)))

    # 客观分量：提交次数与对话次数（归一化到约 1～10）
    submissions = total_submissions or 0
    correct = correct_submissions or 0
    chats = total_chat_messages or 0
    raw_objective = 0.0
    if correct > 0:
        raw_objective = (submissions / correct) * 0.5 + min(chats / max(correct, 1) * 0.2, 4.0)
    else:
        raw_objective = min(submissions * 0.1 + chats * 0.01, 9.0)
    objective_norm = max(1.0, min(10.0, 1.0 + raw_objective))

    # 主观分量：学生评分已是 1～10，直接采用
    if avg_student_rating is not None and feedback_count > 0:
        subjective_norm = max(1.0, min(10.0, avg_student_rating))
    else:
        subjective_norm = base

    n = total_submissions + feedback_count
    if n < 5:
        w = 0.1
    elif n < 15:
        w = 0.25
    elif n < 40:
        w = 0.4
    else:
        w = 0.55

    combined = (1.0 - w) * base + w * (0.5 * objective_norm + 0.5 * subjective_norm)
    return round(max(1.0, min(10.0, combined)), 1)


def suggested_time_seconds(display_difficulty: float, _teacher_time_limit: int | None = None) -> int:
    """限时挑战时长（秒），完全根据题目难度推算。

    这里改为：题目越难，建议用时越长。
    粗略映射：难度 1～10 -> 约 3～10 分钟。
    """
    d = max(1.0, min(10.0, display_difficulty))
    # 线性映射到 [180s, 600s]，即 [3 分钟, 10 分钟]
    return int(120 + 48 * d)

