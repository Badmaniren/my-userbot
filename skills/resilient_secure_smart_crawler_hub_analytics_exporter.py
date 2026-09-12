from skills.resilient_secure_smart_crawler_hub_analytics_v2 import ResilientSecureSmartCrawlerHubAnalyticsV2
from skills.clean_compressed_db_storage import CleanCompressedDBStorage


class ResilientSecureSmartCrawlerHubAnalyticsExporterError(Exception):
    """Кастомное исключение для экспортера аналитики краулер хаба."""
    pass


class ResilientSecureSmartCrawlerHubAnalyticsExporter:
    """Модуль экспорта аналитики краулер хаба v6 на базе композиции v2 и CleanCompressedDBStorage."""

    def __init__(self, db_path=":memory:", max_memory_mb=128, calls=10, period=1.0, raise_on_limit=False):
        self.analytics_v2 = ResilientSecureSmartCrawlerHubAnalyticsV2(
            db_path=db_path,
            max_memory_mb=max_memory_mb,
            calls=calls,
            period=period,
            raise_on_limit=raise_on_limit
        )
        self.storage = CleanCompressedDBStorage(db_path=db_path)

    def validate_target_headers(self, url: str, timeout: int) -> bool:
        return bool(self.analytics_v2.validate_target_headers(url, timeout))

    def coordinate_expansion_safe(self, url: str, timeout: int) -> bool:
        return bool(self.analytics_v2.coordinate_expansion_safe(url, timeout))

    def process_stream(self, url: str, timeout: int):
        return self.analytics_v2.process_stream(url, timeout)

    def export_analytics_report(self, url: str, raw_payload: str) -> None:
        try:
            cleaned_url = self.storage.clean_target_url(url)
            self.storage.save_cleaned_and_compressed_data(cleaned_url, raw_payload)
        except Exception as e:
            raise ResilientSecureSmartCrawlerHubAnalyticsExporterError(f"Export failed: {e}")

    def get_exported_report(self, url: str):
        try:
            cleaned_url = self.storage.clean_target_url(url)
            return self.storage.get_cleaned_and_compressed_data(cleaned_url)
        except Exception as e:
            raise ResilientSecureSmartCrawlerHubAnalyticsExporterError(f"Retrieval failed: {e}")