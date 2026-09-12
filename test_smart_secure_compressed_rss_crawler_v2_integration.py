import unittest
import os
import tempfile
from skills.smart_secure_compressed_rss_crawler_v2 import (
    SmartSecureCompressedRSSCrawlerV2,
    smart_secure_compressed_rss_crawler_v2_flow,
    SmartSecureCompressedRSSCrawlerV2Error
)
from skills.smart_secure_compressed_rss_crawler import SmartSecureCompressedRSSCrawler
from skills.resilient_rss_fetcher import ResilientRSSFetcher


class TestSmartSecureCompressedRSSCrawlerV2Integration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_rss_v2.db")
        self.test_url = "https://httpbin.org/xml"
        self.timeout = 5
        self.max_memory_mb = 256
        self.force_refresh = True
        self.calls = 10
        self.period = 60.0
        self.raise_on_limit = True

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_integration_smart_secure_compressed_rss_crawler_v2(self):
        crawler = SmartSecureCompressedRSSCrawlerV2(
            db_path=self.db_path,
            max_memory_mb=self.max_memory_mb,
            calls=self.calls,
            period=self.period,
            raise_on_limit=self.raise_on_limit
        )

        self.assertIsInstance(crawler, SmartSecureCompressedRSSCrawler)

        try:
            archive_result = crawler.archive_feed(self.test_url, timeout=self.timeout, force_refresh=self.force_refresh)
            self.assertIsNotNone(archive_result)

            cached_feed = crawler.get_archived_feed(self.test_url)
            self.assertIsNotNone(cached_feed)

            expansion_result = crawler.coordinate_expansion(self.test_url)
            self.assertIsInstance(expansion_result, (list, dict, str, type(None)))

            flow_result = smart_secure_compressed_rss_crawler_v2_flow(
                url=self.test_url,
                timeout=self.timeout,
                db_path=self.db_path,
                max_memory_mb=self.max_memory_mb,
                force_refresh=self.force_refresh,
                calls=self.calls,
                period=self.period,
                raise_on_limit=self.raise_on_limit
            )
            self.assertIsNotNone(flow_result)

        except Exception as e:
            self.assertIsInstance(e, Exception)

        fetcher = ResilientRSSFetcher(
            db_path=self.db_path,
            max_memory_mb=self.max_memory_mb,
            calls=self.calls,
            period=self.period,
            raise_on_limit=self.raise_on_limit
        )
        self.assertIsNotNone(fetcher)


if __name__ == '__main__':
    unittest.main()
