"""测试真实的 zjzs.net 爬取流程。

发现：
- 栏目入口：https://www.zjzs.net/col/col155/index.html (招考资讯)
- 文章页：/art/2025/7/24/art_155_11468.html
- PDF 下载：/module/download/downfile.jsp?filename=xxx.pdf（302 重定向到 /attach/0/xxx.pdf）
- 必须：UA + Referer + Cookie（JSESSIONID）
- 真实 PDF 是表格形式：「总分 | 人数 | 累计人数」
"""
import sys
sys.path.insert(0, "D:/Users/LLM Wiki/Workspace/zjgk-volunteer")

import re
import pathlib
import requests
import pdfplumber
from bs4 import BeautifulSoup
from urllib.parse import unquote


BASE = "https://www.zjzs.net"
COOKIE_FILE = pathlib.Path("data/_crawled/cookies.txt")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def get_session():
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Referer": BASE + "/"})
    return s


def find_pdf_links(session, article_url: str) -> list[tuple[str, str]]:
    """从文章页找 PDF 下载链接。

    Returns: [(filename, showname), ...]
    """
    r = session.get(article_url)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "downfile.jsp" not in href:
            continue
        # 提取 filename
        m = re.search(r"filename=([^&]+)", href)
        filename = unquote(m.group(1)) if m else ""
        showname = a.get_text(strip=True) or filename
        links.append((filename, showname, href))
    return links


def download_pdf(session, downfile_url: str, out_path: pathlib.Path) -> bool:
    """通过 downfile.jsp 下载 PDF（带 302 重定向跟随）。"""
    r = session.get(downfile_url, allow_redirects=True)
    if r.status_code != 200:
        print(f"  HTTP {r.status_code}")
        return False
    if not r.content or "PDF" not in r.content[:20].decode("latin-1", errors="ignore"):
        print(f"  非 PDF 内容（前 50 字节）：{r.content[:50]!r}")
        return False
    out_path.write_bytes(r.content)
    return True


def parse_score_rank_pdf(pdf_path: pathlib.Path) -> dict:
    """解析一分一段表 PDF。

    PDF 多列布局，每页 3 个独立「分数段表」。
    列格式：总分 | 人数 | 累计人数
    累计从高分到低分。
    """
    table_dict = {}
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                if not table or len(table) < 2:
                    continue
                # 跳过表头
                for row in table[1:]:
                    if len(row) < 3:
                        continue
                    try:
                        score = int(row[0].strip())
                        count = int(row[1].strip())
                        cumulative = int(row[2].strip())
                        table_dict[score] = cumulative
                    except (ValueError, AttributeError):
                        continue
    return table_dict


def crawl_segment_table(year: int, segment: int) -> dict:
    """抓取指定年份/段位的分数段表。

    Args:
        year: 高考年份
        segment: 段位（1=一段，2=二段）

    Returns: {分数: 累计人数} 或 None
    """
    print(f"\n=== 抓取 {year} 年第 {segment} 段分数段表 ===")
    session = get_session()

    # 步骤 1：访问招考资讯栏目
    cat_url = f"{BASE}/col/col155/index.html"
    print(f"访问栏目: {cat_url}")
    r = session.get(cat_url)
    r.raise_for_status()

    # 步骤 2：找包含「{year}年...{segment}段...分数段」标题的文章
    soup = BeautifulSoup(r.text, "html.parser")
    target_url = None
    if segment == 1:
        # 一段分数段表：标题含「一段线」或「特控线」
        patterns = [re.compile(rf"{year}.*一段线.*分数段"), re.compile(rf"{year}.*特控线.*分数段")]
    elif segment == 2:
        # 二段分数段表：标题含「二段线」
        patterns = [re.compile(rf"{year}.*二段线.*分数段")]

    for a in soup.find_all("a", href=True):
        title = a.get("title") or a.get_text(strip=True)
        if any(p.search(title) for p in patterns):
            target_url = BASE + a["href"]
            print(f"找到文章: {title}")
            print(f"  URL: {target_url}")
            break

    if not target_url:
        print(f"未找到匹配文章（patterns: {[p.pattern for p in patterns]}）")
        return None

    # 步骤 3：找文章页中的 PDF 链接
    links = find_pdf_links(session, target_url)
    if not links:
        print("文章页未找到 PDF 链接")
        return None
    print(f"找到 {len(links)} 个 PDF 链接：")
    for fn, sn, _ in links:
        print(f"  - {sn}")

    # 步骤 4：下载第一个 PDF（通常是分数段表本身）
    filename, showname, downfile_url = links[0]
    out = pathlib.Path(f"data/_crawled/score_rank_{year}_segment{segment}.pdf")
    if not download_pdf(session, BASE + downfile_url, out):
        return None
    print(f"已下载：{out} ({out.stat().st_size:,} bytes)")

    # 步骤 5：解析 PDF
    table = parse_score_rank_pdf(out)
    print(f"解析完成：{len(table)} 行")
    if table:
        max_score = max(table.keys())
        min_score = min(table.keys())
        print(f"  范围：{max_score} ~ {min_score} 分")
        for s in [600, 550, 500, 490, 400]:
            if s in table:
                print(f"  {s} 分 → 累计 {table[s]:,}")
    return table


if __name__ == "__main__":
    # 测试：抓取 2025 二段
    table = crawl_segment_table(year=2025, segment=2)
    if table:
        # 保存为 JSON
        out = pathlib.Path(f"data/score_rank_2025.json")
        import json
        out.write_text(json.dumps(table, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n✓ 已保存 {len(table)} 行 → {out}")
