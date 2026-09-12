import unittest
from unittest.mock import MagicMock, patch
from skills.smart_secure_rss_crawler import SmartSecureRSSCrawler, SmartSecureRSSCrawlerError
from skills.rate_limiter import RateLimitExceeded

class TestSmartSecureRSSCrawler(unittest.TestCase):
    def setUp(self):
        self.url = "https://example.com/rss"
        self.timeout = 10
        self.crawler_instance = SmartSecureRSSCrawler(db_path=":memory:")

    def test_archive_feed_success(self):
        with patch('skills.smart_secure_rss_crawler.SmartCrawler.coordinate_expansion') as mock_coord, \
             patch('skills.smart_secure_rss_crawler.SecureCleanCompressedRSSArchiver.archive_feed') as mock_arch:
            
            mock_coord.return_value = None
            mock_arch.return_value = True
            
            result = self.crawler_instance.archive_feed(self.url, timeout=self.timeout)
            
            self.assertTrue(result)
            mock_coord.assert_called_once_with(self.url)
            mock_arch.assert_called_once_with(self.url, timeout=self.timeout, force_refresh=False)

    def test_archive_feed_rate_limit_exceeded(self):
        self.crawler_instance.raise_on_limit = True
        with patch('skills.smart_secure_rss_crawler.RateLimiter.acquire', side_effect=RateLimitExceeded("Limit")):
            with self.assertRaises(SmartSecureRSSCrawlerError):
                self.crawler_instance.archive_feed(self.url)

    def test_archive_feed_rate_limit_no_raise(self):
        self.crawler_instance.raise_on_limit = False
        with patch('skills.smart_secure_rss_crawler.RateLimiter.acquire', side_effect=RateLimitExceeded("Limit")):
            result = self.crawler_instance.archive_feed(self.url)
            self.assertFalse(result)

    def test_archive_feed_generic_exception(self):
        self.crawler_instance.raise_on_limit = True
        with patch('skills.smart_secure_rss_crawler.SmartCrawler.coordinate_expansion', side_effect=Exception("Crash")):
            with self.assertRaises(SmartSecureRSSCrawlerError):
                self.crawler_instance.archive_feed(self.url)

    def test_get_archived_feed(self):
        with patch('skills.smart_secure_rss_crawler.SecureCleanCompressedRSSArchiver.get_archived_feed') as mock_get:
            mock_get.return_value = "<rss>cached</rss>"
            
            feed = self.crawler_instance.get_archived_feed(self.url)
            
            self.assertEqual(feed, "<rss>cached</rss>")
            mock_get.assert_called_once_with(self.url)

    def test_coordinate_expansion_delegation(self):
        with patch('skills.smart_secure_rss_crawler.SmartCrawler.coordinate_expansion') as mock_coord:
            mock_coord.return_value = "expanded"
            
            res = self.crawler_instance.coordinate_expansion(self.url)
            
            self.assertEqual(res, "expanded")
            mock_coord.assert_called_once_with(self.url)

if __name__ == '__main__':
    unittest.main()