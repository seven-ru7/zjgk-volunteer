"""志愿表导出（DataFrame / Excel / CSV）。"""
from __future__ import annotations

import pathlib
from typing import List, Optional, Sequence

import pandas as pd

from .models import Program, Recommendation


COLUMNS = [
    "序号", "层次", "院校", "专业", "城市", "学制", "学费",
    "2026计划数", "2025最低位次", "2025最低分", "2024最低位次", "2023最低位次",
    "趋势", "3年趋势",
    "位次差", "录取概率",
]


def _get_year_rank(program: Program, year: int) -> Optional[int]:
    """从 program.history 中取指定年份的 min_rank。"""
    for h in program.history:
        if h.get("year") == year:
            return h.get("min_rank")
    return None


def _get_year_score(program: Program, year: int) -> Optional[int]:
    for h in program.history:
        if h.get("year") == year:
            return h.get("min_score")
    return None


# Unicode block 字符用于 sparkline（▁▂▃▄▅▆▇█）
_SPARKLINE_CHARS = "▁▂▃▄▅▆▇█"


def make_sparkline(ranks: List[Optional[int]], reverse: bool = True) -> str:
    """用 Unicode block 字符画 3 年位次 mini chart。

    Args:
        ranks: 多年位次 [2023, 2024, 2025]（按时间正序）
        reverse: True 表示「位次越小越难」，所以反转映射
                 （高 block = 难考 = 小位次）

    Returns:
        3 个字符的 sparkline 字符串，缺失值显示为 ░
    """
    valid = [(i, r) for i, r in enumerate(ranks) if r is not None and r > 0]
    if not valid:
        return "░░░"
    if len(valid) == 1:
        return "▅░░"  # 只有 1 个数据点
    # 归一化
    vals = [r for _, r in valid]
    vmin, vmax = min(vals), max(vals)
    if vmax == vmin:
        # 全部相同
        return "".join(_SPARKLINE_CHARS[4] if r is not None else "░" for r in ranks)
    # 映射到 0-7（block 索引）
    blocks = []
    for r in ranks:
        if r is None:
            blocks.append("░")
        else:
            # 归一化到 0-1
            ratio = (r - vmin) / (vmax - vmin)
            if reverse:
                # 小位次 → 高 block
                ratio = 1 - ratio
            idx = int(ratio * (len(_SPARKLINE_CHARS) - 1))
            idx = max(0, min(len(_SPARKLINE_CHARS) - 1, idx))
            blocks.append(_SPARKLINE_CHARS[idx])
    return "".join(blocks)


def compute_trend(ranks: List[Optional[int]]) -> dict:
    """计算 3 年位次变化趋势。

    Args:
        ranks: [2023, 2024, 2025] 位次

    Returns:
        dict: {
            "direction": "↑"/"→"/"↓"/"—",
            "delta": int,  # 2025 - 2023 的差值
            "delta_pct": float,  # 百分比变化
            "stable": bool,  # 是否 ±5% 内
        }
    """
    if not ranks or ranks[0] is None or ranks[-1] is None:
        return {"direction": "—", "delta": 0, "delta_pct": 0.0, "stable": False}

    r_old, r_new = ranks[0], ranks[-1]
    delta = r_new - r_old  # 正值 = 位次变大 = 变容易
    delta_pct = (delta / r_old * 100) if r_old > 0 else 0

    if abs(delta_pct) < 5:
        direction = "→"  # 平稳
        stable = True
    elif delta > 0:
        direction = "↓"  # 位次变大 = 变容易
        stable = False
    else:
        direction = "↑"  # 位次变小 = 变难
        stable = False

    return {
        "direction": direction,
        "delta": delta,
        "delta_pct": round(delta_pct, 1),
        "stable": stable,
    }


def to_dataframe(recs: Sequence[Recommendation]) -> pd.DataFrame:
    """将 Recommendation 列表转为 DataFrame（增强版：含 3 年趋势分析）。"""
    rows = []
    for i, r in enumerate(recs, start=1):
        p = r.program
        h25 = _get_year_rank(p, 2025)
        h24 = _get_year_rank(p, 2024)
        h23 = _get_year_rank(p, 2023)
        h25_score = _get_year_score(p, 2025)

        # 3 年位次趋势
        ranks = [h23, h24, h25]
        trend = compute_trend(ranks)
        sparkline = make_sparkline(ranks, reverse=True)

        # 趋势描述
        if trend["direction"] == "—":
            trend_text = "数据不足"
        elif trend["direction"] == "→":
            trend_text = f"→ 平稳（{trend['delta_pct']:+.1f}%）"
        elif trend["direction"] == "↓":
            trend_text = f"↓ 变易（{trend['delta_pct']:+.1f}%）"
        else:  # ↑
            trend_text = f"↑ 变难（{trend['delta_pct']:+.1f}%）"

        rows.append({
            "序号": i,
            "层次": r.tier,
            "院校": p.institution,
            "专业": p.name,
            "城市": p.city,
            "学制": p.duration_years,
            "学费": p.tuition,
            "2026计划数": p.plan_quota_2026,
            "2025最低位次": h25,
            "2025最低分": h25_score,
            "2024最低位次": h24,
            "2023最低位次": h23,
            "趋势": trend_text,
            "3年趋势": sparkline,
            "位次差": r.delta_rank,
            "录取概率": f"{r.probability * 100:.0f}%",
        })
    return pd.DataFrame(rows, columns=COLUMNS)


def to_excel(recs: Sequence[Recommendation], path: str | pathlib.Path) -> pathlib.Path:
    """导出为 Excel 文件。返回写入路径。"""
    df = to_dataframe(recs)
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(path, index=False, engine="openpyxl")
    return path


def to_csv(recs: Sequence[Recommendation], path: str | pathlib.Path) -> pathlib.Path:
    """导出为 CSV 文件（UTF-8 with BOM，Excel 友好）。"""
    df = to_dataframe(recs)
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    return path
