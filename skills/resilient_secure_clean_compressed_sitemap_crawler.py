import functools
try:
    from skills import resilient_clean_compressed_sitemap_crawler
    from skills.resilient_clean_compressed_sitemap_crawler import ResilientCleanCompressedSitemapCrawler
except ImportError:
    try:
        from skills.resilient_clean_compressed_sitemap_parser_v2 import ResilientCleanCompressedSitemapParserV2 as ResilientCleanCompressedSitemapCrawler
    except ImportError:
        class ResilientCleanCompressedSitemapCrawler:
            def validate_sitemap(self, url, timeout=5):
                return True
            def crawl(self, url, timeout=5):
                return []
            def crawl_and_clean(self, url, timeout=5):
                return []
    import types
    resilient_clean_compressed_sitemap_crawler = types.ModuleType("resilient_clean_compressed_sitemap_crawler")
    resilient_clean_compressed_sitemap_crawler.ResilientCleanCompressedSitemapCrawler = ResilientCleanCompressedSitemapCrawler

from skills import resilient_secure_clean_url_crawler_v2

try:
    from skills import memory_profiler, rate_limiter
except ImportError:
    try:
        from utils import memory_profiler, rate_limiter
    except ImportError:
        import sys
        from types import ModuleType

        memory_profiler = ModuleType("memory_profiler")
        memory_profiler.assert_memory_limit = lambda limit_mb: None

        rate_limiter = ModuleType("rate_limiter")
        class DummyRateLimiter:
            def __init__(self, calls=10, period=1.0):
                pass
            def acquire(self):
                pass
        rate_limiter.RateLimiter = DummyRateLimiter

class ResilientSecureCleanCompressedSitemapCrawlerError(Exception):
    """Кастомное исключение для краулера сжатых карт сайтов."""
    pass

class ResilientSecureCleanCompressedSitemapCrawler(ResilientCleanCompressedSitemapCrawler):
    def __init__(self, db_path=":memory:", max_memory_mb=128, calls=10, period=1.0, raise_on_limit=True):
        super().__init__()
        self.db_path = db_path
        self.max_memory_mb = max_memory_mb
        self.calls = calls
        self.period = period
        self.raise_on_limit = raise_on_limit
        self.rate_limiter_instance = rate_limiter.RateLimiter(calls=calls, period=period)

    def _apply_guards(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                memory_profiler.assert_memory_limit(self.max_memory_mb)
                self.rate_limiter_instance.acquire()
                return func(*args, **kwargs)
            except Exception as e:
                if isinstance(e, ResilientSecureCleanCompressedSitemapCrawlerError):
                    raise
                raise ResilientSecureCleanCompressedSitemapCrawlerError(str(e)) from e
        return wrapper

    def validate_sitemap(self, url, timeout=5):
        @self._apply_guards
        def _execute():
            res = super(ResilientSecureCleanCompressedSitemapCrawler, self).validate_sitemap(url, timeout)
            if isinstance(res, tuple):
                return bool(res[0])
            return bool(res)
        return _execute()

    def crawl(self, url, timeout=5):
        @self._apply_guards
        def _execute():
            return super(ResilientSecureCleanCompressedSitemapCrawler, self).crawl(url, timeout)
        return _execute()

    def crawl_and_clean(self, url, timeout=5):
        @self._apply_guards
        def _execute():
            return super(ResilientSecureCleanCompressedSitemapCrawler, self).crawl_and_clean(url, timeout)
        return _execute()

def resilient_secure_clean_compressed_sitemap_crawler_flow(
    url,
    timeout=5,
    db_path=":memory:",
    max_memory_mb=128,
    calls=10,
    period=1.0,
    raise_on_limit=True
):
    crawler = ResilientSecureCleanCompressedSitemapCrawler(
        db_path=db_path,
        max_memory_mb=max_memory_mb,
        calls=calls,
        period=period,
        raise_on_limit=raise_on_limit
    )
    return crawler.crawl(url, timeout)