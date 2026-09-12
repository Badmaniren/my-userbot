from skills import resilient_secure_clean_compressed_rss_archiver
from skills import memory_profiler
from skills import rate_limiter


class SmartSecureCompressedRSSCrawlerV4Error(Exception):
    """Кастомное исключение для ошибок SmartSecureCompressedRSSCrawlerV4."""
    pass


class SmartSecureCompressedRSSCrawlerV4:
    def __init__(
        self,
        db_path=":memory:",
        max_memory_mb=128,
        calls=10,
        period=60,
        raise_on_limit=True
    ):
        self.db_path = db_path
        self.max_memory_mb = max_memory_mb
        self.calls = calls
        self.period = period
        self.raise_on_limit = raise_on_limit
        self.archiver = resilient_secure_clean_compressed_rss_archiver.ResilientSecureCleanCompressedRSSArchiver(
            db_path=self.db_path,
            max_memory_mb=self.max_memory_mb,
            calls=self.calls,
            period=self.period,
            raise_on_limit=self.raise_on_limit
        )
        self.memory_profiler = memory_profiler.MemoryProfiler()
        self.rate_limiter = rate_limiter.RateLimiter(
            calls=self.calls,
            period=self.period,
            raise_on_limit=self.raise_on_limit
        )

    def archive_feed(self, url, timeout=10, force_refresh=False):
        memory_profiler.assert_memory_limit(self.max_memory_mb)
        try:
            self.rate_limiter.acquire()
        except rate_limiter.RateLimitExceeded:
            if self.raise_on_limit:
                raise
            return False

        def _do_archive():
            archiver = resilient_secure_clean_compressed_rss_archiver.SecureCleanCompressedRSSArchiver(
                db_path=self.db_path,
                max_memory_mb=self.max_memory_mb,
                calls=self.calls,
                period=self.period,
                raise_on_limit=self.raise_on_limit
            )
            return archiver.archive_feed(url, timeout, force_refresh)

        return memory_profiler.profile_memory(_do_archive)()

    def get_archived_feed(self, url):
        archiver = resilient_secure_clean_compressed_rss_archiver.SecureCleanCompressedRSSArchiver(
            db_path=self.db_path,
            max_memory_mb=self.max_memory_mb,
            calls=self.calls,
            period=self.period,
            raise_on_limit=self.raise_on_limit
        )
        return archiver.get_archived_feed(url)

    def coordinate_expansion(self, url):
        memory_profiler.assert_memory_limit(self.max_memory_mb)
        try:
            self.rate_limiter.acquire()
        except rate_limiter.RateLimitExceeded:
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
    raise_on_limit=True
):
    crawler = SmartSecureCompressedRSSCrawlerV4(
        db_path=db_path,
        max_memory_mb=max_memory_mb,
        calls=calls,
        period=period,
        raise_on_limit=raise_on_limit
    )
    return crawler.archive_feed(url, timeout, force_refresh)
