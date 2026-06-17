"""爬虫基类。

特性：
- 伪装浏览器 User-Agent
- 自动重试（3 次，指数退避）
- 统一日志
- 超时控制
"""
from __future__ import annotations

import logging
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# 默认 UA：模拟 Chrome on Windows
DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


class BaseCrawler:
    """所有爬虫的基类。

    用法：
        crawler = BaseCrawler(base_url="https://www.zjzs.net")
        response = crawler.get("/path/to/page")
    """

    DEFAULT_BASE_URL = "https://www.zjzs.net"
    DEFAULT_TIMEOUT = 15
    DEFAULT_MAX_RETRIES = 3
    RETRY_STATUS_CODES = [429, 500, 502, 503, 504]

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        user_agent: str = DEFAULT_UA,
        max_retries: int = DEFAULT_MAX_RETRIES,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.user_agent = user_agent
        self.session = self._build_session(max_retries)
        self.log = logging.getLogger(self.__class__.__name__)

    def _build_session(self, max_retries: int) -> requests.Session:
        """构造带重试机制的 Session。"""
        session = requests.Session()
        session.headers.update({
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": self.base_url + "/",
        })
        retry = Retry(
            total=max_retries,
            backoff_factor=1.0,  # 1s, 2s, 4s
            status_forcelist=self.RETRY_STATUS_CODES,
            allowed_methods=["GET", "HEAD"],
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def get(self, path: str, params: Optional[dict] = None, **kwargs):
        """GET 请求。

        Args:
            path: URL 路径（绝对或相对）
            params: 查询参数
            **kwargs: 透传给 requests
        """
        url = path if path.startswith("http") else f"{self.base_url}{path}"
        self.log.info(f"GET {url} params={params}")
        response = self.session.get(url, params=params, timeout=self.timeout, **kwargs)
        response.raise_for_status()
        return response

    def close(self):
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
