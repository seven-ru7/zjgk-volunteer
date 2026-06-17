"""投档 PDF 解析测试。"""
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.crawlers.admission_pdf import AdmissionPdfCrawler


class TestParseLine:
    def test_standard_line(self):
        line = "10001 北京大学 01 计算机科学与技术 50 50 720 580"
        row = AdmissionPdfCrawler._parse_line(line)
        assert row is not None
        assert row["code"] == "10001"
        assert "北京大学" in row["institution"]
        assert row["min_score"] == 720
        assert row["min_rank"] == 580

    def test_invalid_no_code(self):
        line = "这是无效行"
        assert AdmissionPdfCrawler._parse_line(line) is None

    def test_invalid_too_few_numbers(self):
        line = "10001 北京大学"  # 缺分数位次
        assert AdmissionPdfCrawler._parse_line(line) is None

    def test_invalid_short_code(self):
        line = "1234 北京大学 720 580"
        assert AdmissionPdfCrawler._parse_line(line) is None

    def test_empty_line(self):
        assert AdmissionPdfCrawler._parse_line("") is None


class TestFetch:
    def test_unknown_year_fallback(self):
        """未配置 URL 的年份 → 返回 fallback。"""
        crawler = AdmissionPdfCrawler()
        result = crawler.fetch(2025)
        assert result["rows"] is None
        assert "2025" in result["manual_tip"]
        assert "2024" in result["manual_tip"]  # 提示已配置年份
        crawler.close()

    def test_known_year_success(self, tmp_path, monkeypatch):
        """已知年份：成功下载并解析。"""
        crawler = AdmissionPdfCrawler()
        # 重定向 data_dir 到 tmp_path
        monkeypatch.setattr(crawler, "data_dir", tmp_path)

        # 模拟一个简单的 PDF
        sample_pdf = tmp_path / "sample.pdf"
        # 真实测试需要用 pdfplumber 生成 PDF；这里 mock parse_pdf
        with patch.object(crawler, "get") as mock_get:
            mock_get.return_value = MagicMock(
                content=b"%PDF-1.4 dummy",
                raise_for_status=MagicMock(),
            )
            with patch.object(AdmissionPdfCrawler, "parse_pdf", return_value=[
                {"code": "10001", "institution": "北京大学",
                 "min_score": 720, "min_rank": 580}
            ]):
                result = crawler.fetch(2024)
        assert result["rows"] is not None
        assert len(result["rows"]) == 1
        assert result["rows"][0]["institution"] == "北京大学"
        assert result["source_url"] == AdmissionPdfCrawler.PDF_URLS[2024]
        crawler.close()

    def test_known_year_failure(self, tmp_path, monkeypatch):
        """已知年份：网络失败。"""
        crawler = AdmissionPdfCrawler()
        monkeypatch.setattr(crawler, "data_dir", tmp_path)
        with patch.object(crawler, "get", side_effect=Exception("网络超时")):
            result = crawler.fetch(2024)
        assert result["rows"] is None
        assert "网络超时" in result["manual_tip"]
        crawler.close()


class TestMergeIntoHistory:
    def test_creates_new(self, tmp_path, monkeypatch):
        crawler = AdmissionPdfCrawler()
        monkeypatch.setattr(crawler, "data_dir", tmp_path)
        rows = [
            {"code": "10001", "institution": "北京大学",
             "min_score": 720, "min_rank": 580}
        ]
        out = crawler.merge_into_history(rows, year=2026)
        assert out.exists()
        loaded = json.loads(out.read_text(encoding="utf-8"))
        assert len(loaded) == 1
        assert loaded[0]["year"] == 2026
        crawler.close()

    def test_appends_to_existing(self, tmp_path, monkeypatch):
        crawler = AdmissionPdfCrawler()
        monkeypatch.setattr(crawler, "data_dir", tmp_path)
        # 预存历史
        existing = tmp_path / "admission_history.json"
        existing.write_text(json.dumps([
            {"code": "99999", "institution": "旧数据", "year": 2024,
             "min_score": 600, "min_rank": 50000}
        ]), encoding="utf-8")
        new_rows = [{"code": "10001", "institution": "北京大学",
                     "min_score": 720, "min_rank": 580}]
        out = crawler.merge_into_history(new_rows, year=2026)
        loaded = json.loads(out.read_text(encoding="utf-8"))
        assert len(loaded) == 2
        assert loaded[0]["code"] == "99999"  # 旧数据保留
        assert loaded[1]["code"] == "10001"  # 新数据
        crawler.close()
