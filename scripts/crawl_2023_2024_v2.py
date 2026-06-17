"""补全 2023 / 2024 数据。

URL（已验证）:
- 2024 一段分数段表: /art/2024/6/26/art_155_9758.html
- 2024 二段分数段表: /art/2024/7/24/art_155_9911.html
- 2023 一段分数段表: /art/2023/6/26/art_155_7134.html
- 2023 二段分数段表: /art/2023/7/22/art_155_2197.html
- 2023 一段投档: /art/2023/7/19/art_155_2089.html
"""
import sys
sys.path.insert(0, "D:/Users/LLM Wiki/Workspace/zjgk-volunteer")

import re
import json
import pathlib
import requests
import pdfplumber
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import unquote


BASE = "https://www.zjzs.net"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
CRAWLED = pathlib.Path("data/_crawled")


def get_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Referer": BASE + "/"})
    return s


def download_article_attachments(session, article_url: str, label: str) -> list[pathlib.Path]:
    """下载文章页的所有附件。"""
    r = session.get(article_url, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    paths = []
    for a in soup.find_all("a", href=True):
        if "downfile.jsp" not in a["href"]:
            continue
        full_url = a["href"] if a["href"].startswith("http") else BASE + a["href"]
        r2 = session.get(full_url, allow_redirects=True, timeout=30)
        if r2.status_code != 200 or not r2.content:
            continue
        magic = r2.content[:4]
        if magic == b"%PDF":
            ext = "pdf"
        elif magic == b"\xd0\xcf\x11\xe0":
            ext = "xls"
        else:
            continue
        # 用 label 作文件名
        out = CRAWLED / f"{label}.{ext}"
        out.write_bytes(r2.content)
        paths.append(out)
    return paths


def parse_score_rank_pdf(pdf_path: pathlib.Path) -> dict:
    """解析一分一段表 PDF。"""
    table = {}
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            for t in page.extract_tables():
                if not t or len(t) < 2:
                    continue
                for row in t[1:]:
                    if len(row) < 3:
                        continue
                    try:
                        score = int(row[0].strip().rstrip("↑"))
                        cum = int(row[2].strip())
                        table[score] = max(table.get(score, 0), cum)
                    except (ValueError, AttributeError):
                        continue
    return table


def parse_admission_xls(xls_path: pathlib.Path) -> pd.DataFrame:
    """解析投档分数线 XLS。"""
    df = pd.read_excel(xls_path, engine="xlrd", header=0)
    df.columns = ["code", "institution", "prog_code", "program", "quota", "min_score", "min_rank"]
    return df


def main():
    session = get_session()
    insts = json.loads(pathlib.Path("data/institutions.json").read_text(encoding="utf-8"))
    inst_names = {i["name"] for i in insts}
    NAME_MAP = {
        "华北电力大学(北京)": "华北电力大学",
        "华北电力大学(保定)": "华北电力大学",
        "河北工业大学": "河北工业大学(天津)",
        "中国人民解放军国防科技大学": "国防科技大学",
    }

    # 6 个目标
    targets = [
        ("score_rank_2024", f"{BASE}/art/2024/6/26/art_155_9758.html"),
        ("score_rank_2023", f"{BASE}/art/2023/6/26/art_155_7134.html"),
        ("admission_2023", f"{BASE}/art/2023/7/19/art_155_2089.html"),
    ]

    print("=" * 60)
    print("下载 2023 / 2024 数据")
    print("=" * 60)

    new_data = {"score_rank": {}, "admission": {}}

    for label, url in targets:
        print(f"\n[{label}] {url}")
        paths = download_article_attachments(session, url, label)
        if not paths:
            print("  ✗ 未找到附件")
            continue
        for p in paths:
            print(f"  ✓ {p.name} ({p.stat().st_size:,} bytes)")
            try:
                if p.suffix == ".pdf":
                    table = parse_score_rank_pdf(p)
                    year = int(label.split("_")[-1])
                    new_data["score_rank"][year] = table
                    print(f"    解析: {len(table)} 个分数点")
                    # 保存 JSON
                    out = pathlib.Path(f"data/score_rank_{year}.json")
                    out.write_text(json.dumps(table, ensure_ascii=False, indent=2), encoding="utf-8")
                    # 关键校验
                    for s in [600, 550, 500]:
                        if s in table:
                            print(f"    {s} 分 → {table[s]:,}")
                elif p.suffix == ".xls":
                    df = parse_admission_xls(p)
                    year = int(label.split("_")[-1])
                    # 修正名称
                    df["institution"] = df["institution"].replace(NAME_MAP)
                    records = df.to_dict(orient="records")
                    # 转 int
                    for r in records:
                        r["min_score"] = int(r["min_score"])
                        r["min_rank"] = int(r["min_rank"])
                        r["quota"] = int(r["quota"])
                    new_data["admission"][year] = records
                    # 保存
                    out = pathlib.Path(f"data/_crawled/admission_{year}.json")
                    out.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
                    print(f"    解析: {len(records)} 条")
                    print(f"    匹配 985+211: {sum(1 for r in records if r['institution'] in inst_names)} 条")
            except Exception as e:
                print(f"  ✗ 解析失败: {e}")

    # 合并 admission 到 programs.json
    print("\n" + "=" * 60)
    print("合并历史数据到 programs.json")
    print("=" * 60)

    progs = json.loads(pathlib.Path("data/programs.json").read_text(encoding="utf-8"))
    prog_index = {(p["institution"], p["name"]): p for p in progs}
    print(f"现有 programs: {len(progs)} 个")

    for year, records in new_data["admission"].items():
        added = 0
        updated = 0
        for r in records:
            inst = r["institution"]
            if inst not in inst_names:
                continue
            key = (inst, r["program"])
            if key in prog_index:
                p = prog_index[key]
                p.setdefault("history", [])
                # 避免重复
                if not any(h["year"] == year for h in p["history"]):
                    p["history"].append({
                        "year": year,
                        "min_rank": r["min_rank"],
                        "min_score": r["min_score"],
                    })
                    updated += 1
        print(f"  {year}: 更新 {updated} 个 program")

    # 排序 history
    for p in progs:
        p["history"] = sorted(p.get("history", []), key=lambda h: h["year"], reverse=True)

    pathlib.Path("data/programs.json").write_text(
        json.dumps(progs, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n✓ 已保存 programs.json ({len(progs)} 个)")

    # 统计
    hist_counts = {}
    for p in progs:
        n = len(p.get("history", []))
        hist_counts[n] = hist_counts.get(n, 0) + 1
    print("\n历史数据覆盖:")
    for n in sorted(hist_counts.keys(), reverse=True):
        print(f"  {n} 年历史: {hist_counts[n]} 个 program")

    # 更新 admission_history.json
    history = []
    for p in progs:
        for h in p.get("history", []):
            history.append({
                "program_id": p["program_id"],
                "institution": p["institution"],
                "program": p["name"],
                "year": h["year"],
                "min_rank": h["min_rank"],
                "min_score": h["min_score"],
            })
    pathlib.Path("data/admission_history.json").write_text(
        json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n✓ admission_history.json: {len(history)} 条")
    year_counts = {}
    for h in history:
        year_counts[h["year"]] = year_counts.get(h["year"], 0) + 1
    for y in sorted(year_counts.keys()):
        print(f"  {y}: {year_counts[y]} 条")

    print("\n✅ 全部完成！")


if __name__ == "__main__":
    main()
