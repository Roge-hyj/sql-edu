"""测试支架计算逻辑。"""

import pytest
from core.scaffolding import calculate_hint_level, get_scaffolding_instruction, get_ability_adjustment


class TestCalculateHintLevel:
    """测试支架等级计算。"""

    def test_first_attempt(self):
        """第一次尝试（0 次失败）应该返回低支架。"""
        assert calculate_hint_level(0) == 1

    def test_one_failure(self):
        """失败 1 次应该仍为低支架。"""
        assert calculate_hint_level(1) == 1

    def test_two_failures(self):
        """失败 2 次应该返回中支架。"""
        assert calculate_hint_level(2) == 2

    def test_three_failures(self):
        """失败 3 次应该返回中支架。"""
        assert calculate_hint_level(3) == 2

    def test_four_failures(self):
        """失败 4 次应该返回高支架。"""
        assert calculate_hint_level(4) == 3

    def test_many_failures(self):
        """失败多次应该返回高支架。"""
        assert calculate_hint_level(10) == 3

    def test_ability_adjustment(self):
        """能力调整应在 1～3 范围内。"""
        assert calculate_hint_level(0, 1) == 2
        assert calculate_hint_level(2, -1) == 1
        assert calculate_hint_level(2, 1) == 3


class TestGetAbilityAdjustment:
    """测试能力调整。"""

    def test_insufficient_data(self):
        """样本不足不调整。"""
        assert get_ability_adjustment(0.5, 3) == 0

    def test_weak_student(self):
        """正确率低且提交多时提高支架。"""
        assert get_ability_adjustment(0.2, 10) == 1

    def test_strong_student(self):
        """正确率高且提交多时降低支架。"""
        assert get_ability_adjustment(0.8, 10) == -1

    def test_middle(self):
        """中等不调整。"""
        assert get_ability_adjustment(0.5, 10) == 0


class TestGetScaffoldingInstruction:
    """测试支架指导语生成。"""

    def test_low_scaffolding(self):
        """低支架指导语应只讲逻辑、不给关键字。"""
        instruction = get_scaffolding_instruction(1)
        assert "低支架" in instruction
        assert "逻辑" in instruction

    def test_medium_scaffolding(self):
        """中支架指导语应以逻辑为主、不直接给解法。"""
        instruction = get_scaffolding_instruction(2)
        assert "中支架" in instruction
        assert "逻辑" in instruction

    def test_high_scaffolding(self):
        """高支架指导语可适量写出关键字并举例，仍严禁泄露本题完整代码。"""
        instruction = get_scaffolding_instruction(3)
        assert "高支架" in instruction
        assert "关键字" in instruction or "举例" in instruction
        assert "严禁" in instruction or "禁止" in instruction

    def test_invalid_level(self):
        """无效等级应该返回默认（低支架）。"""
        instruction = get_scaffolding_instruction(99)
        assert "低支架" in instruction
