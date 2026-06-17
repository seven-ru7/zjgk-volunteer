"""分数↔位次互转。

基于一分一段表（{分数: 累计人数}）实现两个核心函数：
- score_to_rank(score) → 位次
- rank_to_score(rank) → 分数
"""
from __future__ import annotations

import bisect
from typing import Dict


def _normalize(score_rank_table: Dict) -> Dict[int, int]:
    """归一化为 {int(分数): int(累计人数)}。"""
    return {int(k): int(v) for k, v in score_rank_table.items()}


def score_to_rank(score: int, score_rank_table: dict) -> int:
    """给定分数，返回对应累计位次。

    语义：「这个分数及以上」的累计人数（即该考生在全省的位次）。
    例：600 分 → 52529 表示 600 分及以上共有 52529 人。

    算法：在分数表中找最近的两个分数点线性插值。

    Args:
        score: 高考分数（0-750）
        score_rank_table: {分数: 累计人数}，键值可为 int 或 str

    Returns:
        位次（1 表示第 1 名）
    """
    table = _normalize(score_rank_table)
    if not table:
        return 0
    if score <= 0:
        return 0
    # 超过最高分 → 返回最大累计人数（最末位次）
    max_score = max(table.keys())
    if score >= max_score:
        return table[max_score]
    # 分数低于表内最低分 → 返回最大累计人数（位次靠后）
    min_score = min(table.keys())
    if score < min_score:
        return max(table.values())

    # bisect 找最近的两个分数点
    sorted_scores = sorted(table.keys())  # 升序
    i = bisect.bisect_left(sorted_scores, score)
    # sorted_scores[i-1] < score <= sorted_scores[i]
    if sorted_scores[i] == score:
        return table[score]
    lo_s, lo_r = sorted_scores[i - 1], table[sorted_scores[i - 1]]
    hi_s, hi_r = sorted_scores[i], table[sorted_scores[i]]
    # 分数越高，位次越小（累计人数越少）
    ratio = (score - lo_s) / (hi_s - lo_s)
    rank = lo_r + ratio * (hi_r - lo_r)
    return int(round(rank))


def rank_to_score(rank: int, score_rank_table: dict) -> int:
    """给定位次，返回对应分数。

    算法：在分数表中找最近的两个位次点反向插值。

    Args:
        rank: 位次（1 表示第 1 名）
        score_rank_table: {分数: 累计人数}

    Returns:
        对应分数（0-750）
    """
    table = _normalize(score_rank_table)
    if not table:
        return 0
    if rank <= 0:
        return 0
    # 位次超过最大累计人数 → 分数低于表内最低分
    max_rank = max(table.values())
    if rank > max_rank:
        return min(table.keys())
    # 位次小于最小累计人数 → 分数等于表内最高分
    min_rank = min(table.values())
    if rank <= min_rank:
        return max(table.keys())

    # 按位次升序排序（rank 越小，分数越高）
    pairs = sorted(table.items(), key=lambda x: x[1])  # [(score, rank), ...]
    # 转 [(rank, score), ...]
    ranks_scores = sorted([(r, s) for s, r in pairs])
    # 线性找区间
    for i, (r, s) in enumerate(ranks_scores):
        if r >= rank:
            if i == 0 or ranks_scores[i - 1][0] == r:
                return int(s)
            prev_r, prev_s = ranks_scores[i - 1]
            ratio = (rank - prev_r) / (r - prev_r)
            return int(round(prev_s + ratio * (s - prev_s)))
    return int(ranks_scores[-1][1])
