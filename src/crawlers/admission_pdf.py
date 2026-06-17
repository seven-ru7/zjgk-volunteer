"""投档 PDF 解析。

目标：解析 zjzs.net 上的「浙江省普通高校招生投档及专业录取情况」PDF
格式（实际）：
- PDF 包含数千行表格，每行格式：院校代码 院校名称 专业组代码 专业 计划数 投档人数 最低分 最低位次
- 需识别中文表格并按列提取
"""
from __future__ import annotations

import json
import pathlib
import re
from typing import Optional

import pdfplumber

from .base import BaseCrawler


class AdmissionPdfCrawler(BaseCrawler):
    """投档 PDF 爬取与解析。"""

    # 已知的 PDF URL（按年份；缺失年份走 fallback）
    PDF_URLS = {
        2024: "https://www.zjzs.net/attach/0/a9189771c9514010accbac9b2699af95.pdf",
    }

    def __init__(self, base_url: str = "https://www.zjzs.net"):
        super().__init__(base_url=base_url)
        self.data_dir = pathlib.Path(__file__).resolve().parent.parent.parent / "data"

    def fetch(self, year: int) -> dict:
        """抓取并解析指定年份的投档 PDF。

        Returns:
            dict with keys:
                - rows: [{"code": ..., "institution": ..., "program": ...,
                          "min_score": ..., "min_rank": ...}, ...]
                - source_url: 成功时的 URL
                - manual_tip: 失败时的提示
        """
        url = self.PDF_URLS.get(year)
        if not url:
            return {
                "rows": None,
                "manual_tip": (
                    f"{year} 年投档 PDF 暂未配置 URL。\n"
                    f"已配置年份：{list(self.PDF_URLS.keys())}\n"
                    "可手动从 https://www.zjzs.net/zjgj/ksfw/ 下载后放入 data/ 目录，"
                    "使用 parse_local() 解析。"
                ),
                "year": year,
            }

        try:
            response = self.get(url)
            pdf_path = self.data_dir / f"_tmp_admission_{year}.pdf"
            pdf_path.write_bytes(response.content)
            try:
                rows = self.parse_pdf(pdf_path)
                return {
                    "rows": rows,
                    "source_url": url,
                    "year": year,
                    "rows_count": len(rows),
                }
            finally:
                if pdf_path.exists():
                    pdf_path.unlink()
        except Exception as e:
            self.log.error(f"PDF 抓取失败: {e}")
            return {
                "rows": None,
                "manual_tip": (
                    f"抓取 {year} 年 PDF 失败：{e}\n"
                    "可手动从 https://www.zjzs.net/zjgj/ksfw/ 下载后放入 data/ 目录。"
                ),
                "year": year,
            }

    def parse_local(self, pdf_path: str | pathlib.Path) -> dict:
        """解析本地 PDF 文件。"""
        rows = self.parse_pdf(pathlib.Path(pdf_path))
        return {
            "rows": rows,
            "source_url": str(pdf_path),
            "rows_count": len(rows),
        }

    @staticmethod
    def parse_pdf(pdf_path: pathlib.Path) -> list[dict]:
        """解析 PDF 文件，返回录取记录列表。

        行格式示例（实际格式以 PDF 为准）：
        院校代码 院校名称 专业组 专业名称 计划数 投档数 最低分 最低位次

        使用 pdfplumber 提取每行文本，再用正则提取数字字段。
        """
        rows = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                for line in text.splitlines():
                    row = AdmissionPdfCrawler._parse_line(line)
                    if row:
                        rows.append(row)
        return rows

    @staticmethod
    def _parse_line(line: str) -> Optional[dict]:
        """解析单行文本。

        策略：找所有 4-6 位连续数字作为「院校代码 / 最低分 / 最低位次」候选。
        中文上下文模糊时优先信任行首的 5 位数字作为院校代码。
        """
        line = line.strip()
        if not line:
            return None

        # 提取所有数字（含中文标点内的）
        nums = re.findall(r"\d+", line)
        if len(nums) < 3:
            return None

        # 假设行首前 5 位是院校代码（教育部 5 位标准代码）
        code = nums[0] if len(nums[0]) == 5 else None
        if not code:
            return None

        # 剩余数字：尝试找分数（<= 750）和位次（>= 100）
        remaining = nums[1:]
        min_score = None
        min_rank = None
        for n in remaining:
            n_int = int(n)
            if 300 <= n_int <= 750 and min_score is None:
                min_score = n_int
            elif 1 <= n_int <= 5_000_000 and min_rank is None and n_int > 100:
                min_rank = n_int
            if min_score is not None and min_rank is not None:
                break

        if not (min_score and min_rank):
            return None

        # 提取院校名称（在 code 后面、中文标点前的连续中文）
        # 简化处理：取 code 之后的第一段中文
        after_code = line[len(code):].strip()
        m = re.match(r"([\u4e00-\u9fa5（）()A-Za-z·\s]+?)[\s\d]", after_code)
        institution = m.group(1).strip() if m else "未知"

        return {
            "code": code,
            "institution": institution,
            "min_score": min_score,
            "min_rank": min_rank,
        }

    def merge_into_history(self, rows: list[dict], year: int) -> pathlib.Path:
        """将解析出的录取数据合并进 admission_history.json。"""
        out = self.data_dir / "admission_history.json"
        if out.exists():
            history = json.loads(out.read_text(encoding="utf-8"))
        else:
            history = []
        # 为新行添加 year
        for r in rows:
            r["year"] = year
            history.append(r)
        out.write_text(
            json.dumps(history, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return out
