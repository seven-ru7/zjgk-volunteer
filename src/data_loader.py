"""JSON 数据加载器。

所有数据文件位于项目根目录的 data/ 子目录下，按年份命名以便后续替换为真实数据。
"""
from __future__ import annotations

import json
import pathlib
from typing import List

from .models import Program


# 项目根目录 = 本文件父目录的父目录
DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"


def load_score_rank(year: int = 2025) -> dict:
    """加载指定年份的一分一段表。

    Returns:
        dict: {分数(int): 该分及以上累计人数(int)}
        例：{750: 50, 749: 78, ..., 200: 320000}

    Raises:
        FileNotFoundError: 该年份数据文件不存在时，提示用户先运行爬虫或放入文件。
    """
    fp = DATA_DIR / f"score_rank_{year}.json"
    if not fp.exists():
        raise FileNotFoundError(
            f"缺少年份数据 {year}，请先运行爬虫或放入文件：{fp}"
        )
    raw = json.loads(fp.read_text(encoding="utf-8"))
    # JSON 键统一转 int（避免 "600" vs 600 类型不一致）
    return {int(k): int(v) for k, v in raw.items()}


def load_programs() -> List[Program]:
    """加载专业库（programs.json），返回 Program 对象列表。"""
    fp = DATA_DIR / "programs.json"
    if not fp.exists():
        raise FileNotFoundError(f"缺失专业库文件：{fp}")
    raw = json.loads(fp.read_text(encoding="utf-8"))
    return [Program(**r) for r in raw]


def load_institutions() -> list[dict]:
    """加载院校库（institutions.json），返回原始 dict 列表。"""
    fp = DATA_DIR / "institutions.json"
    if not fp.exists():
        raise FileNotFoundError(f"缺失院校库文件：{fp}")
    return json.loads(fp.read_text(encoding="utf-8"))


def load_admission_history() -> list[dict]:
    """加载历史录取数据（admission_history.json）。

    格式：[{"program_id": "...", "year": 2025, "min_rank": ..., "min_score": ...}, ...]
    """
    fp = DATA_DIR / "admission_history.json"
    if not fp.exists():
        return []
    return json.loads(fp.read_text(encoding="utf-8"))
