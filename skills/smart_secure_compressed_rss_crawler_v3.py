from skills import memory_profiler
from skills import smart_secure_compressed_rss_crawler
from skills.smart_secure_compressed_rss_crawler import SmartSecureCompressedRSSCrawler
from skills.resilient_secure_clean_compressed_rss_archiver import ResilientSecureCleanCompressedRSSArchiver
from skills.memory_profiler import MemoryProfiler


class SmartSecureCompressedRSSCrawlerV3Error(Exception):
    """Пользовательское исключение для ошибок SmartSecureCompressedRSSCrawlerV3."""
    pass


class SmartSecureCompressedRSSCrawlerV3(
    SmartSecureCompressedRSSCrawler,
    ResilientSecureCleanCompressedRSSArchiver,
    MemoryProfiler
):
    """Интеллектуальный краулер и архиватор RSS версии 3."""

    def __init__(self, db_path=":memory:", max_memory_mb=512, calls=10, period=1.0, raise_on_limit=True):
        super().__init__(db_path=db_path)
        self.max_memory_mb = max_memory_mb
        self.calls = calls
        self.period = period
        self.raise_on_limit = raise_on_limit

    def archive_feed(self, url, timeout=5, force_refresh=False):
        memory_profiler.assert_memory_limit(self.max_memory_mb)
        try:
            result = super().archive_feed(url, timeout=timeout, force_refresh=force_refresh)
            return bool(result)
        except Exception as e:
            if self.raise_on_limit:
                raise SmartSecureCompressedRSSCrawlerV3Error(str(e))
            return False

    def get_archived_feed(self, url):
        memory_profiler.assert_memory_limit(self.max_memory_mb)
        try:
            return super().get_archived_feed(url)
        except Exception as e:
            if self.raise_on_limit:
                raise SmartSecureCompressedRSSCrawlerV3Error(str(e))
            return None

    def coordinate_expansion(self, url):
        memory_profiler.assert_memory_limit(self.max_memory_mb)
        try:
            return super().coordinate_expansion(url)
        except Exception as e:
            if self.raise_on_limit:
                raise SmartSecureCompressedRSSCrawlerV3Error(str(e))
            return []


def smart_secure_compressed_rss_crawler_v3_flow(
    url,
    timeout=5,
    db_path=":memory:",
    max_memory_mb=512,
    force_refresh=False,
    calls=10,
    period=1.0,
    raise_on_limit=True
):
    memory_profiler.assert_memory_limit(max_memory_mb)
    try:
        result = smart_secure_compressed_rss_crawler.smart_secure_compressed_rss_crawler_flow(
            url=url,
            timeout=timeout,
            db_path=db_path,
            force_refresh=force_refresh
        )
        return bool(result)
    except Exception as e:
        if raise_on_limit:
            raise SmartSecureCompressedRSSCrawlerV3Error(str(e))
        return False