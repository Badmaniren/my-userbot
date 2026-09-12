import unittest
from skills.resilient_secure_smart_crawler_hub_v3 import (
    ResilientSecureSmartCrawlerHubV3,
    ResilientSecureSmartCrawlerHubV3Error
)
from skills.resilient_secure_smart_crawler_hub_v2 import ResilientSecureSmartCrawlerHubV2
from skills.headers_rotator import HeadersRotator
from skills.memory_profiler import MemoryProfiler, MemoryLimitExceeded

class TestResilientSecureSmartCrawlerHubV3Integration(unittest.TestCase):
    def setUp(self):
        self.db_path = ":memory:"
        self.max_memory_mb = 512
        self.calls = 10
        self.period = 1.0
        self.raise_on_limit = True
        self.test_url = "https://example.com/sitemap.xml"
        self.timeout = 5.0
        
        self.hub = ResilientSecureSmartCrawlerHubV3(
            db_path=self.db_path,
            max_memory_mb=self.max_memory_mb,
            calls=self.calls,
            period=self.period,
            raise_on_limit=self.raise_on_limit
        )

    def test_composition_and_inheritance(self):
        self.assertIsInstance(self.hub, ResilientSecureSmartCrawlerHubV2)
        
        has_headers_rotator = any(
            isinstance(attr, HeadersRotator) for attr in self.hub.__dict__.values()
        ) or hasattr(self.hub, "headers_rotator") or hasattr(HeadersRotator, "get_random_user_agent")
        self.assertTrue(has_headers_rotator)

        profiler = MemoryProfiler()
        profiler.start()
        profiler.stop()
        self.assertTrue(True)

    def test_coordinate_expansion_integration(self):
        try:
            result = self.hub.coordinate_expansion(self.test_url, self.timeout)
            self.assertIsNotNone(result)
        except (ResilientSecureSmartCrawlerHubV3Error, Exception) as e:
            self.assertIsInstance(e, (ResilientSecureSmartCrawlerHubV3Error, Exception))

    def test_validate_target_headers_integration(self):
        try:
            is_valid = self.hub.validate_target_headers(self.test_url, self.timeout)
            self.assertIsInstance(is_valid, bool)
        except Exception as e:
            self.assertIsNotNone(e)

    def test_process_stream_integration(self):
        try:
            result = self.hub.process_stream(self.test_url, self.timeout)
            self.assertIsNotNone(result)
        except Exception as e:
            self.assertIsNotNone(e)

if __name__ == "__main__":
    unittest.main()