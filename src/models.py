"""数据模型定义。

核心领域对象：
- Candidate：考生（分数、位次、选考科目、偏好）
- Program：专业（院校、城市、学费、选科要求、招生计划、历史录取）
- Recommendation：志愿推荐结果（专业 + 层次 + 概率 + 位次差）
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Candidate:
    """考生信息。

    Attributes:
        score: 高考总分（满分 750）
        rank: 全省位次（1 表示第一名）；None 表示待反查
        selected_subjects: 选考 3 门科目，如 ["物理", "化学", "生物"]
        preferences: 偏好字典（地域、专业关键词等）
    """

    score: int
    rank: Optional[int] = None
    selected_subjects: List[str] = field(default_factory=list)
    preferences: dict = field(default_factory=dict)


@dataclass
class Program:
    """专业（招生单元）。

    一个 Program 等于「1 个专业 + 1 所院校 + 1 个志愿单位」，对应浙江新高考
    「专业（类）+ 学校」平行志愿模式。

    Attributes:
        program_id: 唯一标识（如 "ZJU-CS-2026"）
        name: 专业名称，如 "计算机科学与技术"
        institution: 院校名称，如 "浙江大学"
        city: 院校所在地
        duration_years: 学制（年）
        tuition: 年学费（元）
        required_subjects: 选考科目要求，如 ["物理", "化学"]
        plan_quota_2026: 2026 年招生计划数（爬取后可填充；缺失时为 0）
        history: 历史录取数据，按年倒序：
            [{"year": 2025, "min_rank": 12500, "min_score": 632}, ...]
    """

    program_id: str
    name: str
    institution: str
    city: str
    duration_years: int
    tuition: int
    required_subjects: List[str]
    plan_quota_2026: int
    history: List[dict] = field(default_factory=list)


@dataclass
class Recommendation:
    """志愿推荐结果（一个志愿单位）。

    Attributes:
        program: 推荐的专业
        tier: 层次，"冲" / "稳" / "保"
        probability: 录取概率估计（0.0 - 1.0）
        delta_rank: 位次差（考生位次 - 该专业 2025 年最低投档位次）
            正值表示考生位次靠后（更难录取），负值表示考生位次靠前
    """

    program: Program
    tier: str
    probability: float
    delta_rank: int
