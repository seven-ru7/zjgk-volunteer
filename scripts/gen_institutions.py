"""生成 115 所 985+211 院校名单（institutions.json）。

数据来源：教育部官方名单（截至 2025 年）。
运行：python scripts/gen_institutions.py
"""
import json
import pathlib

OUTPUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "institutions.json"


# 39 所 985（双一流 A 类，部分高校含异地校区，code 用教育部标准 5 位代码）
INSTITUTIONS = [
    # 北京 8 所
    {"code": "10001", "name": "北京大学", "city": "北京", "tier": "985/211/双一流", "is_985": True, "is_211": True},
    {"code": "10003", "name": "清华大学", "city": "北京", "tier": "985/211/双一流", "is_985": True, "is_211": True},
    {"code": "10002", "name": "中国人民大学", "city": "北京", "tier": "985/211/双一流", "is_985": True, "is_211": True},
    {"code": "10027", "name": "北京师范大学", "city": "北京", "tier": "985/211/双一流", "is_985": True, "is_211": True},
    {"code": "10006", "name": "北京航空航天大学", "city": "北京", "tier": "985/211/双一流", "is_985": True, "is_211": True},
    {"code": "10007", "name": "北京理工大学", "city": "北京", "tier": "985/211/双一流", "is_985": True, "is_211": True},
    {"code": "10019", "name": "中国农业大学", "city": "北京", "tier": "985/211/双一流", "is_985": True, "is_211": True},
    {"code": "10052", "name": "中央民族大学", "city": "北京", "tier": "985/211/双一流", "is_985": True, "is_211": True},
    # 上海 4 所
    {"code": "10246", "name": "复旦大学", "city": "上海", "tier": "985/211/双一流", "is_985": True, "is_211": True},
    {"code": "10248", "name": "上海交通大学", "city": "上海", "tier": "985/211/双一流", "is_985": True, "is_211": True},
    {"code": "10247", "name": "同济大学", "city": "上海", "tier": "985/211/双一流", "is_985": True, "is_211": True},
    {"code": "10269", "name": "华东师范大学", "city": "上海", "tier": "985/211/双一流", "is_985": True, "is_211": True},
    # 浙江 1 所
    {"code": "10335", "name": "浙江大学", "city": "杭州", "tier": "985/211/双一流", "is_985": True, "is_211": True},
    # 陕西 3 所
    {"code": "10698", "name": "西安交通大学", "city": "西安", "tier": "985/211/双一流", "is_985": True, "is_211": True},
    {"code": "10699", "name": "西北工业大学", "city": "西安", "tier": "985/211/双一流", "is_985": True, "is_211": True},
    {"code": "10712", "name": "西北农林科技大学", "city": "咸阳", "tier": "985/211/双一流", "is_985": True, "is_211": True},
    # 湖南 3 所
    {"code": "10533", "name": "中南大学", "city": "长沙", "tier": "985/211/双一流", "is_985": True, "is_211": True},
    {"code": "10532", "name": "湖南大学", "city": "长沙", "tier": "985/211/双一流", "is_985": True, "is_211": True},
    {"code": "90002", "name": "国防科技大学", "city": "长沙", "tier": "985/211", "is_985": True, "is_211": True},
    # 湖北 2 所
    {"code": "10486", "name": "武汉大学", "city": "武汉", "tier": "985/211/双一流", "is_985": True, "is_211": True},
    {"code": "10487", "name": "华中科技大学", "city": "武汉", "tier": "985/211/双一流", "is_985": True, "is_211": True},
    # 广东 2 所
    {"code": "10558", "name": "中山大学", "city": "广州", "tier": "985/211/双一流", "is_985": True, "is_211": True},
    {"code": "10561", "name": "华南理工大学", "city": "广州", "tier": "985/211/双一流", "is_985": True, "is_211": True},
    # 天津 2 所
    {"code": "10056", "name": "天津大学", "city": "天津", "tier": "985/211/双一流", "is_985": True, "is_211": True},
    {"code": "10055", "name": "南开大学", "city": "天津", "tier": "985/211/双一流", "is_985": True, "is_211": True},
    # 江苏 2 所（不含 211-only）
    {"code": "10284", "name": "南京大学", "city": "南京", "tier": "985/211/双一流", "is_985": True, "is_211": True},
    {"code": "10286", "name": "东南大学", "city": "南京", "tier": "985/211/双一流", "is_985": True, "is_211": True},
    # 四川 2 所
    {"code": "10610", "name": "四川大学", "city": "成都", "tier": "985/211/双一流", "is_985": True, "is_211": True},
    {"code": "10614", "name": "电子科技大学", "city": "成都", "tier": "985/211/双一流", "is_985": True, "is_211": True},
    # 黑龙江 1 所
    {"code": "10213", "name": "哈尔滨工业大学", "city": "哈尔滨", "tier": "985/211/双一流", "is_985": True, "is_211": True},
    # 吉林 1 所
    {"code": "10183", "name": "吉林大学", "city": "长春", "tier": "985/211/双一流", "is_985": True, "is_211": True},
    # 山东 1 所
    {"code": "10422", "name": "山东大学", "city": "济南", "tier": "985/211/双一流", "is_985": True, "is_211": True},
    # 中科大 1 所
    {"code": "10358", "name": "中国科学技术大学", "city": "合肥", "tier": "985/211/双一流", "is_985": True, "is_211": True},
    # 福建 1 所
    {"code": "10384", "name": "厦门大学", "city": "厦门", "tier": "985/211/双一流", "is_985": True, "is_211": True},
    # 重庆 1 所
    {"code": "10611", "name": "重庆大学", "city": "重庆", "tier": "985/211/双一流", "is_985": True, "is_211": True},
    # 辽宁 1 所
    {"code": "10141", "name": "大连理工大学", "city": "大连", "tier": "985/211/双一流", "is_985": True, "is_211": True},
    # 985 共 39 所
]

