import unittest
from unittest.mock import patch, MagicMock
import io

from skills.smart_secure_rss_crawler import (
    SmartSecureRSSCrawler,
    SmartSecureRSSCrawlerError,
    smart_secure_rss_crawler_flow
)

class TestSmartSecureRSSCrawler(unittest.TestCase):
    def setUp(self):
        self.db_path = ":memory:"
        self.max_memory_mb = 128
        self.calls = 5
        self.period = 60
        self.raise_on_limit = True
        self.url = "https://example.com/rss.xml"
        self.timeout = 10

    def test_init_and_attributes(self):
        crawler = SmartSecureRSSCrawler(
            db_path=self.db_path,
            max_memory_mb=self.max_memory_mb,
            calls=self.calls,
            period=self.period,
            raise_on_limit=self.raise_on_limit
        )
        self.assertIsNotNone(crawler)

    def test_archive_feed_success(self):
        crawler = SmartSecureRSSCrawler(
            db_path=self.db_path,
            max_memory_mb=self.max_memory_mb,
            calls=self.calls,
            period=self.period,
            raise_on_limit=self.raise_on_limit
        )
        
        with patch('skills.smart_secure_rss_crawler.SecureCleanCompressedRSSArchiver') as mock_archiver_class, \
             patch('skills.smart_secure_rss_crawler.SmartCrawler') as mock_crawler_class, \
             patch('skills.smart_secure_rss_crawler.RateLimiter') as mock_rate_limiter_class:
            
            mock_archiver_instance = mock_archiver_class.return_value
            mock_archiver_instance.archive_feed.return_value = True
            
            mock_crawler_instance = mock_crawler_class.return_value
            mock_crawler_instance.coordinate_expansion.return_value = True
            
            mock_limiter_instance = mock_rate_limiter_class.return_value
            mock_limiter_instance.acquire.return_value = None

            result = crawler.archive_feed(self.url, self.timeout, force_refresh=False)
            self.assertTrue(result)

    def test_archive_feed_rate_limit_exceeded(self):
        crawler = SmartSecureRSSCrawler(
            db_path=self.db_path,
            max_memory_mb=self.max_memory_mb,
            calls=self.calls,
            period=self.period,
            raise_on_limit=True
        )
        
        with patch('skills.smart_secure_rss_crawler.RateLimiter') as mock_rate_limiter_class:
            mock_limiter_instance = mock_rate_limiter_class.return_value
            from skills.rate_limiter import RateLimitExceeded
            mock_limiter_instance.acquire.side_effect = RateLimitExceeded("Limit exceeded")

            with self.assertRaises(SmartSecureRSSCrawlerError):
                crawler.archive_feed(self.url, self.timeout)

    def test_get_archived_feed(self):
        crawler = SmartSecureRSSCrawler(
            db_path=self.db_path,
            max_memory_mb=self.max_memory_mb
        )
        
        with patch('skills.smart_secure_rss_crawler.SecureCleanCompressedRSSArchiver') as mock_archiver_class:
            mock_archiver_instance = mock_archiver_class.return_value
            mock_archiver_instance.get_archived_feed.return_value = "<rss>cached</rss>"

            feed = crawler.get_archived_feed(self.url)
            self.assertEqual(feed, "<rss>cached</rss>")

    def test_crawler_flow_function(self):
        with patch('skills.smart_secure_rss_crawler.SmartSecureRSSCrawler') as mock_crawler_class:
            mock_instance = mock_crawler_class.return_value
            mock_instance.archive_feed.return_value = True

            res = smart_secure_rss_crawler_flow(
                url=self.url,
                timeout=self.timeout,
                db_path=self.db_path,
                max_memory_mb=self.max_memory_mb,
                force_refresh=True,
                calls=self.calls,
                period=self.period,
                raise_on_limit=self.raise_on_limit
            )
            self.assertTrue(res)

    def test_archive_feed_exception_handling(self):
        crawler = SmartSecureRSSCrawler(
            db_path=self.db_path,
            max_memory_mb=self.max_memory_mb,
            calls=self.calls,
            period=self.period,
            raise_on_limit=False
        )
        
        with patch('skills.smart_secure_rss_crawler.SecureCleanCompressedRSSArchiver') as mock_archiver_class:
            mock_archiver_instance = mock_archiver_class.return_value
            mock_archiver_instance.archive_feed.side_effect = Exception("Critical error")

            result = crawler.archive_feed(self.url, self.timeout)
            self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()