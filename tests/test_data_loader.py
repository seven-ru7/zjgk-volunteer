"""数据加载器测试。"""
import json
import pathlib

import pytest

from src.data_loader import (
    load_score_rank,
    load_programs,
    load_institutions,
    load_admission_history,
    DATA_DIR,
)


@pytest.fixture
def sample_score_rank(tmp_path, monkeypatch):
    """在 tmp_path 下伪造一个 2025 年一分一段表，并 monkeypatch DATA_DIR。"""
    data = {"750": 50, "700": 800, "600": 52529, "500": 180000, "490": 200000}
    fp = tmp_path / "score_rank_2025.json"
    fp.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr("src.data_loader.DATA_DIR", tmp_path)
    return fp


def test_load_score_rank_returns_int_keys(sample_score_rank):
    rank = load_score_rank(2025)
    assert rank[600] == 52529
    assert isinstance(list(rank.keys())[0], int)


def test_load_score_rank_missing_year(tmp_path, monkeypatch):
    monkeypatch.setattr("src.data_loader.DATA_DIR", tmp_path)
    with pytest.raises(FileNotFoundError, match="2024"):
        load_score_rank(2024)


def test_load_programs(tmp_path, monkeypatch):
    sample = [
        {
            "program_id": "ZJU-CS",
            "name": "计算机科学与技术",
            "institution": "浙江大学",
            "city": "杭州",
            "duration_years": 4,
            "tuition": 6000,
            "required_subjects": ["物理"],
            "plan_quota_2026": 100,
            "history": [{"year": 2025, "min_rank": 12500, "min_score": 632}],
        }
    ]
    fp = tmp_path / "programs.json"
    fp.write_text(json.dumps(sample, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr("src.data_loader.DATA_DIR", tmp_path)

    programs = load_programs()
    assert len(programs) == 1
    p = programs[0]
    assert p.program_id == "ZJU-CS"
    assert p.institution == "浙江大学"
    assert p.required_subjects == ["物理"]
    assert p.history[0]["min_rank"] == 12500


def test_load_programs_missing(tmp_path, monkeypatch):
    monkeypatch.setattr("src.data_loader.DATA_DIR", tmp_path)
    with pytest.raises(FileNotFoundError):
        load_programs()


def test_load_institutions(tmp_path, monkeypatch):
    data = [{"name": "浙江大学", "city": "杭州", "tier": "985/211/双一流"}]
    fp = tmp_path / "institutions.json"
    fp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr("src.data_loader.DATA_DIR", tmp_path)
    institutions = load_institutions()
    assert institutions[0]["name"] == "浙江大学"


def test_load_admission_history_missing_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setattr("src.data_loader.DATA_DIR", tmp_path)
    assert load_admission_history() == []
