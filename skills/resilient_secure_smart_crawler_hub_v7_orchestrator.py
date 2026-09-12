from skills.resilient_secure_smart_crawler_hub_v6 import ResilientSecureSmartCrawlerHubV6


class ResilientSecureSmartCrawlerHubV7OrchestratorError(Exception):
    """Custom exception for ResilientSecureSmartCrawlerHubV7 orchestrator error."""
    pass


class ResilientSecureSmartCrawlerHubV7Error(Exception):
    """Custom exception for ResilientSecureSmartCrawlerHubV7 error."""
    pass


class ResilientSecureSmartCrawlerHubV7(ResilientSecureSmartCrawlerHubV6):
    """Resilient Secure Smart Crawler Hub V7 inheriting from V6."""

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

    def validate_target_headers(self, url: str, timeout: int = 5) -> bool:
        try:
            return super().validate_target_headers(url, timeout)
        except Exception as e:
            if isinstance(e, ResilientSecureSmartCrawlerHubV7Error):
                raise
            if self.raise_on_limit:
                raise ResilientSecureSmartCrawlerHubV7Error(f"Header validation failed: {e}") from e
            return False

    def coordinate_expansion_safe(self, url: str, timeout: int = 5) -> bool:
        try:
            return super().coordinate_expansion_safe(url, timeout)
        except Exception as e:
            if isinstance(e, ResilientSecureSmartCrawlerHubV7Error):
                raise
            if self.raise_on_limit:
                raise ResilientSecureSmartCrawlerHubV7Error(f"Safe expansion failed: {e}") from e
            return False

    def coordinate_expansion(self, url: str, timeout: int = 5):
        try:
            return super().coordinate_expansion(url, timeout)
        except Exception as e:
            if isinstance(e, ResilientSecureSmartCrawlerHubV7Error):
                raise
            raise ResilientSecureSmartCrawlerHubV7Error(f"Expansion failed: {e}") from e

    def process_stream(self, url: str, timeout: int = 5):
        try:
            return super().process_stream(url, timeout)
        except Exception as e:
            if isinstance(e, ResilientSecureSmartCrawlerHubV7Error):
                raise
            if self.raise_on_limit:
                raise ResilientSecureSmartCrawlerHubV7Error(f"Process stream failed: {e}") from e
            return False


def start_new(url, timeout=5, db_path=":memory:", max_memory_mb=128, calls=10, period=1.0, raise_on_limit=True):
    try:
        hub = ResilientSecureSmartCrawlerHubV7(
            db_path=db_path,
            max_memory_mb=max_memory_mb,
            calls=calls,
            period=period,
            raise_on_limit=raise_on_limit
        )
        return hub.process_stream(url, timeout)
    except Exception as e:
        if isinstance(e, ResilientSecureSmartCrawlerHubV7OrchestratorError):
            raise
        raise ResilientSecureSmartCrawlerHubV7OrchestratorError(str(e)) from e
