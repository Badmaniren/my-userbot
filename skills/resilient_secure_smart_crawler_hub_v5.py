import io

from skills.resilient_secure_smart_crawler_hub_v4 import ResilientSecureSmartCrawlerHubV4
try:
    from skills.smart_secure_compressed_sitemap_crawler_v2 import SmartSecureCompressedSitemapCrawlerV2
except ImportError:
    try:
        from smart_secure_compressed_sitemap_crawler_v2 import SmartSecureCompressedSitemapCrawlerV2
    except ImportError:
        SmartSecureCompressedSitemapCrawlerV2 = None

class ResilientSecureSmartCrawlerHubV5Error(Exception):
    """Custom exception for ResilientSecureSmartCrawlerHubV5 errors."""
    pass

class ResilientSecureSmartCrawlerHubV5(ResilientSecureSmartCrawlerHubV4):
    def __init__(self, db_path=":memory:", max_memory_mb=100, calls=10, period=1.0, raise_on_limit=True):
        super().__init__(db_path=db_path, max_memory_mb=max_memory_mb, calls=calls, period=period, raise_on_limit=raise_on_limit)
        self.db_path = db_path
        self.max_memory_mb = max_memory_mb
        self.calls = calls
        self.period = period
        self.raise_on_limit = raise_on_limit
        if SmartSecureCompressedSitemapCrawlerV2 is not None:
            try:
                self.sitemap_crawler = SmartSecureCompressedSitemapCrawlerV2(
                    db_path=db_path,
                    max_memory_mb=max_memory_mb,
                    calls=calls,
                    period=period,
                    raise_on_limit=raise_on_limit
                )
            except TypeError:
                try:
                    self.sitemap_crawler = SmartSecureCompressedSitemapCrawlerV2(
                        db_path=db_path,
                        max_memory_mb=max_memory_mb,
                        calls=calls,
                        period=period
                    )
                except TypeError:
                    self.sitemap_crawler = SmartSecureCompressedSitemapCrawlerV2()
        else:
            self.sitemap_crawler = None

    def coordinate_expansion(self, url, timeout=5):
        try:
            v4_results = super().coordinate_expansion(url, timeout)
            sitemap_results = []
            if self.sitemap_crawler is not None and hasattr(self.sitemap_crawler, "coordinate_expansion"):
                sitemap_results = self.sitemap_crawler.coordinate_expansion(url, timeout)

            if isinstance(v4_results, list) and isinstance(sitemap_results, list):
                return list(set(v4_results + sitemap_results))
            elif isinstance(v4_results, list):
                return v4_results
            elif isinstance(sitemap_results, list):
                return sitemap_results
            return []
        except Exception as e:
            raise ResilientSecureSmartCrawlerHubV5Error(f"Coordinate expansion failed: {e}") from e

    def coordinate_expansion_safe(self, url, timeout=5):
        try:
            res = self.coordinate_expansion(url, timeout)
            if isinstance(res, list):
                return len(res) > 0
            return bool(res)
        except Exception as e:
            if self.raise_on_limit and isinstance(e, ResilientSecureSmartCrawlerHubV5Error):
                raise
            return False

    def validate_target_headers(self, url, timeout=5):
        try:
            res = super().validate_target_headers(url, timeout)
            return bool(res)
        except Exception as e:
            if self.raise_on_limit and isinstance(e, ResilientSecureSmartCrawlerHubV5Error):
                raise
            return False

    def process_stream(self, url, timeout=5):
        try:
            return super().process_stream(url, timeout)
        except Exception as e:
            raise ResilientSecureSmartCrawlerHubV5Error(f"Stream processing failed: {e}") from e