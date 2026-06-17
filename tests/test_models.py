"""数据模型测试。"""
from src.models import Candidate, Program, Recommendation


class TestCandidate:
    def test_default_constructor(self):
        c = Candidate(score=580)
        assert c.score == 580
        assert c.rank is None
        assert c.selected_subjects == []
        assert c.preferences == {}

    def test_full_constructor(self):
        c = Candidate(
            score=620,
            rank=8500,
            selected_subjects=["物理", "化学", "生物"],
            preferences={"city": ["杭州", "上海"]},
        )
        assert c.score == 620
        assert c.rank == 8500
        assert c.selected_subjects == ["物理", "化学", "生物"]
        assert c.preferences == {"city": ["杭州", "上海"]}

    def test_mutable_defaults_isolated(self):
        """确保 default_factory 不会在实例间共享同一对象。"""
        c1 = Candidate(score=500)
        c2 = Candidate(score=600)
        c1.selected_subjects.append("物理")
        assert c2.selected_subjects == []


class TestProgram:
    def test_required_fields(self):
        p = Program(
            program_id="ZJU-CS-2026",
            name="计算机科学与技术",
            institution="浙江大学",
            city="杭州",
            duration_years=4,
            tuition=6000,
            required_subjects=["物理", "化学"],
            plan_quota_2026=120,
        )
        assert p.program_id == "ZJU-CS-2026"
        assert p.required_subjects == ["物理", "化学"]
        assert p.history == []  # 默认空列表

    def test_with_history(self):
        history = [
            {"year": 2025, "min_rank": 12500, "min_score": 632},
            {"year": 2024, "min_rank": 11800, "min_score": 638},
        ]
        p = Program(
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
        assert len(p.history) == 2
        assert p.history[0]["year"] == 2025


class TestRecommendation:
    def test_construction(self):
        p = Program(
            program_id="T",
            name="X",
            institution="Y",
            city="Z",
            duration_years=4,
            tuition=5000,
            required_subjects=[],
            plan_quota_2026=1,
        )
        r = Recommendation(
            program=p, tier="稳", probability=0.75, delta_rank=-1500
        )
        assert r.tier == "稳"
        assert r.probability == 0.75
        assert r.delta_rank == -1500
        assert r.program is p
