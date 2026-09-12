import gc
from skills import resilient_secure_clean_url_crawler_v2
from skills import smart_secure_compressed_sitemap_crawler_v2
from skills import memory_profiler

class ResilientSmartUrlAggregator:
    def __init__(self, db_path, max_memory_mb=128, calls=10, period=60):
        self.db_path = db_path
        self.max_memory_mb = max_memory_mb
        self.calls = calls
        self.period = period

        self.url_crawler = resilient_secure_clean_url_crawler_v2.ResilientSecureCleanUrlCrawlerV2(
            calls=calls, period=period
        )
        self.sitemap_crawler = smart_secure_compressed_sitemap_crawler_v2.SmartSecureCompressedSitemapCrawlerV2(
            db_path=db_path, max_memory_mb=max_memory_mb, calls=calls, period=period
        )

    def aggregate_expansion(self, url, timeout):
        try:
            memory_profiler.assert_memory_limit(self.max_memory_mb)

            crawler_success = self.url_crawler.process_url(url, timeout)
            if not crawler_success:
                return False

            self.sitemap_crawler.coordinate_expansion(url, timeout)
            return True
        except Exception as e:
            memory_profiler.force_gc()
            if isinstance(e, (MemoryError, RuntimeError)) and ("MemoryLimitExceeded" in str(e) or "RateLimitExceeded" in str(e)):
                raise e
            return False

    def validate_target(self, url, timeout):
        try:
            res = self.sitemap_crawler.validate_sitemap(url, timeout)
            return bool(res)
        except Exception:
            memory_profiler.force_gc()
            return False

    def coordinate_expansion(self, url, timeout):
        try:
            memory_profiler.assert_memory_limit(self.max_memory_mb)
            self.url_crawler.process_url(url, timeout)
            results = self.sitemap_crawler.coordinate_expansion(url, timeout)
            return results if results is not None else []
        except Exception:
            memory_profiler.force_gc()
            return []