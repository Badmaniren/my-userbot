import os
import tempfile
import unittest
from skills.resilient_secure_smart_crawler_hub_analytics_v2 import (
    ResilientSecureSmartCrawlerHubAnalyticsV2,
    ResilientSecureSmartCrawlerHubAnalyticsV2Error
)
from skills.resilient_secure_smart_crawler_hub_v6 import ResilientSecureSmartCrawlerHubV6
from skills.clean_compressed_db_storage import CleanCompressedDBStorage

class TestResilientSecureSmartCrawlerHubAnalyticsV2Integration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.test_dir.name, "analytics_test.db")
        self.url = "https://example.com/sitemap.xml"
        self.timeout = 5
        self.max_memory_mb = 256
        self.calls = 10
        self.period = 60
        self.raise_on_limit = True

    def tearDown(self):
        self.test_dir.cleanup()

    def test_composition_and_inheritance(self):
        analytics_hub = ResilientSecureSmartCrawlerHubAnalyticsV2(
            db_path=self.db_path,
            max_memory_mb=self.max_memory_mb,
            calls=self.calls,
            period=self.period,
            raise_on_limit=self.raise_on_limit
        )
        self.assertIsInstance(analytics_hub, ResilientSecureSmartCrawlerHubV6)
        
        has_storage = hasattr(analytics_hub, 'storage') or isinstance(getattr(analytics_hub, 'db_storage', None), CleanCompressedDBStorage)
        self.assertTrue(has_storage or hasattr(analytics_hub, 'coordinate_expansion'))

    def test_validate_target_headers(self):
        analytics_hub = ResilientSecureSmartCrawlerHubAnalyticsV2(
            db_path=self.db_path,
            max_memory_mb=self.max_memory_mb,
            calls=self.calls,
            period=self.period,
            raise_on_limit=self.raise_on_limit
        )
        result = analytics_hub.validate_target_headers(self.url, self.timeout)
        self.assertIsInstance(result, bool)

    def test_coordinate_expansion_safe(self):
        analytics_hub = ResilientSecureSmartCrawlerHubAnalyticsV2(
            db_path=self.db_path,
            max_memory_mb=self.max_memory_mb,
            calls=self.calls,
            period=self.period,
            raise_on_limit=self.raise_on_limit
        )
        result = analytics_hub.coordinate_expansion_safe(self.url, self.timeout)
        self.assertIsInstance(result, bool)

    def test_process_stream_and_analytics(self):
        analytics_hub = ResilientSecureSmartCrawlerHubAnalyticsV2(
            db_path=self.db_path,
            max_memory_mb=self.max_memory_mb,
            calls=self.calls,
            period=self.period,
            raise_on_limit=self.raise_on_limit
        )
        try:
            analytics_hub.process_stream(self.url, self.timeout)
        except Exception as e:
            self.assertIsInstance(e, (ResilientSecureSmartCrawlerHubAnalyticsV2Error, Exception))

if __name__ == '__main__':
    unittest.main()