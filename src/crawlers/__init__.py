"""爬虫模块统一入口。"""
from .base import BaseCrawler
from .score_rank import ScoreRankCrawler, crawl_score_rank
from .admission_pdf import AdmissionPdfCrawler

__all__ = [
    "BaseCrawler",
    "ScoreRankCrawler",
    "crawl_score_rank",
    "AdmissionPdfCrawler",
]
