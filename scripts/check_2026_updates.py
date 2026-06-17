"""检查 2026 数据是否已在 zjzs.net 发布。

定时任务：每天 9:00（出分前）
检测项：
1. 2026 一段分数段表（预计 6/25-26）
2. 2026 一段投档分数线（预计 7/中下旬）
3. 2026 二段分数段表（预计 7/底）

返回 dict 描述每项的发布状态。
"""
from __future__ import annotations

import re
import sys
import json
import pathlib
import requests
from datetime import datetime
from typing import Dict
from urllib.parse import unquote

sys.path.insert(0, "D:/Users/LLM Wiki/Workspace/zjgk-volunteer")

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
BASE = "https://www.zjzs.net"


def get_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Referer": BASE + "/"})
    return s


def search_articles(session, year: int, page: int = 1) -> list[dict]:
    """从 col155 翻页找 {year} 年相关文章。"""
    start = (page - 1) * 12 + 1
    end = page * 12
    data = {
        "col": "1", "webid": "1", "path": "/", "columnid": "155",
        "sourceContentType": "1", "unitid": "501", "webname": "test", "permissiontype": "0",
    }
    url = f"{BASE}/module/web/jpage/dataproxy.jsp?startrecord={start}&endrecord={end}&perpage=12"
    r = session.post(url, data=data, headers={"X-Requested-With": "XMLHttpRequest"}, timeout=15)
    if r.status_code != 200 or "<record>" not in r.text:
        return []
    records = re.findall(r"<record><!\[CDATA\[(.*?)\]\]></record>", r.text, re.DOTALL)
    result = []
    for rec in records:
        title_m = re.search(r'title="([^"]*)"', rec)
        href_m = re.search(r'href="([^"]*)"', rec)
        if title_m and href_m:
            result.append({
                "title": title_m.group(1),
                "href": href_m.group(1),
            })
    return result


def find_2026_data(session, max_pages: int = 10) -> Dict:
    """扫描 col155 找 2026 年一段相关数据。"""
    found = {
        "score_rank_2026": None,    # 一段分数段表
        "admission_2026": None,      # 一段投档分数线
        "score_rank_2026_seg2": None,  # 二段分数段表
    }

    for page in range(1, max_pages + 1):
        articles = search_articles(session, 2026, page)
        if not articles:
            print(f"  Page {page}: 空（已到末尾）")
            break
        for art in articles:
            title = art["title"]
            href = art["href"]
            # 严格按 URL 中的年份过滤（避免 2025 标题误匹配）
            if f"/art/2026/" not in href:
                continue
            # 一段分数段表
            if found["score_rank_2026"] is None and "一段线" in title and "分数段" in title and "成绩" in title:
                found["score_rank_2026"] = {"title": title, "href": href, "page": page}
                print(f"  ✓ Page {page}: 一段分数段表 - {title[:50]}")
            # 一段投档分数线
            if found["admission_2026"] is None and "第一段" in title and "投档分数线" in title and "普通类" in title:
                found["admission_2026"] = {"title": title, "href": href, "page": page}
                print(f"  ✓ Page {page}: 一段投档 - {title[:50]}")
            # 二段分数段表
            if found["score_rank_2026_seg2"] is None and "二段线" in title and "分数段" in title and "成绩" in title:
                found["score_rank_2026_seg2"] = {"title": title, "href": href, "page": page}
                print(f"  ✓ Page {page}: 二段分数段表 - {title[:50]}")
        # 早停
        if all(found[k] for k in found):
            break

    return found


def main():
    session = get_session()
    print("=" * 60)
    print(f"  2026 浙江高考数据发布检查")
    print(f"  检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    found = find_2026_data(session)

    # 状态判断
    print("\n" + "=" * 60)
    print("  当前状态")
    print("=" * 60)

    if found["score_rank_2026"]:
        print(f"✅ 一段分数段表已发布: {found['score_rank_2026']['title']}")
    else:
        print("⏳ 一段分数段表: 未发布（预计 6/25-26）")

    if found["admission_2026"]:
        print(f"✅ 一段投档分数线已发布: {found['admission_2026']['title']}")
    else:
        print("⏳ 一段投档分数线: 未发布（预计 7/中下旬）")

    if found["score_rank_2026_seg2"]:
        print(f"✅ 二段分数段表已发布: {found['score_rank_2026_seg2']['title']}")
    else:
        print("⏳ 二段分数段表: 未发布（预计 7/底）")

    # 保存结果（保存到 data/ 根目录，以便 git 跟踪 + Streamlit Cloud 可见）
    out = pathlib.Path("data/2026_check_status.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "check_time": datetime.now().isoformat(),
        "found": found,
        "ready_to_crawl": bool(found["score_rank_2026"] or found["admission_2026"]),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✓ 状态已保存: {out}")

    # 如果有数据，提示可以抓取
    if found["admission_2026"] or found["score_rank_2026"]:
        print("\n🚀 检测到 2026 数据已发布！可运行 auto_update_2026.py 自动抓取。")
        return 0
    else:
        print("\n💤 2026 数据尚未发布。保持当前数据，下次再检查。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
