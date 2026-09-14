try:
    from skills import clean_url_crawler
except ImportError:
    from skills import smart_crawler as clean_url_crawler
from skills import rate_limiter

class ResilientCleanUrlCrawlerError(Exception):
    """Базовое исключение для ResilientCleanUrlCrawler."""
    pass

class ResilientCleanUrlCrawler:
    def __init__(self, calls=10, period=1.0, raise_on_limit=False):
        self.rate_limiter = rate_limiter.RateLimiter(calls=calls, period=period)
        self.clean_crawler = clean_url_crawler.CleanUrlCrawler()
        self.raise_on_limit = raise_on_limit

    def _acquire_limit(self):
        try:
            self.rate_limiter.acquire()
        except Exception as e:
            if self.raise_on_limit:
                raise ResilientCleanUrlCrawlerError(f"Rate limit exceeded: {e}")
            return False
        return True

    def process_url(self, url, timeout=5.0):
        if not self._acquire_limit():
            return False
        try:
            return bool(self.clean_crawler.process_url(url, timeout))
        except Exception:
            return False

    def validate_crawled_link(self, url, timeout=3.0):
        if not self._acquire_limit():
            return False
        try:
            return bool(self.clean_crawler.validate_crawled_link(url, timeout))
        except Exception:
            return False

    def extract_and_clean(self, html_content):
        if not self._acquire_limit():
            return []
        try:
            return self.clean_crawler.extract_and_clean(html_content)
        except Exception:
            return []