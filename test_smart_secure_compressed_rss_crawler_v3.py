import unittest
from unittest.mock import patch, MagicMock
import io

from skills.smart_secure_compressed_rss_crawler_v3 import (
    SmartSecureCompressedRSSCrawlerV3,
    smart_secure_compressed_rss_crawler_v3_flow
)


class TestSmartSecureCompressedRSSCrawlerV3(unittest.TestCase):

    def setUp(self):
        self.db_path = ":memory:"
        self.max_memory_mb = 512
        self.calls = 10
        self.period = 1.0
        self.raise_on_limit = True
        self.url = "https://example.com/rss.xml"
        self.timeout = 5

        self.crawler = SmartSecureCompressedRSSCrawlerV3(
            db_path=self.db_path,
            max_memory_mb=self.max_memory_mb,
            calls=self.calls,
            period=self.period,
            raise_on_limit=self.raise_on_limit
        )

    def test_init(self):
        self.assertIsNotNone(self.crawler)
        self.assertEqual(self.crawler.max_memory_mb, self.max_memory_mb)

    def test_archive_feed_success(self):
        with patch('skills.smart_secure_compressed_rss_crawler.SmartSecureCompressedRSSCrawler.archive_feed') as mock_archive:
            mock_archive.return_value = True
            result = self.crawler.archive_feed(self.url, self.timeout, force_refresh=False)
            self.assertTrue(result)

    def test_archive_feed_failure(self):
        with patch('skills.smart_secure_compressed_rss_crawler.SmartSecureCompressedRSSCrawler.archive_feed') as mock_archive:
            mock_archive.return_value = False
            result = self.crawler.archive_feed(self.url, self.timeout, force_refresh=True)
            self.assertFalse(result)

    def test_get_archived_feed(self):
        expected_data = "<rss>cached feed</rss>"
        with patch('skills.smart_secure_compressed_rss_crawler.SmartSecureCompressedRSSCrawler.get_archived_feed') as mock_get:
            mock_get.return_value = expected_data
            result = self.crawler.get_archived_feed(self.url)
            self.assertEqual(result, expected_data)

    def test_coordinate_expansion(self):
        expected_expansion = ["https://example.com/item1", "https://example.com/item2"]
        with patch('skills.smart_secure_compressed_rss_crawler.SmartSecureCompressedRSSCrawler.coordinate_expansion') as mock_coord:
            mock_coord.return_value = expected_expansion
            result = self.crawler.coordinate_expansion(self.url)
            self.assertEqual(result, expected_expansion)

    def test_memory_profiler_integration(self):
        with patch('skills.memory_profiler.assert_memory_limit') as mock_memory:
            mock_memory.return_value = None
            with patch('skills.smart_secure_compressed_rss_crawler.SmartSecureCompressedRSSCrawler.archive_feed') as mock_archive:
                mock_archive.return_value = True
                result = self.crawler.archive_feed(self.url, self.timeout)
                self.assertTrue(result)
                mock_memory.assert_called_once_with(self.max_memory_mb)

    def test_flow_function(self):
        with patch('skills.smart_secure_compressed_rss_crawler.smart_secure_compressed_rss_crawler_flow') as mock_flow:
            mock_flow.return_value = True
            result = smart_secure_compressed_rss_crawler_v3_flow(
                url=self.url,
                timeout=self.timeout,
                db_path=self.db_path,
                max_memory_mb=self.max_memory_mb,
                force_refresh=False,
                calls=self.calls,
                period=self.period,
                raise_on_limit=self.raise_on_limit
            )
            self.assertTrue(result)

    def test_archive_feed_error_raise_on_limit_true(self):
        from skills.smart_secure_compressed_rss_crawler_v3 import SmartSecureCompressedRSSCrawlerV3Error
        with patch('skills.smart_secure_compressed_rss_crawler.SmartSecureCompressedRSSCrawler.archive_feed') as mock_archive:
            mock_archive.side_effect = Exception("Archive failed")
            with self.assertRaises(SmartSecureCompressedRSSCrawlerV3Error):
                self.crawler.archive_feed(self.url, self.timeout)

    def test_archive_feed_error_raise_on_limit_false(self):
        crawler = SmartSecureCompressedRSSCrawlerV3(
            db_path=self.db_path,
            max_memory_mb=self.max_memory_mb,
            calls=self.calls,
            period=self.period,
            raise_on_limit=False
        )
        with patch('skills.smart_secure_compressed_rss_crawler.SmartSecureCompressedRSSCrawler.archive_feed') as mock_archive:
            mock_archive.side_effect = Exception("Archive failed")
            result = crawler.archive_feed(self.url, self.timeout)
            self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()