from skills import memory_profiler, rate_limiter
from skills.smart_secure_compressed_sitemap_crawler_v2 import (
    SmartSecureCompressedSitemapCrawlerV2,
    SmartSecureCompressedSitemapCrawlerV2Error
)
from skills.resilient_secure_clean_url_crawler_v2 import (
    ResilientSecureCleanUrlCrawlerV2,
    ResilientSecureCleanUrlCrawlerV2Error
)
from skills.compressed_db_storage import CompressedDBStorage

RateLimiter = rate_limiter.RateLimiter

class ResilientSecureSmartCrawlerHub:
    def __init__(self, db_path, max_memory_mb, calls, period):
        self.max_memory_mb = max_memory_mb
        self.sitemap_crawler = SmartSecureCompressedSitemapCrawlerV2(
            db_path=db_path,
            max_memory_mb=max_memory_mb,
            calls=calls,
            period=period
        )
        self.url_crawler = ResilientSecureCleanUrlCrawlerV2(
            calls=calls,
            period=period
        )
        self.storage = CompressedDBStorage(db_path)
        self.rate_limiter = RateLimiter(calls=calls, period=period)

    def _check_memory(self):
        memory_profiler.assert_memory_limit(self.max_memory_mb)

    def crawl_sitemap(self, url, timeout=10):
        self._check_memory()
        return self.sitemap_crawler.crawl_and_clean(url, timeout=timeout)

    def process_url_securely(self, url, timeout=5):
        self.rate_limiter.acquire()
        try:
            return self.url_crawler.process_url(url, timeout)
        except ResilientSecureCleanUrlCrawlerV2Error:
            return False

    def save_data(self, key, data):
        self.storage.save_compressed_data(key, data)

    def get_data(self, key):
        return self.storage.get_compressed_data(key)
