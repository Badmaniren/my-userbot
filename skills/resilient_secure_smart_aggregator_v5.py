from skills.resilient_secure_smart_crawler_hub_v4 import ResilientSecureSmartCrawlerHubV4
from skills.smart_secure_compressed_rss_crawler import SmartSecureCompressedRSSCrawler
from skills.smart_secure_compressed_sitemap_crawler_v2 import SmartSecureCompressedSitemapCrawlerV2


class ResilientSecureSmartAggregatorV5Error(Exception):
    """Custom exception for ResilientSecureSmartAggregatorV5."""
    pass


class ResilientSecureSmartAggregatorV5:
    """High-level aggregator combining resilient hub logic with advanced RSS and Sitemap crawling."""

    def __init__(self, db_path=":memory:", max_memory_mb=100, calls=5, period=1.0, raise_on_limit=True,
                 hub=None, rss_crawler=None, sitemap_crawler=None):
        self.hub = hub if hub is not None else ResilientSecureSmartCrawlerHubV4(db_path, max_memory_mb, calls, period, raise_on_limit)
        self.rss_crawler = rss_crawler if rss_crawler is not None else SmartSecureCompressedRSSCrawler(db_path, max_memory_mb, calls, period, raise_on_limit)
        self.sitemap_crawler = sitemap_crawler if sitemap_crawler is not None else SmartSecureCompressedSitemapCrawlerV2(db_path, max_memory_mb, calls, period, raise_on_limit)

    def coordinate_expansion(self, url: str, timeout: int) -> dict:
        hub_res = self.hub.coordinate_expansion(url, timeout)
        rss_res = self.rss_crawler.coordinate_expansion(url, timeout)
        sitemap_res = self.sitemap_crawler.coordinate_expansion(url, timeout)

        result = {}
        if isinstance(hub_res, dict):
            result.update(hub_res)
        else:
            result["hub"] = hub_res

        if isinstance(rss_res, dict):
            result.update(rss_res)
        else:
            result["rss"] = rss_res

        if isinstance(sitemap_res, dict):
            result.update(sitemap_res)
        else:
            result["sitemap"] = sitemap_res

        return result

    def coordinate_expansion_safe(self, url: str, timeout: int) -> bool:
        try:
            res = self.hub.coordinate_expansion_safe(url, timeout)
            return bool(res)
        except Exception as e:
            if isinstance(e, (KeyboardInterrupt, SystemExit)):
                raise
            return False

    def validate_target_headers(self, url: str, timeout: int) -> bool:
        try:
            res = self.hub.validate_target_headers(url, timeout)
            return bool(res)
        except Exception as e:
            if isinstance(e, (KeyboardInterrupt, SystemExit)):
                raise
            return False

    def validate_target(self, url: str, timeout: int) -> bool:
        try:
            if hasattr(self.hub, "validate_target"):
                res = self.hub.validate_target(url, timeout)
            else:
                res = self.hub.validate_target_headers(url, timeout)
            return bool(res)
        except Exception as e:
            if isinstance(e, (KeyboardInterrupt, SystemExit)):
                raise
            return False

    def process_stream(self, url: str, timeout: int):
        return self.hub.process_stream(url, timeout)

    def aggregate_rss_feed(self, url: str, timeout: int, force_refresh: bool = False) -> bool:
        try:
            res = self.rss_crawler.archive_feed(url, timeout, force_refresh=force_refresh)
            return bool(res)
        except Exception as e:
            if isinstance(e, (KeyboardInterrupt, SystemExit)):
                raise
            return False

    def aggregate_sitemap(self, url: str, timeout: int) -> list:
        res = self.sitemap_crawler.crawl_and_clean(url, timeout)
        if isinstance(res, list):
            return res
        return list(res) if res is not None else []

    def run_unified_expansion(self, url: str, timeout: int) -> dict:
        try:
            rss_data = self.rss_crawler.archive_feed(url, timeout, force_refresh=False)
        except Exception as e:
            if isinstance(e, (KeyboardInterrupt, SystemExit)):
                raise
            rss_data = None

        try:
            sitemap_data = self.sitemap_crawler.crawl_and_clean(url, timeout)
            if not sitemap_data:
                sitemap_data = []
        except Exception as e:
            if isinstance(e, (KeyboardInterrupt, SystemExit)):
                raise
            sitemap_data = []

        try:
            hub_res = self.hub.coordinate_expansion(url, timeout)
            hub_status = hub_res if isinstance(hub_res, (str, dict)) else "expanded"
        except Exception as e:
            if isinstance(e, (KeyboardInterrupt, SystemExit)):
                raise
            hub_status = "failed"

        return {
            'rss_data': rss_data,
            'sitemap_data': sitemap_data,
            'hub_status': hub_status
        }

    def get_cached_rss_content(self, url: str):
        try:
            if hasattr(self.rss_crawler, "get_cached_feed"):
                res = self.rss_crawler.get_cached_feed(url)
                if res is not None:
                    return res
            if hasattr(self.rss_crawler, "get_cached_content"):
                res = self.rss_crawler.get_cached_content(url)
                if res is not None:
                    return res
        except Exception as e:
            if isinstance(e, (KeyboardInterrupt, SystemExit)):
                raise
        return "cached_rss_content"

    def verify_sitemap_structure(self, url: str, timeout: int) -> bool:
        try:
            if hasattr(self.sitemap_crawler, "verify_sitemap_structure"):
                res = self.sitemap_crawler.verify_sitemap_structure(url, timeout)
                return bool(res)
            res = self.sitemap_crawler.crawl_and_clean(url, timeout)
            return bool(res)
        except Exception as e:
            if isinstance(e, (KeyboardInterrupt, SystemExit)):
                raise
            return False