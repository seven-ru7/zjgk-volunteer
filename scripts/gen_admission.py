"""生成历史录取数据（admission_history.json）。

策略：
- 为每个 program 分配 2025 年最低投档位次（min_rank_2025）
- 根据院校档次 + 专业热度，位次从 500（清北 CS）到 200000（偏远 211）
- 2023-2024 年位次在 ±10% 范围内浮动（模拟年度差异）
- 同时根据 (min_rank) 反查分数段得到 min_score
"""
import json
import pathlib
import random

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"

random.seed(42)  # 保证可复现


# 院校基础位次档位（rank 越小越难考）
INSTITUTION_BASE_RANK = {
    # Tier 1：清北复交浙（min_rank 1000-10000）
    "清华大学": (800, 1500),
    "北京大学": (800, 1500),
    "复旦大学": (2000, 4000),
    "上海交通大学": (2500, 5000),
    "浙江大学": (3000, 6000),
    "中国科学技术大学": (2500, 4500),
    "南京大学": (4000, 7000),
    "中国人民大学": (3000, 6000),
    # Tier 2：其他 985 顶尖（5000-15000）
    "北京航空航天大学": (5000, 12000),
    "北京理工大学": (7000, 14000),
    "同济大学": (6000, 12000),
    "华东师范大学": (7000, 14000),
    "武汉大学": (7000, 15000),
    "华中科技大学": (8000, 16000),
    "西安交通大学": (8000, 16000),
    "哈尔滨工业大学": (9000, 18000),
    "南开大学": (7000, 14000),
    "天津大学": (8000, 16000),
    "东南大学": (8000, 16000),
    "中山大学": (8000, 16000),
    "厦门大学": (9000, 18000),
    "山东大学": (10000, 20000),
    "四川大学": (10000, 22000),
    "吉林大学": (12000, 25000),
    "中南大学": (12000, 25000),
    "湖南大学": (12000, 24000),
    "大连理工大学": (11000, 22000),
    "重庆大学": (13000, 26000),
    "电子科技大学": (9000, 18000),
    "华南理工大学": (12000, 24000),
    "西北工业大学": (10000, 20000),
    "兰州大学": (18000, 35000),
    "中央民族大学": (15000, 30000),
    "国防科技大学": (5000, 12000),
    "北京师范大学": (6000, 13000),
    "中国农业大学": (15000, 35000),
    "西北农林科技大学": (25000, 50000),
    # Tier 3：强势 211（15000-40000）
    "北京交通大学": (15000, 30000),
    "北京科技大学": (15000, 30000),
    "北京邮电大学": (8000, 18000),
    "北京林业大学": (20000, 40000),
    "中国传媒大学": (12000, 28000),
    "中央财经大学": (8000, 18000),
    "对外经济贸易大学": (7000, 15000),
    "北京外国语大学": (8000, 18000),
    "中国政法大学": (8000, 18000),
    "华北电力大学": (18000, 35000),
    "北京工业大学": (18000, 35000),
    "华东理工大学": (16000, 32000),
    "东华大学": (22000, 45000),
    "上海财经大学": (6000, 13000),
    "上海大学": (18000, 38000),
    "上海外国语大学": (10000, 22000),
    "南京航空航天大学": (13000, 28000),
    "南京理工大学": (15000, 32000),
    "河海大学": (18000, 38000),
    "江南大学": (22000, 45000),
    "南京农业大学": (22000, 45000),
    "南京师范大学": (18000, 38000),
    "中国药科大学": (18000, 38000),
    "中国矿业大学": (25000, 50000),
    "苏州大学": (15000, 35000),
    "武汉理工大学": (18000, 38000),
    "华中农业大学": (22000, 45000),
    "中南财经政法大学": (12000, 25000),
    "中国地质大学": (22000, 45000),
    "西安电子科技大学": (10000, 22000),
    "陕西师范大学": (20000, 40000),
    "长安大学": (22000, 45000),
    "西北大学": (22000, 45000),
    "西南交通大学": (18000, 38000),
    "西南财经大学": (12000, 26000),
    "四川农业大学": (35000, 70000),
    "暨南大学": (15000, 32000),
    "华南师范大学": (18000, 38000),
    "哈尔滨工程大学": (18000, 38000),
    "东北林业大学": (35000, 70000),
    "东北农业大学": (40000, 80000),
    "湖南师范大学": (22000, 45000),
    "东北师范大学": (22000, 45000),
    "中国海洋大学": (18000, 38000),
    "中国石油大学(华东)": (22000, 45000),
    "中国石油大学(北京)": (22000, 45000),
    "合肥工业大学": (22000, 45000),
    "福州大学": (22000, 45000),
    "郑州大学": (25000, 50000),
    "东北大学": (18000, 38000),
    "辽宁大学": (28000, 55000),
    "大连海事大学": (22000, 45000),
    "河北工业大学": (30000, 60000),
    "南昌大学": (28000, 55000),
    "广西大学": (35000, 70000),
    "云南大学": (30000, 60000),
    "贵州大学": (40000, 80000),
    "海南大学": (45000, 90000),
    "新疆大学": (50000, 100000),
    "石河子大学": (60000, 120000),
    "宁夏大学": (50000, 100000),
    "青海大学": (50000, 100000),
    "西藏大学": (70000, 150000),
    "内蒙古大学": (45000, 90000),
    "山西大学": (35000, 70000),
    "太原理工大学": (30000, 60000),
    "安徽大学": (28000, 55000),
    "河南大学": (35000, 70000),
    "中国矿业大学(北京)": (25000, 50000),
    "中国地质大学(北京)": (22000, 45000),
    "延边大学": (50000, 100000),
    "南京邮电大学": (18000, 38000),
    "海军军医大学": (15000, 30000),
    "中国人民公安大学": (15000, 30000),
    "北京中医药大学": (18000, 38000),
    "江苏大学": (30000, 60000),
}


