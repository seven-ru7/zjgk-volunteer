"""抓取 2024 / 2023 年真实高考数据。

从 col155 翻页找：
- 2024 / 2023 的一段分数段表 PDF
- 2024 / 2023 的一段投档分数线 XLS

合并到 programs.json 作为 history 字段（多年数据增强推荐质量）。
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
from collections import OrderedDict
from urllib.parse import unquote


BASE = "https://www.zjzs.net"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
CRAWLED = pathlib.Path("data/_crawled")
CRAWLED.mkdir(parents=True, exist_ok=True)


def get_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Referer": BASE + "/"})
    return s


def fetch_col155_page(session, page: int) -> list[dict]:
    """翻页获取 col155 文章列表。

    Returns: [{"title": ..., "href": ..., "date": ...}, ...]
    """
    start = (page - 1) * 12 + 1
    end = page * 12
    data = {
        "col": "1", "webid": "1", "path": "/", "columnid": "155",
        "sourceContentType": "1", "unitid": "501", "webname": "test", "permissiontype": "0",
    }
    url = f"{BASE}/module/web/jpage/dataproxy.jsp?startrecord={start}&endrecord={end}&perpage=12"
    r = session.post(url, data=data, headers={"X-Requested-With": "XMLHttpRequest"})
    if r.status_code != 200 or "<record>" not in r.text:
        return []
    records = re.findall(r"<record><!\[CDATA\[(.*?)\]\]></record>", r.text, re.DOTALL)
    result = []
    for rec in records:
        title_m = re.search(r'title="([^"]*)"', rec)
        href_m = re.search(r'href="([^"]*)"', rec)
        if not (title_m and href_m):
            continue
        title = title_m.group(1)
        href = href_m.group(1)
        if not href.startswith("http"):
            href = BASE + href
        result.append({"title": title, "href": href})
    return result


def find_pdf_links(session, article_url: str) -> list[tuple[str, str, str]]:
    """从文章页提取下载链接。

    Returns: [(showname, filename, full_url), ...]
    """
    r = session.get(article_url)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "downfile.jsp" not in href:
            continue
        full_url = href if href.startswith("http") else BASE + href
        showname = a.get_text(strip=True) or "unknown"
        m = re.search(r"filename=([^&]+)", href)
        filename = unquote(m.group(1)) if m else ""
        links.append((showname, filename, full_url))
    return links


def download_file(session, url: str, out_path: pathlib.Path) -> bool:
    """下载文件（PDF 或 XLS），跟随 302。"""
    r = session.get(url, allow_redirects=True)
    if r.status_code != 200 or not r.content:
        return False
    # 检查 magic bytes：PDF=%PDF, XLS=D0CF11E0
    magic = r.content[:4]
    if not (magic.startswith(b"%PDF") or magic == b"\xd0\xcf\x11\xe0"):
        print(f"  未知文件格式: {magic!r}")
        return False
    out_path.write_bytes(r.content)
    return True


def parse_score_rank_pdf(pdf_path: pathlib.Path) -> dict:
    """解析一分一段表 PDF（多列布局）。"""
    table = {}
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            for t in page.extract_tables():
                if not t or len(t) < 2:
                    continue
                for row in t[1:]:  # skip header
                    if len(row) < 3:
                        continue
                    try:
                        score = int(row[0].strip().rstrip("↑"))
                        cum = int(row[2].strip())
                        table[score] = cum
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
    print("=" * 60)
    print("翻页扫描 col155 找 2023 / 2024 年关键数据")
    print("=" * 60)

    targets = {
        2023: {"score_rank": None, "admission": None},
        2024: {"score_rank": None, "admission": None},
    }

    for page in range(1, 65):  # ~748 篇文章 / 12 per page ≈ 63 页
        articles = fetch_col155_page(session, page)
        if not articles:
            print(f"Page {page}: 空")
            continue
        for art in articles:
            title = art["title"]
            href = art["href"]
            # 检查目标年份
            for year in [2023, 2024]:
                if f"{year}年" not in title:
                    continue
                if "一段线" in title and "分数段" in title and "成绩" in title:
                    if targets[year]["score_rank"] is None:
                        targets[year]["score_rank"] = (title, href)
                        print(f"  ✓ {year} 分数段表（Page {page}）: {title[:40]}")
                elif "第一段" in title and "投档分数线" in title and "普通类" in title:
                    if targets[year]["admission"] is None:
                        targets[year]["admission"] = (title, href)
                        print(f"  ✓ {year} 投档分数线（Page {page}）: {title[:40]}")
        # 早停
        if all(targets[y]["score_rank"] and targets[y]["admission"] for y in targets):
            print(f"  ✓ 全部找到，停止于 Page {page}")
            break

    print("\n" + "=" * 60)
    print("下载并解析")
    print("=" * 60)

    results = {}
    for year, urls in targets.items():
        results[year] = {"score_rank": None, "admission": None}

        # 一分一段表
        if urls["score_rank"]:
            title, url = urls["score_rank"]
            print(f"\n[{year}] 一分一段表: {title}")
            links = find_pdf_links(session, url)
            if not links:
                print("  ✗ 未找到 PDF 链接")
                continue
            showname, filename, full_url = links[0]
            print(f"  PDF: {showname}")
            out = CRAWLED / f"score_rank_{year}.pdf"
            if not download_file(session, full_url, out):
                print("  ✗ 下载失败")
                continue
            print(f"  ✓ 下载: {out.stat().st_size:,} bytes")
            table = parse_score_rank_pdf(out)
            print(f"  ✓ 解析: {len(table)} 个分数点")
            # 保存为 JSON
            out_json = pathlib.Path(f"data/score_rank_{year}.json")
            out_json.write_text(json.dumps(table, ensure_ascii=False, indent=2), encoding="utf-8")
            results[year]["score_rank"] = table

        # 投档分数线
        if urls["admission"]:
            title, url = urls["admission"]
            print(f"\n[{year}] 投档分数线: {title}")
            links = find_pdf_links(session, url)
            if not links:
                print("  ✗ 未找到 XLS 链接")
                continue
            showname, filename, full_url = links[0]
            print(f"  XLS: {showname}")
            out = CRAWLED / f"admission_{year}.xls"
            if not download_file(session, full_url, out):
                print("  ✗ 下载失败")
                continue
            print(f"  ✓ 下载: {out.stat().st_size:,} bytes")
            try:
                df = parse_admission_xls(out)
                print(f"  ✓ 解析: {len(df)} 行 x {len(df.columns)} 列")
                # 保存为 JSON（精简版）
                records = df.to_dict(orient="records")
                out_json = pathlib.Path(f"data/_crawled/admission_{year}.json")
                out_json.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
                results[year]["admission"] = records
            except Exception as e:
                print(f"  ✗ 解析失败: {e}")

    # 合并到 programs.json
    print("\n" + "=" * 60)
    print("合并到 programs.json")
    print("=" * 60)

    if results[2024].get("admission") or results[2023].get("admission"):
        # 加载现有 programs.json
        progs = json.loads(pathlib.Path("data/programs.json").read_text(encoding="utf-8"))
        prog_index = {(p["institution"], p["name"]): p for p in progs}
        print(f"现有 programs: {len(progs)} 个")

        for year in [2023, 2024]:
            records = results[year].get("admission")
            if not records:
                continue

            # 加载 985+211 院校名单
            insts = json.loads(pathlib.Path("data/institutions.json").read_text(encoding="utf-8"))
            inst_names = {i["name"] for i in insts}
            NAME_MAP = {
                "华北电力大学(北京)": "华北电力大学",
                "华北电力大学(保定)": "华北电力大学",
                "河北工业大学": "河北工业大学(天津)",
                "中国人民解放军国防科技大学": "国防科技大学",
            }

            added = 0
            updated = 0
            for r in records:
                inst = r["institution"]
                if inst in NAME_MAP:
                    inst = NAME_MAP[inst]
                if inst not in inst_names:
                    continue
                key = (inst, r["program"])
                if key in prog_index:
                    # 已存在：追加 history
                    p = prog_index[key]
                    p.setdefault("history", [])
                    p["history"].append({
                        "year": year,
                        "min_rank": int(r["min_rank"]),
                        "min_score": int(r["min_score"]),
                    })
                    updated += 1
                else:
                    # 新增（少数 2023/2024 才有，2025 没有的专业）
                    continue
            print(f"  {year}: 更新 {updated} 个 program 的 history")

        # 按年份排序 history
        for p in progs:
            p["history"] = sorted(p.get("history", []), key=lambda h: h["year"], reverse=True)

        # 写回
        pathlib.Path("data/programs.json").write_text(
            json.dumps(progs, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"✓ 已保存 programs.json ({len(progs)} 个)")

        # 统计有几年历史
        hist_counts = {}
        for p in progs:
            n = len(p.get("history", []))
            hist_counts[n] = hist_counts.get(n, 0) + 1
        print(f"\n历史数据覆盖:")
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
        print(f"\n✓ admission_history.json: {len(history)} 条记录")
        # 按年统计
        year_counts = {}
        for h in history:
            year_counts[h["year"]] = year_counts.get(h["year"], 0) + 1
        for y in sorted(year_counts.keys()):
            print(f"  {y}: {year_counts[y]} 条")

    print("\n✅ 全部完成！")


if __name__ == "__main__":
    main()
