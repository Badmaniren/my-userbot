from skills.resilient_secure_clean_compressed_rss_archiver import (
    ResilientSecureCleanCompressedRSSArchiver,
    SecureCleanCompressedRSSArchiverError,
)
from skills.memory_profiler import (
    MemoryProfiler,
    assert_memory_limit,
    profile_memory,
    MemoryLimitExceeded,
)
from skills.rate_limiter import RateLimiter, RateLimitExceeded


class SmartSecureCompressedRSSCrawlerV4Error(Exception):
    """Базовое исключение для SmartSecureCompressedRSSCrawlerV4."""
    pass


class SmartSecureCompressedRSSCrawlerV4:
    def __init__(self, db_path=":memory:", max_memory_mb=128, calls=10, period=60, raise_on_limit=True):
        self.db_path = db_path
        self.max_memory_mb = max_memory_mb
        self.archiver = ResilientSecureCleanCompressedRSSArchiver(
            db_path=db_path,
            max_memory_mb=max_memory_mb,
            calls=calls,
            period=period,
            raise_on_limit=raise_on_limit,
        )
        self.memory_profiler = MemoryProfiler()
        self.rate_limiter = RateLimiter(calls=calls, period=period, raise_on_limit=raise_on_limit)
        self.raise_on_limit = raise_on_limit

    @profile_memory
    def archive_feed(self, url, timeout=10, force_refresh=False):
        assert_memory_limit(self.max_memory_mb)

        try:
            self.rate_limiter.acquire()
        except RateLimitExceeded:
            if self.raise_on_limit:
                raise
            return False

        return self.archiver.archive_feed(url, timeout=timeout, force_refresh=force_refresh)

    def get_archived_feed(self, url):
        return self.archiver.get_archived_feed(url)

    def coordinate_expansion(self, url, timeout=10):
        assert_memory_limit(self.max_memory_mb)
        try:
            self.rate_limiter.acquire()
        except RateLimitExceeded:
            if self.raise_on_limit:
                raise
            return False
        return True


def smart_secure_compressed_rss_crawler_v4_flow(
    url,
    timeout=10,
    db_path=":memory:",
    max_memory_mb=128,
    force_refresh=False,
    calls=10,
    period=60,
    raise_on_limit=True,
):
    crawler = SmartSecureCompressedRSSCrawlerV4(
        db_path=db_path,
        max_memory_mb=max_memory_mb,
        calls=calls,
        period=period,
        raise_on_limit=raise_on_limit,
    )
    return crawler.archive_feed(url, timeout=timeout, force_refresh=force_refresh)
