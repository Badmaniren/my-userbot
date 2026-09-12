from skills.resilient_secure_smart_crawler_hub_v4 import ResilientSecureSmartCrawlerHubV4
from skills.headers_rotator import HeadersRotator


class ResilientSecureSmartCrawlerHubV6Error(Exception):
    """Кастомное исключение для ResilientSecureSmartCrawlerHubV6."""
    pass


class ResilientSecureSmartCrawlerHubV6(ResilientSecureSmartCrawlerHubV4):
    def __init__(
        self,
        db_path=":memory:",
        max_memory_mb=128,
        calls=10,
        period=1.0,
        raise_on_limit=True
    ):
        super().__init__(
            db_path=db_path,
            max_memory_mb=max_memory_mb,
            calls=calls,
            period=period,
            raise_on_limit=raise_on_limit
        )
        self.headers_rotator = HeadersRotator()

    def validate_target_headers(self, url: str, timeout: int = 5) -> bool:
        try:
            return bool(self.headers_rotator.validate_headers_against_target(url, timeout))
        except Exception:
            if self.raise_on_limit:
                raise ResilientSecureSmartCrawlerHubV6Error("Header validation failed")
            return False

    def coordinate_expansion_safe(self, url: str, timeout: int = 5) -> bool:
        try:
            return bool(super().coordinate_expansion_safe(url, timeout))
        except Exception:
            if self.raise_on_limit:
                raise ResilientSecureSmartCrawlerHubV6Error("Safe coordinate expansion failed")
            return False

    def coordinate_expansion(self, url: str, timeout: int = 5):
        try:
            return super().coordinate_expansion(url, timeout)
        except Exception as e:
            if self.raise_on_limit:
                raise ResilientSecureSmartCrawlerHubV6Error(f"Coordinate expansion failed: {e}")
            raise e

    def process_stream(self, url: str, timeout: int = 5):
        try:
            return super().process_stream(url, timeout)
        except Exception as e:
            if self.raise_on_limit:
                raise ResilientSecureSmartCrawlerHubV6Error(f"Process stream failed: {e}")
            return False