"""一分一段表爬取测试（mock HTTP）。"""
import json
from unittest.mock import MagicMock, patch

import pytest

from src.crawlers.score_rank import ScoreRankCrawler, crawl_score_rank


# 模拟 HTML 片段
SAMPLE_HTML = """
<html><body>
<table>
  <tr><th>分数</th><th>累计人数</th></tr>
  <tr><td>750</td><td>200</td></tr>
  <tr><td>700</td><td>2000</td></tr>
  <tr><td>650</td><td>21,000</td></tr>
  <tr><td>600</td><td>88500</td></tr>
  <tr><td>500</td><td>373500</td></tr>
</table>
</body></html>
"""

HTML_NO_TABLE = "<html><body><p>暂无数据</p></body></html>"

HTML_BAD_CELLS = """
<html><body>
<table>
  <tr><th>分数</th><th>累计人数</th></tr>
  <tr><td>abc</td><td>100</td></tr>
  <tr><td>700</td><td>xyz</td></tr>
  <tr><td>600</td><td>50000</td></tr>
</table>
</body></html>
"""


class TestParseHtml:
    def test_valid_html(self):
        result = ScoreRankCrawler.parse_html(SAMPLE_HTML)
        assert result[750] == 200
        assert result[700] == 2000
        assert result[650] == 21000  # 自动去逗号
        assert result[600] == 88500

    def test_no_table(self):
        assert ScoreRankCrawler.parse_html(HTML_NO_TABLE) == {}

    def test_bad_cells_skipped(self):
        result = ScoreRankCrawler.parse_html(HTML_BAD_CELLS)
        assert 600 in result
        assert 700 not in result
        assert result[600] == 50000


class TestFetch:
    def test_success(self, tmp_path):
        """模拟成功抓取。"""
        crawler = ScoreRankCrawler()
        mock_response = MagicMock(status_code=200, text=SAMPLE_HTML)
        mock_response.raise_for_status = MagicMock()
        with patch.object(crawler, "get", return_value=mock_response):
            result = crawler.fetch(2025)
        assert result["table"] is not None
        assert result["rows"] == 5
        assert result["year"] == 2025
        crawler.close()

    def test_all_fail_fallback(self):
        """所有 URL 失败 → 返回 fallback 提示。"""
        crawler = ScoreRankCrawler()
        with patch.object(crawler, "get", side_effect=Exception("网络错误")):
            result = crawler.fetch(2025)
        assert result["table"] is None
        assert "manual_tip" in result
        assert "浙江省教育考试院" in result["manual_tip"]
        crawler.close()

    def test_empty_response(self):
        """返回空 HTML。"""
        crawler = ScoreRankCrawler()
        mock_response = MagicMock(status_code=200, text=HTML_NO_TABLE)
        mock_response.raise_for_status = MagicMock()
        with patch.object(crawler, "get", return_value=mock_response):
            result = crawler.fetch(2025)
        assert result["table"] is None
        crawler.close()


class TestSave:
    def test_save_creates_file(self, tmp_path, monkeypatch):
        crawler = ScoreRankCrawler()
        # 重定向 data_dir 到 tmp_path
        monkeypatch.setattr(crawler, "data_dir", tmp_path)
        table = {600: 88500, 700: 2000}
        out = crawler.save(2025, table)
        assert out.exists()
        loaded = json.loads(out.read_text(encoding="utf-8"))
        assert loaded["600"] == 88500
        crawler.close()
