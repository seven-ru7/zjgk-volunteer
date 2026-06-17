"""选科匹配测试。"""
import pytest

from src.matcher import is_eligible, filter_eligible
from src.models import Candidate, Program


class TestIsEligible:
    def test_no_requirement(self):
        """专业不限选科 → 任何考生都满足。"""
        assert is_eligible([], ["物理", "化学", "生物"]) is True
        assert is_eligible([], ["历史", "政治", "地理"]) is True

    def test_single_subject_match(self):
        assert is_eligible(["物理"], ["物理", "化学", "生物"]) is True

    def test_single_subject_not_match(self):
        assert is_eligible(["物理"], ["历史", "政治", "地理"]) is False

    def test_two_subjects_subset(self):
        assert is_eligible(["物理", "化学"], ["物理", "化学", "生物"]) is True

    def test_two_subjects_partial(self):
        # 缺化学
        assert is_eligible(["物理", "化学"], ["物理", "生物", "历史"]) is False

    def test_three_subjects_exact(self):
        assert is_eligible(["物理", "化学", "生物"], ["物理", "化学", "生物"]) is True

    def test_empty_selected(self):
        assert is_eligible(["物理"], []) is False

    def test_none_inputs(self):
        assert is_eligible(None, ["物理"]) is True
        assert is_eligible(["物理"], None) is False


class TestFilterEligible:
    def _make_programs(self):
        return [
            Program("P1", "计算机", "A大学", "杭州", 4, 6000, ["物理"], 100, []),
            Program("P2", "临床医学", "B大学", "北京", 5, 7000, ["化学", "生物"], 80, []),
            Program("P3", "汉语言文学", "C大学", "南京", 4, 5500, [], 60, []),
            Program("P4", "数学", "D大学", "上海", 4, 5500, [], 50, []),
        ]

    def test_physics_chem_bio(self):
        """物理+化学+生物 → 可报 P1(物理), P2(化学+生物), P3/P4(不限)"""
        cand = Candidate(score=600, selected_subjects=["物理", "化学", "生物"])
        eligible = filter_eligible(self._make_programs(), cand)
        assert {p.program_id for p in eligible} == {"P1", "P2", "P3", "P4"}

    def test_history_only(self):
        """历史+政治+地理 → 不能报 P1(物理) P2(化学+生物)，可报 P3/P4"""
        cand = Candidate(score=550, selected_subjects=["历史", "政治", "地理"])
        eligible = filter_eligible(self._make_programs(), cand)
        assert {p.program_id for p in eligible} == {"P3", "P4"}

    def test_physics_only(self):
        """物理+政治+地理 → 可报 P1(物理) 和 P3/P4(不限)，不能报 P2"""
        cand = Candidate(score=550, selected_subjects=["物理", "政治", "地理"])
        eligible = filter_eligible(self._make_programs(), cand)
        assert {p.program_id for p in eligible} == {"P1", "P3", "P4"}
