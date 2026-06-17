"""冲稳保推荐算法测试。"""
import pytest

from src.recommender import recommend, summary
from src.models import Candidate, Program


def make_program(pid, name, inst, min_rank, required=None):
    return Program(
        program_id=pid,
        name=name,
        institution=inst,
        city="杭州",
        duration_years=4,
        tuition=5000,
        required_subjects=required or [],
        plan_quota_2026=10,
        history=[{"year": 2025, "min_rank": min_rank, "min_score": 600}],
    )


@pytest.fixture
def programs():
    """13 个专业，覆盖各档位（考生位次 50000）。

    概率档位定义：
        delta < -8000  → 保（95%）
        -8000 ≤ delta < 2000  → 稳（75%）
        2000 ≤ delta < 10000  → 冲（45%）
        delta ≥ 10000  → 冲（10%）

    delta = 考生位次 50000 - min_rank
    """
    return [
        # 冲档 10%（delta ≥ 10000）：min_rank ≤ 40000
        make_program("R1", "CS", "A大学", min_rank=20000),
        make_program("R2", "SE", "B大学", min_rank=25000),
        make_program("R3", "AI", "C大学", min_rank=30000),
        # 冲档 45%（delta ∈ [2000, 10000)）：min_rank ∈ [40000, 48000]
        make_program("R4", "大数据", "C大学", min_rank=42000),
        make_program("R5", "网安", "D大学", min_rank=45000),
        make_program("R6", "软件测试", "E大学", min_rank=48000),
        # 稳档 75%（delta ∈ [-8000, 2000)）：min_rank ∈ [48000, 58000]
        make_program("S1", "数学", "F大学", min_rank=51000),
        make_program("S2", "物理", "G大学", min_rank=54000),
        make_program("S3", "化学", "H大学", min_rank=56000),
        make_program("S4", "生物", "I大学", min_rank=57000),
        # 保档 95%（delta < -8000）：min_rank ≥ 58000
        make_program("P1", "农学", "J大学", min_rank=65000),
        make_program("P2", "林学", "K大学", min_rank=70000),
        make_program("P3", "动物科学", "L大学", min_rank=80000),
    ]


class TestRecommend:
    def test_basic_counts(self, programs):
        """3 冲10% + 3 冲45% + 4 稳 + 3 保 = 13 条（小于 80，全部入选）"""
        cand = Candidate(score=600, rank=50000, selected_subjects=["物理", "化学", "生物"])
        recs = recommend(cand, programs, top_n=80)
        assert len(recs) == 13
        s = summary(recs)
        assert s["rush"] == 6   # 3 + 3
        assert s["stable"] == 4
        assert s["safe"] == 3

    def test_top_n_limit(self, programs):
        """生成更多专业，验证 top_n 限制。"""
        many = programs * 10
        cand = Candidate(score=600, rank=50000, selected_subjects=[])
        recs = recommend(cand, many, top_n=80)
        assert len(recs) == 80
        # 默认比例 30/50/20 = 24/40/16
        s = summary(recs)
        assert s["total"] == 80
        assert s["rush"] == 24
        assert s["stable"] == 40
        assert s["safe"] == 16

    def test_subjects_filter(self, programs):
        """选科不匹配 → 全部过滤。"""
        for p in programs:
            p.required_subjects = ["物理"]
        cand = Candidate(score=600, rank=50000, selected_subjects=["历史", "政治", "地理"])
        recs = recommend(cand, programs)
        assert len(recs) == 0

    def test_city_filter(self, programs):
        cand = Candidate(score=600, rank=50000, selected_subjects=[])
        recs = recommend(cand, programs, cities=["杭州"])
        assert len(recs) == 13

    def test_keyword_filter(self, programs):
        cand = Candidate(score=600, rank=50000, selected_subjects=[])
        recs = recommend(cand, programs, keywords=["CS"])
        assert len(recs) == 1
        assert recs[0].program.program_id == "R1"

    def test_custom_ratio(self, programs):
        many = programs * 10
        cand = Candidate(score=600, rank=50000, selected_subjects=[])
        recs = recommend(cand, many, top_n=80, ratio=(0.50, 0.30, 0.20))
        assert len(recs) == 80
        s = summary(recs)
        assert s["rush"] == 40
        assert s["stable"] == 24
        assert s["safe"] == 16

    def test_ordering(self, programs):
        cand = Candidate(score=600, rank=50000, selected_subjects=[])
        recs = recommend(cand, programs, top_n=80)
        tiers = [r.tier for r in recs]
        assert tiers == ["冲"] * 6 + ["稳"] * 4 + ["保"] * 3

    def test_no_programs(self):
        cand = Candidate(score=600, rank=50000, selected_subjects=[])
        recs = recommend(cand, [], top_n=80)
        assert recs == []


class TestSummary:
    def test_empty(self):
        s = summary([])
        assert s["total"] == 0
        assert s["avg_probability"] == 0.0

    def test_mixed(self, programs):
        cand = Candidate(score=600, rank=50000, selected_subjects=[])
        recs = recommend(cand, programs, top_n=80)
        s = summary(recs)
        assert s["total"] == 13
        assert s["rush"] + s["stable"] + s["safe"] == 13
        assert 0 < s["avg_probability"] < 1
