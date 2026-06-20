"""冲稳保志愿推荐算法。

输入：考生 + 专业列表 + 偏好（地域 / 关键词）
输出：80 个志愿（按冲稳保比例分配）
"""
from __future__ import annotations

from typing import Iterable, List, Optional, Sequence, Tuple

from .matcher import is_eligible
from .models import Candidate, Program, Recommendation
from .probability import estimate


# 默认冲稳保比例：冲 30% / 稳 50% / 保 20%（依据招办主任建议）
DEFAULT_RATIO: Tuple[float, float, float] = (0.30, 0.50, 0.20)


def _filter_by_preferences(
    programs: Sequence[Program],
    cities: Optional[Iterable[str]] = None,
    keywords: Optional[Iterable[str]] = None,
) -> List[Program]:
    """按地域 / 关键词过滤专业。空过滤项表示不限。"""
    city_set = set(cities) if cities else set()
    kw_list = [k.strip() for k in (keywords or []) if k and k.strip()]

    filtered = []
    for p in programs:
        if city_set and p.city not in city_set:
            continue
        if kw_list and not any(kw in p.name for kw in kw_list):
            continue
        filtered.append(p)
    return filtered


def recommend(
    candidate: Candidate,
    programs: Sequence[Program],
    top_n: int = 80,
    ratio: Tuple[float, float, float] = DEFAULT_RATIO,
    cities: Optional[Iterable[str]] = None,
    keywords: Optional[Iterable[str]] = None,
) -> List[Recommendation]:
    """为考生生成冲稳保志愿推荐。

    Args:
        candidate: 考生（含 score / rank / selected_subjects）
        programs: 可选专业列表（已被选科 + 偏好过滤）
        top_n: 目标志愿数量（默认 80 = 普通类一段平行志愿上限）
        ratio: (冲, 稳, 保) 占比；和应为 1.0
        cities: 偏好城市列表（None 表示不限）
        keywords: 专业关键词列表（任一匹配即保留）

    Returns:
        Recommendation 列表（按冲→稳→保排序，每组内按概率降序）
    """
    # 1. 偏好过滤
    filtered = _filter_by_preferences(programs, cities, keywords)

    # 2. 选科筛选 + 计算概率
    rush, stable, safe = [], [], []
    for prog in filtered:
        if not is_eligible(prog.required_subjects, candidate.selected_subjects):
            continue
        result = estimate(candidate.rank, prog)
        rec = Recommendation(
            program=prog,
            tier=result.tier,
            probability=result.probability,
            delta_rank=result.delta_rank,
        )
        if rec.tier == "冲":
            rush.append(rec)
        elif rec.tier == "稳":
            stable.append(rec)
        else:
            safe.append(rec)

    # 3. 组内排序：
#    - 冲档：概率降序，delta_rank 升序（位次越接近考生越好）
#    - 稳/保档：|delta_rank| 升序（位次最接近考生位次的最匹配）
    rush.sort(key=lambda r: (-r.probability, r.delta_rank))
    stable.sort(key=lambda r: (abs(r.delta_rank), -r.probability))
    safe.sort(key=lambda r: (abs(r.delta_rank), -r.probability))

    # 4. 按 ratio 分配名额
    n_rush = int(top_n * ratio[0])
    n_stable = int(top_n * ratio[1])
    n_safe = top_n - n_rush - n_stable  # 余数归保档，保证总数=top_n

    picked = rush[:n_rush] + stable[:n_stable] + safe[:n_safe]

    # 5. 最终按 冲→稳→保 排序
    tier_order = {"冲": 0, "稳": 1, "保": 2}
    picked.sort(key=lambda r: (tier_order[r.tier], -r.probability))

    return picked


def summary(recs: Sequence[Recommendation]) -> dict:
    """返回推荐结果的统计摘要。"""
    if not recs:
        return {"total": 0, "rush": 0, "stable": 0, "safe": 0, "avg_probability": 0.0}
    rush = sum(1 for r in recs if r.tier == "冲")
    stable = sum(1 for r in recs if r.tier == "稳")
    safe = sum(1 for r in recs if r.tier == "保")
    avg = sum(r.probability for r in recs) / len(recs)
    return {
        "total": len(recs),
        "rush": rush,
        "stable": stable,
        "safe": safe,
        "avg_probability": round(avg, 3),
    }
