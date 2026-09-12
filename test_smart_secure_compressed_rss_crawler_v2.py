import unittest
from unittest.mock import patch, MagicMock
import io
from skills.smart_secure_compressed_rss_crawler_v2 import (
    SmartSecureCompressedRSSCrawlerV2,
    SmartSecureCompressedRSSCrawlerV2Error,
    smart_secure_compressed_rss_crawler_v2_flow
)


class TestSmartSecureCompressedRSSCrawlerV2(unittest.TestCase):

    def setUp(self):
        self.db_path = ":memory:"
        self.url = "https://example.com/rss"

    def test_crawler_v2_initialization(self):
        crawler = SmartSecureCompressedRSSCrawlerV2(
            db_path=self.db_path,
            max_memory_mb=64,
            calls=10,
            period=30,
            raise_on_limit=False
        )
        self.assertEqual(crawler.db_path, self.db_path)
        self.assertIsNotNone(crawler.resilient_fetcher)

    def test_archive_feed_success(self):
        crawler = SmartSecureCompressedRSSCrawlerV2(db_path=self.db_path)
        with patch('skills.smart_secure_compressed_rss_crawler.SmartSecureCompressedRSSCrawler.archive_feed', return_value=True) as mock_archive:
            result = crawler.archive_feed(self.url, timeout=5, force_refresh=True)
            self.assertTrue(result)
            mock_archive.assert_called_once_with(self.url, timeout=5, force_refresh=True)

    def test_archive_feed_failure(self):
        crawler = SmartSecureCompressedRSSCrawlerV2(db_path=self.db_path)
        with patch('skills.smart_secure_compressed_rss_crawler.SmartSecureCompressedRSSCrawler.archive_feed', return_value=False) as mock_archive:
            result = crawler.archive_feed(self.url)
            self.assertFalse(result)
            mock_archive.assert_called_once_with(self.url, timeout=10, force_refresh=False)

    def test_flow_success(self):
        with patch('skills.smart_secure_compressed_rss_crawler_v2.SmartSecureCompressedRSSCrawlerV2.archive_feed', return_value=True) as mock_archive:
            result = smart_secure_compressed_rss_crawler_v2_flow(
                url=self.url,
                timeout=5,
                db_path=self.db_path,
                max_memory_mb=128,
                force_refresh=False,
                calls=5,
                period=60,
                raise_on_limit=True
            )
            self.assertTrue(result)
            mock_archive.assert_called_once_with(self.url, timeout=5, force_refresh=False)

    def test_flow_exception(self):
        with patch('skills.smart_secure_compressed_rss_crawler_v2.SmartSecureCompressedRSSCrawlerV2.archive_feed', side_effect=Exception("Database error")):
            with self.assertRaises(Exception):
                smart_secure_compressed_rss_crawler_v2_flow(url=self.url)


if __name__ == '__main__':
    unittest.main()
