from skills import memory_profiler
from skills.memory_profiler import MemoryLimitExceeded
from skills.smart_secure_compressed_sitemap_crawler import SmartSecureCompressedSitemapCrawler
from skills.resilient_secure_clean_compressed_sitemap_crawler import ResilientSecureCleanCompressedSitemapCrawler

class SmartSecureCompressedSitemapCrawlerV2Error(Exception):
    """Базовое исключение для модуля V2."""
    pass

class SmartSecureCompressedSitemapCrawlerV2(SmartSecureCompressedSitemapCrawler, ResilientSecureCleanCompressedSitemapCrawler):
    """
    Интеллектуальный отказоустойчивый краулер V2.
    Композиция функционала Smart и Resilient краулеров.
    """
    def __init__(self, db_path, max_memory_mb, calls, period, raise_on_limit=True):
        # Инициализация обоих базовых классов
        SmartSecureCompressedSitemapCrawler.__init__(self, db_path, max_memory_mb, calls, period, raise_on_limit)
        ResilientSecureCleanCompressedSitemapCrawler.__init__(self, db_path, max_memory_mb, calls, period, raise_on_limit)

    def validate_sitemap(self, url, timeout):
        try:
            memory_profiler.assert_memory_limit(self.max_memory_mb)
            return ResilientSecureCleanCompressedSitemapCrawler.validate_sitemap(self, url, timeout)
        except MemoryLimitExceeded:
            raise
        except Exception as e:
            if "Memory" in type(e).__name__:
                raise
            raise SmartSecureCompressedSitemapCrawlerV2Error(f"Validation failed: {e}")

    def crawl(self, url, timeout):
        try:
            memory_profiler.assert_memory_limit(self.max_memory_mb)
            return ResilientSecureCleanCompressedSitemapCrawler.crawl(self, url, timeout)
        except MemoryLimitExceeded:
            raise
        except Exception as e:
            if "Memory" in type(e).__name__:
                raise
            raise SmartSecureCompressedSitemapCrawlerV2Error(f"Crawl failed: {e}")

    def crawl_and_clean(self, url, timeout):
        try:
            memory_profiler.assert_memory_limit(self.max_memory_mb)
            return SmartSecureCompressedSitemapCrawler.crawl_and_clean(self, url, timeout)
        except MemoryLimitExceeded:
            raise
        except Exception as e:
            if "Memory" in type(e).__name__:
                raise
            raise SmartSecureCompressedSitemapCrawlerV2Error(f"Crawl and clean failed: {e}")

    def coordinate_expansion(self, url, timeout):
        try:
            memory_profiler.assert_memory_limit(self.max_memory_mb)
            return SmartSecureCompressedSitemapCrawler.coordinate_expansion(self, url, timeout)
        except MemoryLimitExceeded:
            raise
        except Exception as e:
            if "Memory" in type(e).__name__:
                raise
            raise SmartSecureCompressedSitemapCrawlerV2Error(f"Expansion failed: {e}")

def smart_secure_compressed_sitemap_crawler_v2_flow(url, timeout, db_path, max_memory_mb, calls, period, raise_on_limit):
    """Функциональный поток выполнения V2."""
    crawler = SmartSecureCompressedSitemapCrawlerV2(
        db_path=db_path,
        max_memory_mb=max_memory_mb,
        calls=calls,
        period=period,
        raise_on_limit=raise_on_limit
    )
    
    if not crawler.validate_sitemap(url, timeout):
        return None
        
    data = crawler.crawl_and_clean(url, timeout)
    expansion = crawler.coordinate_expansion(url, timeout)
    
    return {
        "data": data,
        "expansion": expansion
    }
