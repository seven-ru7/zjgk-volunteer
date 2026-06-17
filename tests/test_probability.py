"""录取概率估算测试。"""
import pytest

from src.probability import estimate, estimate_legacy
from src.models import Program


def make_program(history):
    """快速构造一个 Program。"""
    return Program(
        program_id="TEST",
        name="测试",
        institution="测试大学",
        city="北京",
        duration_years=4,
        tuition=5000,
        required_subjects=[],
        plan_quota_2026=10,
        history=history,
    )


class TestEstimate:
    def test_tier_safe(self):
        """考生位次远好于历史最低 → 保档"""
        p = make_program([{"year": 2025, "min_rank": 50000, "min_score": 580}])
        # 考生位次 30000（delta = -20000 < -8000）
        r = estimate(30000, p)
        assert r.tier == "保"
        assert r.probability == 0.95
        assert r.delta_rank == -20000

    def test_tier_stable(self):
        """考生位次接近历史 → 稳档"""
        p = make_program([{"year": 2025, "min_rank": 50000, "min_score": 580}])
        # 考生位次 51000（delta = 1000 ∈ [-8000, 2000)）
        r = estimate(51000, p)
        assert r.tier == "稳"
        assert r.probability == 0.75
        assert r.delta_rank == 1000

    def test_tier_rush_mid(self):
        """考生位次较靠后 → 冲档中段"""
        p = make_program([{"year": 2025, "min_rank": 50000, "min_score": 580}])
        # 考生位次 55000（delta = 5000 ∈ [2000, 10000)）
        r = estimate(55000, p)
        assert r.tier == "冲"
        assert r.probability == 0.45
        assert r.delta_rank == 5000

    def test_tier_rush_far(self):
        """考生位次远靠后 → 冲档低概率"""
        p = make_program([{"year": 2025, "min_rank": 50000, "min_score": 580}])
        # 考生位次 70000（delta = 20000 > 10000）
        r = estimate(70000, p)
        assert r.tier == "冲"
        assert r.probability == 0.10
        assert r.delta_rank == 20000

    def test_no_rank(self):
        """位次为 None → 中性"""
        p = make_program([{"year": 2025, "min_rank": 50000, "min_score": 580}])
        r = estimate(None, p)
        assert r.tier == "稳"
        assert r.probability == 0.5

    def test_no_history(self):
        """专业无历史 → 中性"""
        p = make_program([])
        r = estimate(50000, p)
        assert r.tier == "稳"
        assert r.probability == 0.5

    def test_use_other_year(self):
        """指定年份无数据 → 用最近一年"""
        p = make_program([
            {"year": 2024, "min_rank": 50000, "min_score": 580},
            {"year": 2023, "min_rank": 55000, "min_score": 575},
        ])
        # 指定 2025 但没数据 → 应回退到 2024
        r = estimate(52000, p, year=2025)
        assert r.delta_rank == 2000

    def test_boundary_minus_8000(self):
        """边界：delta = -8000 应归入稳档（< -8000 是保）"""
        p = make_program([{"year": 2025, "min_rank": 50000, "min_score": 580}])
        # delta = -8000 → 不是 < -8000 → 应归稳档
        r = estimate(42000, p)
        assert r.tier == "稳"

    def test_boundary_2000(self):
        """边界：delta = 2000 应归入冲档（< 2000 是稳）"""
        p = make_program([{"year": 2025, "min_rank": 50000, "min_score": 580}])
        r = estimate(52000, p)
        assert r.tier == "冲"

    def test_legacy_interface(self):
        p = make_program([{"year": 2025, "min_rank": 50000, "min_score": 580}])
        prob, delta, tier = estimate_legacy(51000, p)
        assert (prob, delta, tier) == (0.75, 1000, "稳")