# 专业热度修正系数（热门专业位次更靠前）
PROG_HOTNESS = {
    "计算机科学与技术": 0.5,  # 顶尖 50% 难度
    "软件工程": 0.55,
    "人工智能": 0.4,
    "电子信息工程": 0.6,
    "通信工程": 0.65,
    "临床医学": 0.6,
    "口腔医学": 0.5,
    "金融学": 0.5,
    "经济学": 0.6,
    "会计学": 0.65,
    "法学": 0.65,
    "建筑学": 0.7,
    "汉语言文学": 0.8,
    "英语": 0.85,
    "数学与应用数学": 0.7,
    "物理学": 0.85,
    "化学": 0.85,
    "农学": 1.3,  # 农学相对好考
    "林学": 1.4,
    "园林": 1.2,
    "动物科学": 1.3,
    "护理学": 1.2,
    "中医学": 1.1,
}


def get_base_range(institution: str) -> tuple:
    """获取院校位次区间。"""
    if institution in INSTITUTION_BASE_RANK:
        return INSTITUTION_BASE_RANK[institution]
    # 关键字兜底
    for key, rng in INSTITUTION_BASE_RANK.items():
        if key in institution or institution in key:
            return rng
    # 默认偏远 211
    return (50000, 100000)


def rank_to_score(target_rank: int, score_rank_table: dict) -> int:
    """位次 → 对应分数（位次越小分数越高，反向插值）。"""
    # 归一化 key 为 int
    score_rank_table = {int(k): int(v) for k, v in score_rank_table.items()}
    # 按位次升序排序
    pairs = sorted(score_rank_table.items(), key=lambda x: x[1])  # [(score, rank), ...]
    # 转为 [(rank, score), ...] 并排序
    ranks_scores = sorted([(rank, score) for score, rank in pairs])
    if not ranks_scores:
        return 0
    # 找 target_rank 所在的区间
    for i, (r, s) in enumerate(ranks_scores):
        if r >= target_rank:
            if i == 0:
                return int(s)
            prev_r, prev_s = ranks_scores[i - 1]
            if r == prev_r:
                return int(s)
            ratio = (target_rank - prev_r) / (r - prev_r)
            return int(prev_s + ratio * (s - prev_s))
    return int(ranks_scores[-1][1])


def main():
    programs = json.loads((DATA_DIR / "programs.json").read_text(encoding="utf-8"))
    sr_2025 = json.loads((DATA_DIR / "score_rank_2025.json").read_text(encoding="utf-8"))
    sr_2024 = json.loads((DATA_DIR / "score_rank_2024.json").read_text(encoding="utf-8"))
    sr_2023 = json.loads((DATA_DIR / "score_rank_2023.json").read_text(encoding="utf-8"))

    history_records = []
    updated_programs = []

    for prog in programs:
        inst = prog["institution"]
        name = prog["name"]
        base_min, base_max = get_base_range(inst)
        # 应用热度系数
        hotness = PROG_HOTNESS.get(name, 1.0)
        rank_2025 = int(random.uniform(base_min, base_max) * hotness)
        # 三年位次：±10% 浮动
        history = []
        for year, sr_table, jitter in [
            (2023, sr_2023, 0.10),
            (2024, sr_2024, 0.05),
            (2025, sr_2025, 0.0),
        ]:
            yr_rank = int(rank_2025 * (1 + random.uniform(-jitter, jitter)))
            yr_score = rank_to_score(yr_rank, sr_table)
            history.append({
                "year": year,
                "min_rank": yr_rank,
                "min_score": yr_score,
            })
        history.sort(key=lambda x: x["year"], reverse=True)

        # 更新 program.history
        new_prog = {**prog, "history": history, "plan_quota_2026": random.randint(20, 150)}
        updated_programs.append(new_prog)

        # 同时输出 admission_history.json（聚合格式）
        for h in history:
            history_records.append({
                "program_id": prog["program_id"],
                "institution": inst,
                "program": name,
                "year": h["year"],
                "min_rank": h["min_rank"],
                "min_score": h["min_score"],
            })

    # 写回 programs.json
    (DATA_DIR / "programs.json").write_text(
        json.dumps(updated_programs, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    # 写 admission_history.json
    (DATA_DIR / "admission_history.json").write_text(
        json.dumps(history_records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"✓ {len(updated_programs)} 个 program 写入 history")
    print(f"✓ {len(history_records)} 条历史录取记录 → admission_history.json")
    # 抽样展示
    sample = updated_programs[0]
    print(f"\n示例：{sample['institution']} - {sample['name']}")
    for h in sample["history"]:
        print(f"  {h['year']}: 位次 {h['min_rank']:,} / 分数 {h['min_score']}")


if __name__ == "__main__":
    main()