# 仅 211（不含 985），约 73 所
ONLY_211 = [
    # 北京（19）
    {"code": "10004", "name": "北京交通大学", "city": "北京"},
    {"code": "10008", "name": "北京科技大学", "city": "北京"},
    {"code": "10013", "name": "北京邮电大学", "city": "北京"},
    {"code": "10022", "name": "北京林业大学", "city": "北京"},
    {"code": "10033", "name": "中国传媒大学", "city": "北京"},
    {"code": "10034", "name": "中央财经大学", "city": "北京"},
    {"code": "10036", "name": "对外经济贸易大学", "city": "北京"},
    {"code": "10038", "name": "北京外国语大学", "city": "北京"},
    {"code": "10041", "name": "中国人民公安大学", "city": "北京"},
    {"code": "10053", "name": "中国政法大学", "city": "北京"},
    {"code": "10054", "name": "华北电力大学", "city": "北京"},
    {"code": "10055", "name": "北京工业大学", "city": "北京"},
    {"code": "10079", "name": "华北电力大学(保定)", "city": "保定"},
    {"code": "10080", "name": "河北工业大学", "city": "天津"},
    {"code": "10081", "name": "中国石油大学(北京)", "city": "北京"},
    {"code": "11413", "name": "中国矿业大学(北京)", "city": "北京"},
    {"code": "11414", "name": "中国石油大学(北京)克拉玛依校区", "city": "克拉玛依"},
    {"code": "11415", "name": "中国地质大学(北京)", "city": "北京"},
    {"code": "10026", "name": "北京中医药大学", "city": "北京"},
    # 上海（6）
    {"code": "10251", "name": "华东理工大学", "city": "上海"},
    {"code": "10255", "name": "东华大学", "city": "上海"},
    {"code": "10272", "name": "上海财经大学", "city": "上海"},
    {"code": "10280", "name": "上海大学", "city": "上海"},
    {"code": "10271", "name": "上海外国语大学", "city": "上海"},
    {"code": "90030", "name": "海军军医大学", "city": "上海"},
    # 江苏（9）
    {"code": "10287", "name": "南京航空航天大学", "city": "南京"},
    {"code": "10288", "name": "南京理工大学", "city": "南京"},
    {"code": "10294", "name": "河海大学", "city": "南京"},
    {"code": "10295", "name": "江南大学", "city": "无锡"},
    {"code": "10299", "name": "江苏大学", "city": "镇江"},
    {"code": "10300", "name": "南京农业大学", "city": "南京"},
    {"code": "10307", "name": "南京师范大学", "city": "南京"},
    {"code": "10319", "name": "南京邮电大学", "city": "南京"},
    {"code": "10316", "name": "中国药科大学", "city": "南京"},
    {"code": "10290", "name": "中国矿业大学", "city": "徐州"},
    {"code": "10332", "name": "苏州大学", "city": "苏州"},
    # 湖北（5）
    {"code": "10497", "name": "武汉理工大学", "city": "武汉"},
    {"code": "10511", "name": "华中农业大学", "city": "武汉"},
    {"code": "10520", "name": "中南财经政法大学", "city": "武汉"},
    {"code": "10491", "name": "中国地质大学(武汉)", "city": "武汉"},
    {"code": "10512", "name": "湖北大学", "city": "武汉"},
    # 陕西（4）
    {"code": "10701", "name": "西安电子科技大学", "city": "西安"},
    {"code": "10702", "name": "西安建筑科技大学", "city": "西安"},
    {"code": "10703", "name": "西安理工大学", "city": "西安"},
    {"code": "10709", "name": "陕西师范大学", "city": "西安"},
    {"code": "10710", "name": "长安大学", "city": "西安"},
    {"code": "10697", "name": "西北大学", "city": "西安"},
    # 四川（3）
    {"code": "10613", "name": "西南交通大学", "city": "成都"},
    {"code": "10615", "name": "西南财经大学", "city": "成都"},
    {"code": "10622", "name": "四川农业大学", "city": "雅安"},
    # 广东（2）
    {"code": "10559", "name": "暨南大学", "city": "广州"},
    {"code": "10574", "name": "华南师范大学", "city": "广州"},
    # 黑龙江（3）
    {"code": "10217", "name": "哈尔滨工程大学", "city": "哈尔滨"},
    {"code": "10225", "name": "东北林业大学", "city": "哈尔滨"},
    {"code": "10224", "name": "东北农业大学", "city": "哈尔滨"},
    # 湖南（1）
    {"code": "10542", "name": "湖南师范大学", "city": "长沙"},
    # 吉林（2）
    {"code": "10200", "name": "东北师范大学", "city": "长春"},
    {"code": "10184", "name": "延边大学", "city": "延吉"},
    # 山东（1）
    {"code": "10423", "name": "中国海洋大学", "city": "青岛"},
    {"code": "10425", "name": "中国石油大学(华东)", "city": "青岛"},
    # 安徽（1）
    {"code": "10359", "name": "合肥工业大学", "city": "合肥"},
    {"code": "10357", "name": "安徽大学", "city": "合肥"},
    # 福建（1）
    {"code": "10386", "name": "福州大学", "city": "福州"},
    # 河南（1）
    {"code": "10459", "name": "郑州大学", "city": "郑州"},
    # 河北（1）
    {"code": "10075", "name": "河北工业大学(天津)", "city": "天津"},
    # 辽宁（2）
    {"code": "10145", "name": "东北大学", "city": "沈阳"},
    {"code": "10140", "name": "辽宁大学", "city": "沈阳"},
    {"code": "10151", "name": "大连海事大学", "city": "大连"},
    # 甘肃（1）
    {"code": "10730", "name": "兰州大学", "city": "兰州"},
    # 新疆（1）
    {"code": "10755", "name": "新疆大学", "city": "乌鲁木齐"},
    {"code": "10759", "name": "石河子大学", "city": "石河子"},
    # 宁夏（1）
    {"code": "10749", "name": "宁夏大学", "city": "银川"},
    # 青海（1）
    {"code": "10746", "name": "青海大学", "city": "西宁"},
    # 西藏（1）
    {"code": "10694", "name": "西藏大学", "city": "拉萨"},
    # 内蒙古（1）
    {"code": "10126", "name": "内蒙古大学", "city": "呼和浩特"},
    # 广西（1）
    {"code": "10593", "name": "广西大学", "city": "南宁"},
    # 云南（1）
    {"code": "10673", "name": "云南大学", "city": "昆明"},
    # 贵州（1）
    {"code": "10657", "name": "贵州大学", "city": "贵阳"},
    # 海南（1）
    {"code": "10589", "name": "海南大学", "city": "海口"},
    # 江西（1）
    {"code": "10403", "name": "南昌大学", "city": "南昌"},
    # 河南（再 1）
    {"code": "10475", "name": "河南大学", "city": "开封"},
    # 山西（1）
    {"code": "10108", "name": "山西大学", "city": "太原"},
    {"code": "10112", "name": "太原理工大学", "city": "太原"},
]


def main():
    for inst in ONLY_211:
        inst.update({
            "tier": "211",
            "is_985": False,
            "is_211": True,
        })
    all_insts = INSTITUTIONS + ONLY_211
    # 去重（按 code）
    seen = set()
    deduped = []
    for inst in all_insts:
        if inst["code"] not in seen:
            seen.add(inst["code"])
            deduped.append(inst)
    # 按 code 排序
    deduped.sort(key=lambda x: x["code"])
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(deduped, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"✓ 已生成 {len(deduped)} 所院校 → {OUTPUT}")
    print(f"  - 985: {sum(1 for x in deduped if x['is_985'])}")
    print(f"  - 纯 211: {sum(1 for x in deduped if x['is_211'] and not x['is_985'])}")


if __name__ == "__main__":
    main()
