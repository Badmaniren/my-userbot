from skills.resilient_secure_smart_crawler_hub_v3 import ResilientSecureSmartCrawlerHubV3
from skills.smart_secure_compressed_rss_crawler import SmartSecureCompressedRSSCrawler


class ResilientSecureSmartCrawlerHubV4Error(Exception):
    """Кастомное исключение для хаба версии 4."""
    pass


class ResilientSecureSmartCrawlerHubV4(ResilientSecureSmartCrawlerHubV3, SmartSecureCompressedRSSCrawler):
    """
    Эволюционировавший хаб интеллектуального сжатого краулинга (версия 4),
    наследующий функционал от v3 и SmartSecureCompressedRSSCrawler.
    """

    def __init__(
        self,
        db_path: str = ":memory:",
        max_memory_mb: int = 100,
        calls: int = 10,
        period: float = 1.0,
        raise_on_limit: bool = True
    ):
        # Инициализируем родительские классы корректно
        ResilientSecureSmartCrawlerHubV3.__init__(
            self,
            db_path=db_path,
            max_memory_mb=max_memory_mb,
            calls=calls,
            period=period,
            raise_on_limit=raise_on_limit
        )

    def coordinate_expansion(self, url: str, timeout: int = 5):
        try:
            return super().coordinate_expansion(url, timeout)
        except Exception as e:
            if isinstance(e, ResilientSecureSmartCrawlerHubV4Error):
                raise
            raise ResilientSecureSmartCrawlerHubV4Error(str(e)) from e

    def coordinate_expansion_safe(self, url: str, timeout: int = 5) -> bool:
        try:
            res = super().coordinate_expansion_safe(url, timeout)
            return bool(res)
        except Exception:
            return False

    def validate_target_headers(self, url: str, timeout: int = 5) -> bool:
        try:
            res = super().validate_target_headers(url, timeout)
            return bool(res)
        except Exception as e:
            if isinstance(e, ResilientSecureSmartCrawlerHubV4Error):
                raise
            raise ResilientSecureSmartCrawlerHubV4Error(str(e)) from e

    def process_stream(self, url: str, timeout: int = 5):
        try:
            return super().process_stream(url, timeout)
        except Exception as e:
            if isinstance(e, ResilientSecureSmartCrawlerHubV4Error):
                raise
            raise ResilientSecureSmartCrawlerHubV4Error(str(e)) from e