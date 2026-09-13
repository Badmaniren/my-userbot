from skills.clean_compressed_sitemap_parser_v3 import CleanCompressedSitemapParserV3
from skills.resilient_clean_url_crawler import ResilientCleanUrlCrawler
from skills.rate_limiter import RateLimiter


class ResilientCleanCompressedSitemapCrawlerError(Exception):
    """Кастомное исключение для ResilientCleanCompressedSitemapCrawler."""
    pass


class ResilientCleanCompressedSitemapCrawler:
    def __init__(self, db_path=":memory:", max_memory_mb=128, calls=10, period=1.0, raise_on_limit=True):
        self.db_path = db_path
        self.max_memory_mb = max_memory_mb
        self.calls = calls
        self.period = period
        self.raise_on_limit = raise_on_limit

        try:
            self.parser = CleanCompressedSitemapParserV3(db_path=db_path)
        except TypeError:
            self.parser = CleanCompressedSitemapParserV3()
        self.url_crawler = ResilientCleanUrlCrawler(calls=calls, period=period, raise_on_limit=raise_on_limit)
        self.rate_limiter = RateLimiter(calls=calls, period=period)

    def crawl_sitemap(self, url: str, timeout: int = 5) -> list:
        try:
            self.rate_limiter.acquire()
            parsed_urls = self.parser.parse_sitemap(url, timeout=timeout)
            results = []
            for u in parsed_urls:
                if self.url_crawler.process_url(u, timeout=timeout):
                    results.append(u)
            return results
        except Exception as e:
            if self.raise_on_limit:
                raise ResilientCleanCompressedSitemapCrawlerError(str(e)) from e
            return []

    def crawl(self, url: str, timeout: int = 5) -> list:
        return self.crawl_sitemap(url, timeout=timeout)

    def crawl_and_clean(self, url: str, timeout: int = 5) -> list:
        return self.crawl_sitemap(url, timeout=timeout)

    def validate_sitemap(self, url: str, timeout: int = 5) -> bool:
        try:
            self.rate_limiter.acquire()
            return self.parser.validate_sitemap(url, timeout=timeout)
        except Exception as e:
            if self.raise_on_limit:
                raise ResilientCleanCompressedSitemapCrawlerError(str(e)) from e
            return False


def resilient_clean_compressed_sitemap_crawler_flow(
    url: str,
    timeout: int = 5,
    db_path: str = ":memory:",
    max_memory_mb: int = 128,
    calls: int = 10,
    period: float = 1.0,
    raise_on_limit: bool = True
):
    crawler = ResilientCleanCompressedSitemapCrawler(
        db_path=db_path,
        max_memory_mb=max_memory_mb,
        calls=calls,
        period=period,
        raise_on_limit=raise_on_limit
    )
    return crawler.crawl_sitemap(url, timeout=timeout)
