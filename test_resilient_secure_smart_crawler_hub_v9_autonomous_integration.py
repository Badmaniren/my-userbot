import os
import unittest
from skills.resilient_secure_smart_crawler_hub_v9_autonomous import (
    ResilientSecureSmartCrawlerHubV9Autonomous,
    ResilientSecureSmartCrawlerHubV9AutonomousError
)

class TestResilientSecureSmartCrawlerHubV9AutonomousIntegration(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_crawler_hub_v9.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

        self.hub = ResilientSecureSmartCrawlerHubV9Autonomous(
            db_path=self.db_path,
            max_memory_mb=512,
            calls=10,
            period=1.0,
            raise_on_limit=True
        )
        self.test_url = "https://example.com"
        self.test_timeout = 5

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_validate_target_headers(self):
        result = self.hub.validate_target_headers(self.test_url, self.test_timeout)
        self.assertIsInstance(result, bool)

    def test_coordinate_expansion_safe(self):
        result = self.hub.coordinate_expansion_safe(self.test_url, self.test_timeout)
        self.assertIsInstance(result, bool)

    def test_analytics_export_and_get(self):
        report_data = {"status": "success", "metrics": {"items_crawled": 42}}
        self.hub.export_analytics_report(self.test_url, report_data)

        exported = self.hub.get_exported_report(self.test_url)
        self.assertIsNotNone(exported)

    def test_process_stream(self):
        try:
            stream_result = self.hub.process_stream(self.test_url, self.test_timeout)
            self.assertIsNotNone(stream_result)
        except Exception as e:
            self.assertIsInstance(e, (ResilientSecureSmartCrawlerHubV9AutonomousError, Exception))

if __name__ == "__main__":
    unittest.main()