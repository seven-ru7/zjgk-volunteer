"""录取概率估算。

核心思路：基于历史 2025 年最低投档位次与考生位次的差值（delta_rank），
按分段赋予录取概率：
    delta < -8000  → 保（95%）
    -8000 ≤ delta < 2000  → 稳（75%）
    2000 ≤ delta < 10000  → 冲（45%）
    delta ≥ 10000  → 冲（10%）

delta_rank = 考生位次 - 该专业 2025 年最低投档位次
正数表示考生位次靠后（更难录取），负数表示考生位次靠前。

注：概率是经验估算，仅供参考；真实录取受招生计划、报考热度等多因素影响。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class ProbabilityResult:
    """概率估算结果。"""
    probability: float   # 0.0 - 1.0
    delta_rank: int      # 位次差（正=位次靠后）
    tier: str            # "冲" / "稳" / "保"


def estimate(
    candidate_rank: Optional[int],
    program,
    year: int = 2025,
) -> ProbabilityResult:
    """估算考生录取该专业的概率。

    Args:
        candidate_rank: 考生全省位次
        program: Program 对象（含 history 字段）
        year: 参考年份（默认 2025）

    Returns:
        ProbabilityResult
    """
    if candidate_rank is None or candidate_rank <= 0:
        # 未知位次 → 中性估计
        return ProbabilityResult(probability=0.5, delta_rank=0, tier="稳")

    # 找参考年份的历史位次
    history = getattr(program, "history", []) or []
    target = None
    for h in history:
        if h.get("year") == year:
            target = h
            break
    if target is None and history:
        # 找不到指定年份 → 用最近一年
        target = max(history, key=lambda x: x.get("year", 0))

    if target is None:
        # 无历史数据
        return ProbabilityResult(probability=0.5, delta_rank=0, tier="稳")

    history_rank = target["min_rank"]
    delta = candidate_rank - history_rank

    # 分档
    if delta < -8000:
        prob, tier = 0.95, "保"
    elif delta < 2000:
        prob, tier = 0.75, "稳"
    elif delta < 10000:
        prob, tier = 0.45, "冲"
    else:
        prob, tier = 0.10, "冲"

    return ProbabilityResult(probability=prob, delta_rank=delta, tier=tier)


def estimate_legacy(
    candidate_rank: int,
    program,
    year: int = 2025,
) -> Tuple[float, int, str]:
    """返回 (probability, delta_rank, tier) 元组（兼容性接口）。"""
    r = estimate(candidate_rank, program, year)
    return r.probability, r.delta_rank, r.tier
