import unittest
from unittest.mock import patch, MagicMock

from skills.smart_secure_compressed_rss_crawler_v3 import (
    SmartSecureCompressedRSSCrawlerV3,
    SmartSecureCompressedRSSCrawlerV3Error,
    smart_secure_compressed_rss_crawler_v3_flow
)
from skills.smart_secure_compressed_rss_crawler import SmartSecureCompressedRSSCrawler
from skills.resilient_secure_clean_compressed_rss_archiver import ResilientSecureCleanCompressedRSSArchiver
from skills.memory_profiler import MemoryProfiler


class TestSmartSecureCompressedRSSCrawlerV3Integration(unittest.TestCase):
    def setUp(self):
        self.db_path = ":memory:"
        self.max_memory_mb = 512
        self.calls = 10
        self.period = 1.0
        self.raise_on_limit = True
        self.test_url = "https://example.com/rss.xml"
        self.timeout = 5

    def test_composition_and_inheritance(self):
        crawler = SmartSecureCompressedRSSCrawlerV3(
            db_path=self.db_path,
            max_memory_mb=self.max_memory_mb,
            calls=self.calls,
            period=self.period,
            raise_on_limit=self.raise_on_limit
        )
        self.assertIsInstance(crawler, SmartSecureCompressedRSSCrawler)
        self.assertIsInstance(crawler, ResilientSecureCleanCompressedRSSArchiver)
        self.assertIsInstance(crawler, MemoryProfiler)

    @patch('skills.smart_secure_compressed_rss_crawler.smart_secure_compressed_rss_crawler_flow')
    def test_flow_function_execution(self, mock_flow):
        mock_flow.return_value = True
        result = smart_secure_compressed_rss_crawler_v3_flow(
            url=self.test_url,
            timeout=self.timeout,
            db_path=self.db_path,
            max_memory_mb=self.max_memory_mb,
            force_refresh=True,
            calls=self.calls,
            period=self.period,
            raise_on_limit=self.raise_on_limit
        )
        self.assertTrue(result)

    @patch.object(SmartSecureCompressedRSSCrawler, 'archive_feed')
    @patch.object(SmartSecureCompressedRSSCrawler, 'get_archived_feed')
    @patch.object(SmartSecureCompressedRSSCrawler, 'coordinate_expansion')
    def test_crawler_methods(self, mock_coord, mock_get, mock_archive):
        mock_archive.return_value = True
        mock_get.return_value = "<rss></rss>"
        mock_coord.return_value = ["https://example.com/item"]

        crawler = SmartSecureCompressedRSSCrawlerV3(
            db_path=self.db_path,
            max_memory_mb=self.max_memory_mb,
            calls=self.calls,
            period=self.period,
            raise_on_limit=self.raise_on_limit
        )

        arch_res = crawler.archive_feed(self.test_url, self.timeout, force_refresh=True)
        get_res = crawler.get_archived_feed(self.test_url)
        coord_res = crawler.coordinate_expansion(self.test_url)

        self.assertTrue(arch_res)
        self.assertEqual(get_res, "<rss></rss>")
        self.assertEqual(coord_res, ["https://example.com/item"])


if __name__ == "__main__":
    unittest.main()
