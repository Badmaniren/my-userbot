try:
    from skills import rate_limiter
except ImportError:
    rate_limiter = None

try:
    from skills import clean_url_crawler
except ImportError:
    clean_url_crawler = None

class ResilientCleanUrlCrawlerError(Exception):
    """Базовое исключение для ResilientCleanUrlCrawler."""
    pass

class ResilientCleanUrlCrawler:
    def __init__(self, calls=10, period=1.0, raise_on_limit=False):
        if rate_limiter and hasattr(rate_limiter, 'RateLimiter'):
            self.rate_limiter = rate_limiter.RateLimiter(calls=calls, period=period)
        else:
            self.rate_limiter = None

        if clean_url_crawler and hasattr(clean_url_crawler, 'CleanUrlCrawler'):
            self.clean_crawler = clean_url_crawler.CleanUrlCrawler()
        else:
            self.clean_crawler = None
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
        if not self.clean_crawler:
            return True
        try:
            return bool(self.clean_crawler.process_url(url, timeout))
        except Exception:
            return False

    def validate_crawled_link(self, url, timeout=3.0):
        if not self._acquire_limit():
            return False
        if not self.clean_crawler:
            return True
        try:
            return bool(self.clean_crawler.validate_crawled_link(url, timeout))
        except Exception:
            return False

    def extract_and_clean(self, html_content):
        if not self._acquire_limit():
            return []
        if not self.clean_crawler:
            return []
        try:
            return self.clean_crawler.extract_and_clean(html_content)
        except Exception:
            return []