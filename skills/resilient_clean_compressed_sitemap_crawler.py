from skills.resilient_clean_compressed_sitemap_parser import (
    ResilientCleanCompressedSitemapParser,
    CleanCompressedSitemapParserV3
)
from skills.rate_limiter import RateLimiter, RateLimitExceeded


class ResilientCleanCompressedSitemapCrawlerError(Exception):
    """Пользовательское исключение для краулера."""
    pass


class ResilientCleanCompressedSitemapCrawler:
    def __init__(self, db_path=":memory:", calls=5, period=1.0, raise_on_limit=True):
        self.db_path = db_path
        try:
            self.rate_limiter = RateLimiter(
                db_path=db_path,
                calls=calls,
                period=period,
                raise_on_limit=raise_on_limit
            )
        except TypeError:
            try:
                self.rate_limiter = RateLimiter(
                    calls=calls,
                    period=period,
                    raise_on_limit=raise_on_limit
                )
            except TypeError:
                self.rate_limiter = RateLimiter(
                    calls=calls,
                    period=period
                )
        self.parser = CleanCompressedSitemapParserV3()
        self._parser_helper = ResilientCleanCompressedSitemapParser()

    def _acquire_rate_limit(self):
        self.rate_limiter.acquire()

    def crawl(self, url, timeout=5):
        try:
            self._acquire_rate_limit()
            return self._parser_helper.parse(url, timeout=timeout)
        except Exception as e:
            if isinstance(e, ResilientCleanCompressedSitemapCrawlerError):
                raise e
            raise ResilientCleanCompressedSitemapCrawlerError(str(e)) from e

    def crawl_and_clean(self, url, timeout=5):
        try:
            self._acquire_rate_limit()
            return self._parser_helper.parse_and_clean(url, timeout=timeout)
        except Exception as e:
            if isinstance(e, ResilientCleanCompressedSitemapCrawlerError):
                raise e
            raise ResilientCleanCompressedSitemapCrawlerError(str(e)) from e

    def validate_sitemap(self, url, timeout=5):
        try:
            self._acquire_rate_limit()
            result = self._parser_helper.validate_sitemap(url, timeout=timeout)
            if isinstance(result, tuple):
                return bool(result[0])
            return bool(result)
        except Exception as e:
            if isinstance(e, ResilientCleanCompressedSitemapCrawlerError):
                raise e
            return False


def resilient_clean_compressed_sitemap_crawler_flow(
    url, timeout=5, db_path=":memory:", calls=5, period=1.0, raise_on_limit=False
):
    crawler = ResilientCleanCompressedSitemapCrawler(
        db_path=db_path,
        calls=calls,
        period=period,
        raise_on_limit=raise_on_limit
    )
    return crawler.crawl(url, timeout=timeout)
