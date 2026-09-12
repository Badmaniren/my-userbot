import unittest
from skills.smart_secure_rss_crawler import SmartSecureRSSCrawler

class TestSmartSecureRSSCrawlerIntegration(unittest.TestCase):
    def test_smart_secure_rss_crawler_integration(self):
        crawler = SmartSecureRSSCrawler()
        self.assertTrue(hasattr(crawler, "coordinate_expansion"))

if __name__ == "__main__":
    unittest.main()