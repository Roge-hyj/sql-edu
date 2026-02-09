"""学生等级与经验：首次正确完成题目获得经验，经验达标升级，控制升级速度与积极性平衡。"""


def xp_for_next_level(level: int) -> int:
    """从当前等级升到下一级所需经验（当前等级内的进度条上限）。"""
    if level < 1:
        return 100
    return 100 + 50 * (level - 1)


def get_level_from_total(total_experience: int) -> tuple[int, int, int]:
    """根据累计经验计算等级、当前等级内经验、升到下一级所需经验。

    :return: (level, experience_in_level, xp_to_next_level)
    - level: 当前等级（从 1 开始）
    - experience_in_level: 当前等级内已获得的经验（进度条当前值）
    - xp_to_next_level: 升到下一级还需的经验（进度条上限）
    """
    if total_experience <= 0:
        return 1, 0, xp_for_next_level(1)
    level = 1
    consumed = 0
    while True:
        need = xp_for_next_level(level)
        if consumed + need > total_experience:
            exp_in_level = total_experience - consumed
            return level, exp_in_level, need
        consumed += need
        level += 1


def compute_xp_gain(
    question_difficulty: int,
    chat_count: int,
    wrong_attempts_before_correct: int,
    challenge_mode: bool,
) -> int:
    """计算首次正确完成一题获得的经验。

    - 题目难度（1～10）：难度越高经验越多，鼓励挑战。
    - 对话条数：体现思考与投入，适量奖励，有上限。
    - 错误尝试次数：体现修改与成长，适量奖励，有上限。
    - 限时挑战：额外加成，鼓励限时训练。

    数值控制在适量范围，保证升级速度适中、正向反馈明显。
    """
    # 基础经验（完成即得）
    base = 25
    # 难度加成：1～10 对应 +0～+27（约每级 +3）
    difficulty_bonus = min(27, max(0, (question_difficulty - 1) * 3))
    # 对话投入：每 2 条 +1 经验，最多 +12（约 24 条对话封顶）
    chat_bonus = min(12, chat_count // 2)
    # 修改成长：每次错误尝试 +1 经验，最多 +8（避免刷失败）
    attempt_bonus = min(8, wrong_attempts_before_correct)
    total = base + difficulty_bonus + chat_bonus + attempt_bonus
    # 限时挑战加成 50%
    if challenge_mode:
        total = int(total * 1.5)
    return max(1, min(80, total))  # 单题经验控制在 1～80


__all__ = ["xp_for_next_level", "get_level_from_total", "compute_xp_gain"]
