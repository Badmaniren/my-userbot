from skills.resilient_secure_smart_crawler_hub_v6 import ResilientSecureSmartCrawlerHubV6
from skills.clean_compressed_db_storage import CleanCompressedDBStorage

class ResilientSecureSmartCrawlerHubAnalyticsV2Error(Exception):
    """Custom exception for ResilientSecureSmartCrawlerHubAnalyticsV2 errors."""
    pass

class ResilientSecureSmartCrawlerHubAnalyticsV2(ResilientSecureSmartCrawlerHubV6):
    """
    Advanced analytics module for crawler hub v6, integrating data compression
    and secure rate-limiting for safe metric collection and export.
    """
    def __init__(self, db_path=":memory:", max_memory_mb=128, calls=10, period=1.0, raise_on_limit=True):
        super().__init__(
            db_path=db_path,
            max_memory_mb=max_memory_mb,
            calls=calls,
            period=period,
            raise_on_limit=raise_on_limit
        )
        self.storage = CleanCompressedDBStorage(db_path=db_path)
        self.db_storage = self.storage

    def validate_target_headers(self, url, timeout):
        try:
            result = super().validate_target_headers(url, timeout)
            return bool(result)
        except Exception as e:
            if self.raise_on_limit:
                raise ResilientSecureSmartCrawlerHubAnalyticsV2Error(str(e)) from e
            return False

    def coordinate_expansion_safe(self, url, timeout):
        try:
            result = super().coordinate_expansion_safe(url, timeout)
            return bool(result)
        except Exception as e:
            if self.raise_on_limit:
                raise ResilientSecureSmartCrawlerHubAnalyticsV2Error(str(e)) from e
            return False

    def coordinate_expansion(self, url, timeout):
        try:
            return super().coordinate_expansion(url, timeout)
        except Exception as e:
            raise ResilientSecureSmartCrawlerHubAnalyticsV2Error(str(e)) from e

    def process_stream(self, url, timeout):
        try:
            return super().process_stream(url, timeout)
        except Exception as e:
            raise ResilientSecureSmartCrawlerHubAnalyticsV2Error(str(e)) from e