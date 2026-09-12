import unittest
from skills.resilient_clean_url_crawler import ResilientCleanUrlCrawler
from skills.clean_url_crawler import CleanUrlCrawler
from skills.rate_limiter import RateLimiter

class TestResilientCleanUrlCrawlerIntegration(unittest.TestCase):
    def test_composition_and_functionality(self):
        crawler = ResilientCleanUrlCrawler(calls=10, period=1.0)
        self.assertIsInstance(crawler.clean_crawler, CleanUrlCrawler)
        self.assertIsInstance(crawler.rate_limiter, RateLimiter)
        
        test_url = "HTTPS://Example.com/Path/?utm_source=test#anchor"
        result = crawler.process_url(test_url, timeout=5)
        self.assertIsInstance(result, bool)

if __name__ == "__main__":
    unittest.main()