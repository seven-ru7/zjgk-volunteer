"""选科匹配。

浙江新高考规则：专业的选科要求（1-3 门）必须被考生的 3 门选考科目完全覆盖。
例如：专业要求「物理+化学」，考生选了「物理+化学+生物」→ 合格。
"""
from __future__ import annotations

from typing import List


def is_eligible(required_subjects: List[str], selected_subjects: List[str]) -> bool:
    """判断考生选考科目是否满足专业要求。

    语义：required_subjects ⊆ selected_subjects

    Args:
        required_subjects: 专业要求的选科科目（0-3 门）；空列表表示不限
        selected_subjects: 考生选考的 3 门科目

    Returns:
        True 表示考生可填报该专业
    """
    required = set(required_subjects or [])
    selected = set(selected_subjects or [])
    return required.issubset(selected)


def filter_eligible(programs, candidate):
    """便捷函数：过滤出考生可填报的所有专业。

    Args:
        programs: Program 列表
        candidate: Candidate 对象（含 selected_subjects）

    Returns:
        Program 子集
    """
    return [p for p in programs if is_eligible(p.required_subjects, candidate.selected_subjects)]
