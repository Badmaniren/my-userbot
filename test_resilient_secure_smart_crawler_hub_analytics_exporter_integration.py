import unittest
import os
from skills.resilient_secure_smart_crawler_hub_analytics_exporter import ResilientSecureSmartCrawlerHubAnalyticsExporter
from skills.clean_compressed_db_storage import CleanCompressedDBStorage
from skills.resilient_secure_smart_crawler_hub_analytics_v2 import ResilientSecureSmartCrawlerHubAnalyticsV2

class TestResilientSecureSmartCrawlerHubAnalyticsExporterIntegration(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_crawler_hub_exporter.db"
        self.url = "https://example.com/sitemap.xml"
        self.timeout = 5
        self.max_memory_mb = 128
        self.calls = 10
        self.period = 1.0
        self.raise_on_limit = True

        if os.path.exists(self.db_path):
            os.remove(self.db_path)

        self.exporter = ResilientSecureSmartCrawlerHubAnalyticsExporter(
            db_path=self.db_path,
            max_memory_mb=self.max_memory_mb,
            calls=self.calls,
            period=self.period,
            raise_on_limit=self.raise_on_limit
        )

        self.storage = CleanCompressedDBStorage(db_path=self.db_path)
        self.analytics_v2 = ResilientSecureSmartCrawlerHubAnalyticsV2(
            db_path=self.db_path,
            max_memory_mb=self.max_memory_mb,
            calls=self.calls,
            period=self.period,
            raise_on_limit=self.raise_on_limit
        )

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_composition_and_analytics_export_flow(self):
        self.assertIsInstance(self.exporter, ResilientSecureSmartCrawlerHubAnalyticsExporter)
        
        cleaned_url = self.storage.clean_target_url(self.url)
        self.assertIsInstance(cleaned_url, str)

        headers_valid = self.exporter.validate_target_headers(self.url, self.timeout)
        self.assertIsInstance(headers_valid, bool)

        expansion_result = self.exporter.coordinate_expansion_safe(self.url, self.timeout)
        self.assertIsInstance(expansion_result, bool)

        stream_data = self.exporter.process_stream(self.url, self.timeout)
        self.assertIsNotNone(stream_data)

if __name__ == "__main__":
    unittest.main()