"""分数↔位次互转测试。"""
import pytest

from src.rank_lookup import score_to_rank, rank_to_score


# 简化测试表（基于 2025 浙江实际分布特征）
SAMPLE_TABLE = {
    "750": 200,
    "700": 2000,
    "650": 21000,
    "600": 88500,
    "550": 206000,
    "500": 373500,
    "490": 413000,
    "450": 591000,
    "400": 858500,
    "300": 1700000,
    "200": 2700000,
}


class TestScoreToRank:
    def test_exact_match(self):
        assert score_to_rank(600, SAMPLE_TABLE) == 88500
        assert score_to_rank(700, SAMPLE_TABLE) == 2000

    def test_interpolation(self):
        # 600 → 88500, 650 → 21000
        # 625 中点约 54750
        rank = score_to_rank(625, SAMPLE_TABLE)
        assert 21000 < rank < 88500

    def test_above_max(self):
        # 超过 750 → 返回最小累计人数
        assert score_to_rank(800, SAMPLE_TABLE) == 200

    def test_below_min(self):
        # 低于 200 → 返回最大累计人数
        assert score_to_rank(100, SAMPLE_TABLE) == 2700000

    def test_zero_or_negative(self):
        assert score_to_rank(0, SAMPLE_TABLE) == 0
        assert score_to_rank(-10, SAMPLE_TABLE) == 0

    def test_empty_table(self):
        assert score_to_rank(600, {}) == 0

    def test_string_keys(self):
        """data_loader 已归一化，但保险起见测试 str key 也支持。"""
        assert score_to_rank(600, SAMPLE_TABLE) == 88500


class TestRankToScore:
    def test_exact_match(self):
        assert rank_to_score(88500, SAMPLE_TABLE) == 600

    def test_interpolation(self):
        # 88500 → 600, 21000 → 650
        # 54750 中点约 625
        score = rank_to_score(54750, SAMPLE_TABLE)
        assert 600 < score < 650

    def test_below_min_rank(self):
        # 位次 100（比最小累计人数 200 还小）→ 返回最高分
        assert rank_to_score(100, SAMPLE_TABLE) == 750

    def test_above_max_rank(self):
        # 位次 5,000,000（超过最大累计人数）→ 返回最低分
        assert rank_to_score(5_000_000, SAMPLE_TABLE) == 200

    def test_zero_rank(self):
        assert rank_to_score(0, SAMPLE_TABLE) == 0

    def test_empty_table(self):
        assert rank_to_score(100, {}) == 0


class TestRoundTrip:
    """测试互转的近似闭合性。"""

    def test_score_to_rank_to_score(self):
        """score → rank → score 应该近似回到原分数。"""
        for s in [400, 500, 550, 600, 650, 700]:
            r = score_to_rank(s, SAMPLE_TABLE)
            s2 = rank_to_score(r, SAMPLE_TABLE)
            # 由于位次是离散累计人数，存在 ±1-2 分误差
            assert abs(s - s2) <= 2, f"score {s} → rank {r} → score {s2}"
