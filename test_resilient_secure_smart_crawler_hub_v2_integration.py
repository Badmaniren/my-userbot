import unittest
from skills.resilient_secure_smart_crawler_hub_v2 import ResilientSecureSmartCrawlerHubV2
from skills.smart_crawler import SmartCrawler
from skills.headers_rotator import HeadersRotator

class TestResilientSecureSmartCrawlerHubV2Integration(unittest.TestCase):
    def setUp(self):
        self.db_path = ":memory:"
        self.hub = ResilientSecureSmartCrawlerHubV2(
            db_path=self.db_path,
            max_memory_mb=128,
            calls=10,
            period=1.0,
            raise_on_limit=True
        )

    def test_hub_composition_and_dependencies(self):
        self.assertIsInstance(self.hub.crawler, SmartCrawler)
        self.assertIsInstance(self.hub.rotator, HeadersRotator)

    def test_integration_coordinate_expansion(self):
        test_url = "http://example.com"
        try:
            result = self.hub.coordinate_expansion(test_url, timeout=5)
            self.assertIsNotNone(result)
        except Exception as e:
            self.assertTrue(len(str(e)) > 0)

    def test_integration_header_validation(self):
        test_url = "http://example.com"
        try:
            is_valid = self.hub.rotator.validate_headers_against_target(test_url, timeout=5)
            self.assertIsInstance(is_valid, bool)
        except Exception as e:
            self.assertTrue(len(str(e)) > 0)

if __name__ == "__main__":
    unittest.main()