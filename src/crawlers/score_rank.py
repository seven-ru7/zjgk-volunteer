"""一分一段表爬取。

目标：从浙江省教育考试院「招考资讯」栏目抓取浙江一分一段表
URL 示例：https://www.zjzs.net/art/2025/06_25/...
实际 URL 每年可能变化；若失败则返回 fallback 提示，由用户手动下载。
"""
from __future__ import annotations

import json
import pathlib
from typing import Optional

from bs4 import BeautifulSoup

from .base import BaseCrawler


class ScoreRankCrawler(BaseCrawler):
    """一分一段表爬取器。"""

    # 候选 URL 列表（按优先级；实际有效 URL 需要发布后确认）
    CANDIDATE_URLS = [
        # 2025 年（参考）
        "https://www.zjzs.net/art/2025/06_25/art_0_100000_2025xxxx.html",
        # 通用入口
        "https://www.zjzs.net/zjgj/ksfw/",
    ]

    def __init__(self, base_url: str = "https://www.zjzs.net"):
        super().__init__(base_url=base_url)
        # 数据目录
        self.data_dir = pathlib.Path(__file__).resolve().parent.parent.parent / "data"

    def fetch(self, year: int) -> dict:
        """抓取指定年份的一分一段表。

        Returns:
            dict with keys:
                - table: {分数: 累计人数} 或 None（失败时）
                - source_url: 成功或失败对应的 URL
                - manual_tip: 失败时的提示
        """
        # 尝试每个候选 URL
        for url_template in self.CANDIDATE_URLS:
            url = url_template.format(year=year)
            try:
                response = self.get(url)
                table = self.parse_html(response.text)
                if table:
                    return {
                        "table": table,
                        "source_url": url,
                        "year": year,
                        "rows": len(table),
                    }
            except Exception as e:
                self.log.warning(f"抓取失败 {url}: {e}")
                continue

        # 全部失败 → 返回 fallback
        return {
            "table": None,
            "source_url": "https://www.zjzs.net/zjgj/ksfw/",
            "manual_tip": (
                f"自动抓取 {year} 年一分一段表失败。\n"
                "请访问浙江省教育考试院手动下载：\n"
                "https://www.zjzs.net/zjgj/ksfw/\n"
                "下载后将数据放入 data/score_rank_<year>.json"
            ),
            "year": year,
        }

    @staticmethod
    def parse_html(html: str) -> dict:
        """从 HTML 中解析一分一段表。

        期望格式（实际格式可能变化）：
        <table>
          <tr><th>分数</th><th>累计人数</th></tr>
          <tr><td>750</td><td>200</td></tr>
          ...
        </table>
        """
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table")
        if not table:
            return {}

        result = {}
        rows = table.find_all("tr")
        for tr in rows[1:]:  # 跳过表头
            cells = [td.get_text(strip=True) for td in tr.find_all("td")]
            if len(cells) >= 2:
                score_str, rank_str = cells[0], cells[1]
                # 宽松解析：去掉可能的 "," 或 "分"
                score_str = score_str.replace("分", "").replace(",", "").strip()
                rank_str = rank_str.replace(",", "").strip()
                if score_str.isdigit() and rank_str.isdigit():
                    score, rank = int(score_str), int(rank_str)
                    if 0 <= score <= 750 and 0 < rank < 10_000_000:
                        result[score] = rank
        return result

    def save(self, year: int, table: dict) -> pathlib.Path:
        """保存到 data/score_rank_<year>.json。"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        out = self.data_dir / f"score_rank_{year}.json"
        out.write_text(
            json.dumps(table, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return out


def crawl_score_rank(year: int) -> dict:
    """便捷函数：抓取 + 自动保存。"""
    crawler = ScoreRankCrawler()
    try:
        result = crawler.fetch(year)
        if result.get("table"):
            saved = crawler.save(year, result["table"])
            result["saved_path"] = str(saved)
        return result
    finally:
        crawler.close()
