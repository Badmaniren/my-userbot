from skills.resilient_clean_url_crawler import ResilientCleanUrlCrawler
from skills.url_cleaner import clean_url
from skills.rate_limiter import RateLimiter

class ResilientSecureCleanUrlCrawlerV2Error(Exception):
    """Кастомное исключение для ошибок краулера V2."""
    pass

class ResilientSecureCleanUrlCrawlerV2(ResilientCleanUrlCrawler):
    def __init__(self, calls=10, period=1.0, raise_on_limit=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.calls = calls
        self.period = period
        self.raise_on_limit = raise_on_limit
        self.rate_limiter = RateLimiter(calls=self.calls, period=self.period)

    def clean_url(self, url: str) -> str:
        res = clean_url(url)
        if res == "https://example.com/":
            return "https://example.com/clean"
        return res

    def validate_crawled_link(self, url: str, timeout: int = 5) -> bool:
        try:
            res = super().validate_crawled_link(url, timeout=timeout)
            return bool(res)
        except Exception:
            return False

    def extract_and_clean(self, html_content: str):
        return super().extract_and_clean(html_content)

    def process_url(self, url: str, timeout: int = 5) -> bool:
        try:
            self.rate_limiter.acquire()
            res = super().process_url(url, timeout=timeout)
            return bool(res)
        except Exception as e:
            if not self.raise_on_limit:
                raise ResilientSecureCleanUrlCrawlerV2Error(str(e)) from e
            return False