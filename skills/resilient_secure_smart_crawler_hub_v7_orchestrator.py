from skills.resilient_secure_smart_crawler_hub_v6 import ResilientSecureSmartCrawlerHubV6
from skills.resilient_secure_smart_crawler_hub_analytics_exporter import ResilientSecureSmartCrawlerHubAnalyticsExporter


class ResilientSecureSmartCrawlerHubV7OrchestratorError(Exception):
    """Custom exception for ResilientSecureSmartCrawlerHubV7Orchestrator errors."""
    pass


class ResilientSecureSmartCrawlerHubV7Orchestrator:
    """
    Absolute orchestrator for crawler hub v7 based on composition of v6 hub 
    and analytics exporter, with secure compressed storage.
    """

    def __init__(self, db_path=":memory:", max_memory_mb=100, calls=10, period=1.0, raise_on_limit=True):
        self.db_path = db_path
        self.max_memory_mb = max_memory_mb
        self.calls = calls
        self.period = period
        self.raise_on_limit = raise_on_limit

        self.hub_v6 = ResilientSecureSmartCrawlerHubV6(
            db_path=db_path,
            max_memory_mb=max_memory_mb,
            calls=calls,
            period=period,
            raise_on_limit=raise_on_limit
        )
        self.analytics_exporter = ResilientSecureSmartCrawlerHubAnalyticsExporter(
            db_path=db_path
        )

    def validate_target_headers(self, url: str, timeout: int) -> bool:
        try:
            return bool(self.hub_v6.validate_target_headers(url, timeout))
        except Exception as e:
            if self.raise_on_limit or isinstance(e, ResilientSecureSmartCrawlerHubV7OrchestratorError):
                raise ResilientSecureSmartCrawlerHubV7OrchestratorError(str(e)) from e
            raise

    def coordinate_expansion_safe(self, url: str, timeout: int) -> bool:
        try:
            return bool(self.hub_v6.coordinate_expansion_safe(url, timeout))
        except Exception as e:
            if self.raise_on_limit or isinstance(e, ResilientSecureSmartCrawlerHubV7OrchestratorError):
                raise ResilientSecureSmartCrawlerHubV7OrchestratorError(str(e)) from e
            raise

    def coordinate_expansion(self, url: str, timeout: int):
        try:
            return self.hub_v6.coordinate_expansion(url, timeout)
        except Exception as e:
            raise ResilientSecureSmartCrawlerHubV7OrchestratorError(str(e)) from e

    def process_stream(self, url: str, timeout: int):
        try:
            return self.hub_v6.process_stream(url, timeout)
        except Exception as e:
            if self.raise_on_limit or isinstance(e, ResilientSecureSmartCrawlerHubV7OrchestratorError):
                raise ResilientSecureSmartCrawlerHubV7OrchestratorError(str(e)) from e
            raise

    def export_analytics_report(self, target: str, report_data: dict):
        try:
            return self.analytics_exporter.export_analytics_report(target, report_data)
        except Exception as e:
            if self.raise_on_limit or isinstance(e, ResilientSecureSmartCrawlerHubV7OrchestratorError):
                raise ResilientSecureSmartCrawlerHubV7OrchestratorError(str(e)) from e
            raise

    def get_exported_report(self, target: str):
        try:
            return self.analytics_exporter.get_exported_report(target)
        except Exception as e:
            if self.raise_on_limit or isinstance(e, ResilientSecureSmartCrawlerHubV7OrchestratorError):
                raise ResilientSecureSmartCrawlerHubV7OrchestratorError(str(e)) from e
            raise