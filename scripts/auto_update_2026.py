"""自动抓取 2026 年浙江高考数据并合并到 programs.json。

前提：先跑 check_2026_updates.py 确认数据已发布
执行：python scripts/auto_update_2026.py
"""
from __future__ import annotations

import re
import sys
import json
import pathlib
import requests
import pdfplumber
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import unquote

ROOT = pathlib.Path("D:/Users/LLM Wiki/Workspace/zjgk-volunteer")
sys.path.insert(0, str(ROOT))

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
BASE = "https://www.zjzs.net"
CRAWLED = ROOT / "data/_crawled"


def get_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Referer": BASE + "/"})
    return s


def download_article_attachments(session, article_url: str, label: str) -> list[pathlib.Path]:
    """从文章页下载所有附件（PDF 或 XLS）。"""
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
        out = CRAWLED / f"{label}.{ext}"
        out.write_bytes(r2.content)
        paths.append(out)
    # 也尝试直接 URL（2023 模式：/picture/0/plug-in/ueditor/...）
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/picture/0/plug-in/ueditor/" not in href:
            continue
        full_url = href if href.startswith("http") else BASE + href
        r2 = session.get(full_url, timeout=30)
        if r2.status_code != 200 or not r2.content:
            continue
        magic = r2.content[:4]
        if magic == b"%PDF":
            ext = "pdf"
        elif magic == b"\xd0\xcf\x11\xe0":
            ext = "xls"
        else:
            continue
        out = CRAWLED / f"{label}.{ext}"
        if not out.exists():
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
    df = pd.read_excel(xls_path, engine="xlrd", header=0)
    df.columns = ["code", "institution", "prog_code", "program", "quota", "min_score", "min_rank"]
    return df


NAME_MAP = {
    "华北电力大学(北京)": "华北电力大学",
    "华北电力大学(保定)": "华北电力大学",
    "河北工业大学": "河北工业大学(天津)",
    "中国人民解放军国防科技大学": "国防科技大学",
}


def merge_score_rank(year: int, table: dict) -> pathlib.Path:
    """保存一分一段表。"""
    out = ROOT / "data" / f"score_rank_{year}.json"
    out.write_text(json.dumps(table, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def merge_admission(year: int, df: pd.DataFrame) -> int:
    """合并投档数据到 programs.json，返回更新条数。"""
    df["institution"] = df["institution"].replace(NAME_MAP)
    records = df.to_dict(orient="records")
    for r in records:
        r["min_score"] = int(r["min_score"])
        r["min_rank"] = int(r["min_rank"])
        r["quota"] = int(r["quota"])

    insts = json.loads((ROOT / "data/institutions.json").read_text(encoding="utf-8"))
    inst_names = {i["name"] for i in insts}

    progs = json.loads((ROOT / "data/programs.json").read_text(encoding="utf-8"))
    prog_index = {(p["institution"], p["name"]): p for p in progs}

    updated = 0
    for r in records:
        inst = r["institution"]
        if inst not in inst_names:
            continue
        key = (inst, r["program"])
        if key in prog_index:
            p = prog_index[key]
            p.setdefault("history", [])
            if not any(h["year"] == year for h in p["history"]):
                p["history"].append({
                    "year": year,
                    "min_rank": r["min_rank"],
                    "min_score": r["min_score"],
                })
                updated += 1

    # 排序 + 写回
    for p in progs:
        p["history"] = sorted(p.get("history", []), key=lambda h: h["year"], reverse=True)
    (ROOT / "data/programs.json").write_text(
        json.dumps(progs, ensure_ascii=False, indent=2), encoding="utf-8"
    )

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
    (ROOT / "data/admission_history.json").write_text(
        json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return updated


def main():
    print("=" * 60)
    print(f"  2026 浙江高考数据自动抓取")
    print(f"  执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 1. 检查
    import subprocess
    result = subprocess.run(
        ["python", str(ROOT / "scripts/check_2026_updates.py")],
        capture_output=True, text=True, cwd=str(ROOT)
    )
    print(result.stdout)

    # 2. 读状态
    status_path = ROOT / "data/_crawled/2026_check_status.json"
    if not status_path.exists():
        print("❌ 检查脚本未生成状态文件")
        return 1
    status = json.loads(status_path.read_text(encoding="utf-8"))
    found = status["found"]

    if not (found["score_rank_2026"] or found["admission_2026"]):
        print("⏳ 2026 数据尚未发布，退出。")
        return 1

    session = get_session()
    updated_count = 0

    # 3. 处理一段分数段表
    if found["score_rank_2026"]:
        info = found["score_rank_2026"]
        print(f"\n[1/2] 一段分数段表: {info['title']}")
        paths = download_article_attachments(session, info["href"], "score_rank_2026")
        for p in paths:
            print(f"  ✓ {p.name} ({p.stat().st_size:,} bytes)")
            table = parse_score_rank_pdf(p)
            print(f"  解析: {len(table)} 个分数点")
            if table:
                out = merge_score_rank(2026, table)
                print(f"  ✓ 已保存: {out}")
                # 校验
                for s in [600, 550, 500]:
                    if s in table:
                        print(f"    {s} 分 → {table[s]:,}")

    # 4. 处理一段投档
    if found["admission_2026"]:
        info = found["admission_2026"]
        print(f"\n[2/2] 一段投档: {info['title']}")
        paths = download_article_attachments(session, info["href"], "admission_2026")
        for p in paths:
            print(f"  ✓ {p.name} ({p.stat().st_size:,} bytes)")
            df = parse_admission_xls(p)
            print(f"  解析: {len(df)} 行")
            n = merge_admission(2026, df)
            print(f"  ✓ 合并: {n} 个 program 新增 2026 历史")
            updated_count += n

    # 5. 总结
    print("\n" + "=" * 60)
    if updated_count > 0 or found["score_rank_2026"]:
        print(f"  🎉 2026 数据更新完成！")
        print(f"  - 新增 2026 历史: {updated_count} 条")
        print("\n  下一步：")
        print("    1. git add . && git commit -m 'feat: 抓取 2026 真实数据'")
        print("    2. git push")
        print("    3. Streamlit Cloud 自动重新部署")
    else:
        print("  ℹ 没有新数据可更新")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
