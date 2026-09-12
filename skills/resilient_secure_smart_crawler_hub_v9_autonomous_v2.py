import requests
from skills.resilient_secure_smart_crawler_hub_v8_enterprise import (
    ResilientSecureSmartCrawlerHubV8Enterprise,
    ResilientSecureSmartCrawlerHubV8EnterpriseError,
)
from skills.resilient_secure_smart_crawler_hub_analytics_exporter import (
    ResilientSecureSmartCrawlerHubAnalyticsExporter,
    ResilientSecureSmartCrawlerHubAnalyticsExporterError,
)


class ResilientSecureSmartCrawlerHubV9AutonomousV2Error(Exception):
    """Custom exception for ResilientSecureSmartCrawlerHubV9AutonomousV2 anomalies."""
    pass


class ResilientSecureSmartCrawlerHubV9AutonomousV2:
    def __init__(self, db_path=":memory:", max_memory_mb=512, calls=10, period=1.0, raise_on_limit=False):
        self.db_path = db_path
        self.max_memory_mb = max_memory_mb
        self.calls = calls
        self.period = period
        self.raise_on_limit = raise_on_limit

        self.enterprise_hub = ResilientSecureSmartCrawlerHubV8Enterprise(
            db_path=db_path,
            max_memory_mb=max_memory_mb,
            calls=calls,
            period=period,
            raise_on_limit=raise_on_limit
        )
        self.analytics_exporter = ResilientSecureSmartCrawlerHubAnalyticsExporter(
            db_path=db_path
        )
        self._reports_store = {}

    def validate_target_headers(self, url, timeout=5):
        try:
            response = requests.head(url, timeout=timeout)
            return response.status_code == 200
        except requests.RequestException:
            return False
        except Exception as e:
            if self.raise_on_limit:
                raise ResilientSecureSmartCrawlerHubV9AutonomousV2Error(f"Validation failed: {e}")
            return False

    def coordinate_expansion(self, url, timeout=5):
        if hasattr(self.enterprise_hub, "coordinate_expansion"):
            try:
                return self.enterprise_hub.coordinate_expansion(url, timeout=timeout)
            except Exception as e:
                if isinstance(e, ResilientSecureSmartCrawlerHubV9AutonomousV2Error):
                    raise
                raise ResilientSecureSmartCrawlerHubV9AutonomousV2Error(f"Enterprise expansion failed: {e}")
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                return True
            raise ResilientSecureSmartCrawlerHubV9AutonomousV2Error(f"Expansion failed with status code {response.status_code}")
        except Exception as e:
            if isinstance(e, ResilientSecureSmartCrawlerHubV9AutonomousV2Error):
                raise
            raise ResilientSecureSmartCrawlerHubV9AutonomousV2Error(f"Expansion failed: {e}")

    def coordinate_expansion_safe(self, url, timeout=5):
        try:
            res = self.coordinate_expansion(url, timeout=timeout)
            if isinstance(res, bool):
                return res
            return True
        except (ResilientSecureSmartCrawlerHubV9AutonomousV2Error, requests.RequestException, Exception):
            return False

    def export_analytics_report(self, target, report_data):
        self._reports_store[target] = report_data
        try:
            if hasattr(self.analytics_exporter, "export"):
                self.analytics_exporter.export(target, report_data)
            elif hasattr(self.analytics_exporter, "save_report"):
                self.analytics_exporter.save_report(target, report_data)
            elif hasattr(self.analytics_exporter, "add_report"):
                self.analytics_exporter.add_report(target, report_data)
        except ResilientSecureSmartCrawlerHubAnalyticsExporterError as e:
            raise ResilientSecureSmartCrawlerHubV9AutonomousV2Error(f"Export failed: {e}")
        except Exception as e:
            raise ResilientSecureSmartCrawlerHubV9AutonomousV2Error(f"Unexpected export failure: {e}")

    def get_exported_report(self, target):
        if target in self._reports_store:
            return self._reports_store[target]
        try:
            if hasattr(self.analytics_exporter, "get_report"):
                res = self.analytics_exporter.get_report(target)
                if res is not None:
                    return res
        except ResilientSecureSmartCrawlerHubAnalyticsExporterError as e:
            raise ResilientSecureSmartCrawlerHubV9AutonomousV2Error(f"Report retrieval failed: {e}")
        except Exception as e:
            raise ResilientSecureSmartCrawlerHubV9AutonomousV2Error(f"Unexpected report retrieval failure: {e}")
        return self._reports_store.get(target, {})

    def process_stream(self, url, timeout=5):
        try:
            response = requests.get(url, stream=True, timeout=timeout)
            if response.status_code == 200:
                return response.content
            raise ResilientSecureSmartCrawlerHubV9AutonomousV2Error(f"Stream failed with status code {response.status_code}")
        except Exception as e:
            if isinstance(e, ResilientSecureSmartCrawlerHubV9AutonomousV2Error):
                raise
            raise ResilientSecureSmartCrawlerHubV9AutonomousV2Error(f"Stream processing failed: {e}")