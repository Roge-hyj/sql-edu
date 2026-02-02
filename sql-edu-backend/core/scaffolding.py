"""支架式教学：根据失败次数动态调整提示深度。"""


def calculate_hint_level(
    failure_count: int,
    ability_adjustment: int = 0,
) -> int:
    """根据本题失败次数计算基础支架等级，并可结合能力调整。

    支架等级说明：
    - 1 (低支架)：只讲逻辑、不给关键字
    - 2 (中支架)：缩小错误范围，仍以逻辑为主
    - 3 (高支架)：可适量写出关键字并举例

    阈值（放宽）：0 次失败低支架，1 次失败低支架，2～3 次中支架，4 次以上高支架。

    :param failure_count: 该用户在该题目上的历史失败次数
    :param ability_adjustment: 根据学生全局能力做的调整（-1/0/+1），正数表示提高支架
    :return: 支架等级 (1, 2, 或 3)
    """
    if failure_count <= 1:
        base = 1  # 0 或 1 次失败，给低支架
    elif failure_count <= 3:
        base = 2  # 2～3 次失败，给中支架
    else:
        base = 3  # 4 次及以上，给高支架

    level = base + ability_adjustment
    return max(1, min(3, level))


def get_ability_adjustment(success_rate: float, total_submissions: int) -> int:
    """根据学生全局答题表现计算支架调整量，用于动态调整指导强度。

    - 表现较弱（提交较多且正确率低）：提高支架，多给一点引导
    - 表现较好（提交较多且正确率高）：可适当降低支架，少一点提示
    - 样本不足或中等：不调整

    :param success_rate: 历史总正确率 (0～1)
    :param total_submissions: 历史总提交次数
    :return: 调整量 -1、0 或 +1
    """
    if total_submissions < 5:
        return 0
    if success_rate < 0.35:
        return 1   # 较弱，提高支架
    if success_rate > 0.7:
        return -1  # 较好，适当降低支架
    return 0


def get_scaffolding_instruction(hint_level: int) -> str:
    """根据支架等级生成 Prompt 指导语。

    原则：初始只讲逻辑差异，不直接给 SQL 关键字/语法；学生追问时可讲语法并举例，但严禁泄露本题答案。
    :param hint_level: 支架等级 (1, 2, 或 3)
    :return: 用于嵌入 System Prompt 的指导语
    """
    instructions = {
        1: (
            "【低支架模式】这是学生第一次尝试，只讲逻辑、不给关键字或语法：\n"
            "- 用自然语言描述「题目要求」与「学生当前写法」的逻辑差异，例如：题目要求从大到小排序而你的写法没有体现排序、题目要求只取前几条而你的结果没有限制条数。\n"
            "- 严禁直接说出 ORDER BY、DESC、LIMIT、GROUP BY 等 SQL 关键字或给出与本题相关的代码片段。\n"
            "- 可用反问或邀请提问，如：你知道怎么实现「从大到小」吗？如果不知道用哪个关键字，可以在下方对话框问我。\n"
            "- 鼓励学生自己先想逻辑，再在对话中主动问语法。"
        ),
        2: (
            "【中支架模式】学生已失败 1～2 次，仍以逻辑为主、不直接给本题解法：\n"
            "- 明确说出「哪一方面的逻辑」与题目不符（例如：排序方向、条数限制、条件范围），不要指出具体子句名或关键字。\n"
            "- 严禁直接给出 ORDER BY、DESC、LIMIT 等关键字或本题可用的代码片段。\n"
            "- 可以问学生：你知道怎么实现降序吗？你知道怎么只取前几条吗？并提示「不知道可以问我」。\n"
            "- 若学生主动问「降序用什么」「怎么限制条数」，再在对话中回答语法并举例（举例用其他表/字段，不泄露本题答案）。"
        ),
        3: (
            "【高支架模式】学生已失败 3 次以上，可以适量、少量写出 SQL 关键字并举例介绍功能：\n"
            "- 可以写出 ORDER BY、DESC、LIMIT 等关键字，并举例说明其作用（如「ORDER BY 用于排序，DESC 表示降序」「LIMIT 用于限制返回条数，通常写在语句末尾」）。\n"
            "- 举例必须与本题无关：用其他表名、其他字段名举例（如用 score、name 等），不得使用本题涉及的 users、id 等与答案直接相关的表/字段。\n"
            "- 严禁泄露本题完整代码或可直接套用的片段（如不得写出 ORDER BY id DESC LIMIT 3 这类本题答案）。\n"
            "- 可以结合逻辑提示，如「你需要在合适位置加上排序，关键字是 ORDER BY，降序用 DESC」「限制条数用 LIMIT，一般写在最后」，再配一道与本题无关的小例子说明用法。"
        ),
    }

    return instructions.get(hint_level, instructions[1])


__all__ = ["calculate_hint_level", "get_scaffolding_instruction", "get_ability_adjustment"]
