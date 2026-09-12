from skills.resilient_secure_clean_compressed_sitemap_crawler import ResilientSecureCleanCompressedSitemapCrawler
from skills.smart_crawler import SmartCrawler

class SmartSecureCompressedSitemapCrawlerError(Exception):
    """Кастомное исключение для SmartSecureCompressedSitemapCrawler."""
    pass

class SmartSecureCompressedSitemapCrawler(ResilientSecureCleanCompressedSitemapCrawler, SmartCrawler):
    """
    Интеллектуальный краулер карт сайтов с поддержкой сжатия, кэширования, 
    проверки памяти и ограничения частоты запросов.
    """
    def __init__(self, db_path=":memory:", max_memory_mb=128, calls=10, period=1.0, raise_on_limit=True):
        self.db_path = db_path
        self.max_memory_mb = max_memory_mb
        self.calls = calls
        self.period = period
        self.raise_on_limit = raise_on_limit
        
        # Корректная инициализация базовых классов без заглушек
        try:
            super().__init__(db_path=db_path, max_memory_mb=max_memory_mb, calls=calls, period=period, raise_on_limit=raise_on_limit)
        except TypeError:
            ResilientSecureCleanCompressedSitemapCrawler.__init__(self)
        SmartCrawler.__init__(self)

    def validate_sitemap(self, url, timeout=5):
        try:
            res = super().validate_sitemap(url, timeout)
            return bool(res)
        except SmartSecureCompressedSitemapCrawlerError:
            raise
        except Exception:
            try:
                res = ResilientSecureCleanCompressedSitemapCrawler.validate_sitemap(self, url, timeout)
                return bool(res)
            except Exception:
                return False

    def crawl(self, url, timeout=5):
        try:
            return super().crawl(url, timeout)
        except SmartSecureCompressedSitemapCrawlerError:
            raise
        except Exception as e:
            raise SmartSecureCompressedSitemapCrawlerError(f"Crawl failed: {e}") from e

    def crawl_and_clean(self, url, timeout=5):
        try:
            return super().crawl_and_clean(url, timeout)
        except SmartSecureCompressedSitemapCrawlerError:
            raise
        except Exception as e:
            raise SmartSecureCompressedSitemapCrawlerError(f"Crawl and clean failed: {e}") from e

    def coordinate_expansion(self, url, timeout=5):
        try:
            if hasattr(SmartCrawler, "coordinate_expansion"):
                try:
                    return SmartCrawler.coordinate_expansion(self, url, timeout)
                except TypeError:
                    return SmartCrawler.coordinate_expansion(self, url)
            return super().coordinate_expansion(url, timeout)
        except TypeError:
            try:
                return super().coordinate_expansion(url)
            except Exception as e:
                raise SmartSecureCompressedSitemapCrawlerError(f"Coordinate expansion failed: {e}") from e
        except SmartSecureCompressedSitemapCrawlerError:
            raise
        except Exception as e:
            raise SmartSecureCompressedSitemapCrawlerError(f"Coordinate expansion failed: {e}") from e


def smart_secure_compressed_sitemap_crawler_flow(url, timeout=5, db_path=":memory:", max_memory_mb=128, calls=10, period=1.0, raise_on_limit=True):
    crawler = SmartSecureCompressedSitemapCrawler(
        db_path=db_path,
        max_memory_mb=max_memory_mb,
        calls=calls,
        period=period,
        raise_on_limit=raise_on_limit
    )
    return crawler.crawl(url, timeout)