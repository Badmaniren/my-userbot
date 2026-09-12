import unittest
import io
from skills.resilient_secure_smart_crawler_hub_analytics import (
    ResilientSecureSmartCrawlerHubAnalytics,
    ResilientSecureSmartCrawlerHubAnalyticsError
)


class TestResilientSecureSmartCrawlerHubAnalyticsIntegration(unittest.TestCase):

    def test_integration_resilient_secure_smart_crawler_hub_analytics(self):
        analytics = ResilientSecureSmartCrawlerHubAnalytics(
            db_path=":memory:",
            max_memory_mb=512,
            calls=10,
            period=1.0,
            raise_on_limit=True
        )

        test_url = "https://example.com"

        metrics = analytics.collect_metrics(url=test_url, timeout=2)
        self.assertIsInstance(metrics, dict)
        self.assertIn("status", metrics)

        structure_valid = analytics.analyze_crawl_structure(test_url, timeout=2)
        self.assertIsInstance(structure_valid, bool)

        exported_data = analytics.export_analytics_data(test_url)
        self.assertIsInstance(exported_data, io.BytesIO)

        expansion_result = analytics.coordinate_expansion_with_analytics(test_url, timeout=2)
        self.assertIsNotNone(expansion_result)

        headers_valid = analytics.validate_target_headers(test_url, timeout=2.0)
        self.assertIsInstance(headers_valid, bool)

        safe_expansion = analytics.coordinate_expansion_safe(test_url, timeout=2.0)
        self.assertIsInstance(safe_expansion, bool)

        report = analytics.export_analytics_report()
        self.assertIsInstance(report, str)
        self.assertIn("Analytics Report", report)


if __name__ == "__main__":
    unittest.main()
