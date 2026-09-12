import unittest
from unittest.mock import patch, MagicMock
import io
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from skills.smart_secure_compressed_rss_crawler import (
    SmartSecureCompressedRSSCrawler,
    SmartSecureCompressedRSSCrawlerError,
    smart_secure_compressed_rss_crawler_flow
)
from skills.smart_secure_rss_crawler import SmartSecureRSSCrawler
from skills.payload_compressor import PayloadCompressor


class TestSmartSecureCompressedRSSCrawler(unittest.TestCase):

    def setUp(self):
        self.db_path = ":memory:"
        self.max_memory_mb = 512
        self.calls = 10
        self.period = 1
        self.raise_on_limit = True
        self.crawler = SmartSecureCompressedRSSCrawler(
            db_path=self.db_path,
            max_memory_mb=self.max_memory_mb,
            calls=self.calls,
            period=self.period,
            raise_on_limit=self.raise_on_limit
        )

    def test_init_composition(self):
        self.assertIsInstance(self.crawler, SmartSecureCompressedRSSCrawler)
        self.assertTrue(hasattr(self.crawler, 'archive_feed'))
        self.assertTrue(hasattr(self.crawler, 'get_archived_feed'))
        self.assertTrue(hasattr(self.crawler, 'coordinate_expansion'))

    def test_archive_feed_success(self):
        test_url = "https://example.com/rss"
        test_timeout = 5
        fake_payload = "<rss><channel><title>Test Feed</title></channel></rss>"

        with patch('skills.smart_secure_rss_crawler.SmartSecureRSSCrawler.archive_feed', return_value=True) as mock_parent_archive, \
             patch('skills.smart_secure_rss_crawler.SmartSecureRSSCrawler.get_archived_feed', return_value=fake_payload) as mock_parent_get, \
             patch('skills.payload_compressor.PayloadCompressor.compress_payload', return_value="compressed_data") as mock_compress:

            res = self.crawler.archive_feed(test_url, timeout=test_timeout, force_refresh=True)
            self.assertTrue(res)
            mock_parent_archive.assert_called_once_with(test_url, timeout=test_timeout, force_refresh=True)
            mock_compress.assert_called_once()

    def test_archive_feed_failure(self):
        test_url = "https://example.com/bad-rss"
        test_timeout = 5

        with patch('skills.smart_secure_rss_crawler.SmartSecureRSSCrawler.archive_feed', side_effect=Exception("Crawler error")):
            with self.assertRaises(SmartSecureCompressedRSSCrawlerError):
                self.crawler.archive_feed(test_url, timeout=test_timeout, force_refresh=False)

    def test_get_archived_feed_success(self):
        test_url = "https://example.com/rss"
        compressed_payload = "compressed_data"
        decompressed_payload = "<rss><channel><title>Test Feed</title></channel></rss>"

        with patch('skills.smart_secure_rss_crawler.SmartSecureRSSCrawler.get_archived_feed', return_value=compressed_payload) as mock_parent_get, \
             patch('skills.payload_compressor.PayloadCompressor.decompress_payload', return_value=decompressed_payload) as mock_decompress:

            res = self.crawler.get_archived_feed(test_url)
            self.assertEqual(res, decompressed_payload)
            mock_parent_get.assert_called_once_with(test_url)
            mock_decompress.assert_called_once_with(compressed_payload)

    def test_get_archived_feed_not_found(self):
        test_url = "https://example.com/missing-rss"

        with patch('skills.smart_secure_rss_crawler.SmartSecureRSSCrawler.get_archived_feed', return_value=None):
            res = self.crawler.get_archived_feed(test_url)
            self.assertIsNone(res)

    def test_coordinate_expansion(self):
        test_url = "https://example.com/rss"

        with patch('skills.smart_secure_rss_crawler.SmartSecureRSSCrawler.coordinate_expansion', return_value=True) as mock_expand:
            res = self.crawler.coordinate_expansion(test_url)
            self.assertTrue(res)
            mock_expand.assert_called_once_with(test_url)

    def test_module_level_flow(self):
        test_url = "https://example.com/rss"
        test_timeout = 5
        fake_payload = "<rss><channel><title>Test Feed</title></channel></rss>"

        with patch('skills.smart_secure_rss_crawler.SmartSecureRSSCrawler.archive_feed', return_value=True), \
             patch('skills.smart_secure_rss_crawler.SmartSecureRSSCrawler.get_archived_feed', return_value=fake_payload), \
             patch('skills.payload_compressor.PayloadCompressor.compress_payload', return_value="compressed"):

            res = smart_secure_compressed_rss_crawler_flow(
                url=test_url,
                timeout=test_timeout,
                db_path=self.db_path,
                max_memory_mb=self.max_memory_mb,
                force_refresh=True,
                calls=self.calls,
                period=self.period,
                raise_on_limit=self.raise_on_limit
            )
            self.assertTrue(res)


if __name__ == '__main__':
    unittest.main()