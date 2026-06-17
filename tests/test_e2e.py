"""端到端集成测试。

模拟完整业务流：分数 → 位次 → 候选 → 推荐 → 导出 → 文件验证。
"""
from pathlib import Path

import pandas as pd
import pytest

from src.data_loader import load_programs, load_score_rank
from src.exporter import to_csv, to_dataframe, to_excel
from src.models import Candidate
from src.rank_lookup import score_to_rank
from src.recommender import recommend, summary


class TestE2E:
    def test_full_flow_phys_chem_bio(self, tmp_path):
        """完整流程：物理+化学+生物考生。"""
        sr = load_score_rank(2025)
        progs = load_programs()
        score = 595
        rank = score_to_rank(score, sr)
        cand = Candidate(
            score=score, rank=rank,
            selected_subjects=["物理", "化学", "生物"],
        )
        recs = recommend(cand, progs, top_n=80)
        s = summary(recs)
        # 至少有合理数量（数据规模有限）
        assert s["total"] > 0
        # 验证 tier 字段合法
        for r in recs:
            assert r.tier in ("冲", "稳", "保")
            assert 0 < r.probability <= 1
        # 验证排序：冲→稳→保
        tier_order = {"冲": 0, "稳": 1, "保": 2}
        for i in range(1, len(recs)):
            assert tier_order[recs[i - 1].tier] <= tier_order[recs[i].tier]

    def test_export_xlsx(self, tmp_path):
        """导出 xlsx → 文件存在 + 可读回。"""
        sr = load_score_rank(2025)
        progs = load_programs()
        cand = Candidate(score=600, rank=score_to_rank(600, sr),
                         selected_subjects=["物理", "化学", "生物"])
        recs = recommend(cand, progs, top_n=80)
        out = to_excel(recs, tmp_path / "志愿表.xlsx")
        assert out.exists()
        df = pd.read_excel(out, engine="openpyxl")
        assert len(df) == len(recs)
        assert "层次" in df.columns
        assert "院校" in df.columns
        assert "专业" in df.columns

    def test_export_csv(self, tmp_path):
        """导出 CSV → 文件存在 + UTF-8 BOM。"""
        sr = load_score_rank(2025)
        progs = load_programs()
        cand = Candidate(score=600, rank=score_to_rank(600, sr),
                         selected_subjects=["物理", "化学", "生物"])
        recs = recommend(cand, progs, top_n=80)
        out = to_csv(recs, tmp_path / "志愿表.csv")
        assert out.exists()
        content = out.read_bytes()
        # UTF-8 BOM
        assert content[:3] == b"\xef\xbb\xbf"
        # 含中文
        assert "院校".encode("utf-8") in content

    def test_dataframe_columns_complete(self):
        """DataFrame 必须包含所有关键列。"""
        sr = load_score_rank(2025)
        progs = load_programs()
        cand = Candidate(score=600, rank=score_to_rank(600, sr),
                         selected_subjects=["物理", "化学", "生物"])
        recs = recommend(cand, progs, top_n=80)
        df = to_dataframe(recs)
        required = ["序号", "层次", "院校", "专业", "城市", "学制", "学费",
                    "2026计划数", "2025最低位次", "2025最低分",
                    "2024最低位次", "2023最低位次", "位次差", "录取概率"]
        for col in required:
            assert col in df.columns, f"缺少列：{col}"

    def test_history_only_考生(self):
        """选科为「历史+政治+地理」时，所有推荐必须是不限选科或仅要求这三门的专业。"""
        sr = load_score_rank(2025)
        progs = load_programs()
        cand = Candidate(score=550, rank=score_to_rank(550, sr),
                         selected_subjects=["历史", "政治", "地理"])
        recs = recommend(cand, progs, top_n=80)
        for r in recs:
            req = set(r.program.required_subjects)
            assert req.issubset({"历史", "政治", "地理"}), \
                f"专业 {r.program.name} 选科要求 {req} 不符合历史类考生"
