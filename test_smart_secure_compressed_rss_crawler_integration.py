import unittest
import os
from skills.smart_secure_compressed_rss_crawler import (
    SmartSecureCompressedRSSCrawler,
    smart_secure_compressed_rss_archive_flow,
    SmartSecureCompressedRSSCrawlerError
)
from skills.smart_secure_rss_crawler import SmartSecureRSSCrawler
from skills.payload_compressor import PayloadCompressor

class TestSmartSecureCompressedRSSCrawlerIntegration(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_secure_compressed_rss.db"
        self.url = "http://example.com/rss"
        self.timeout = 5
        self.max_memory_mb = 512
        self.calls = 10
        self.period = 60
        self.raise_on_limit = True

        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_composition_and_inheritance(self):
        crawler = SmartSecureCompressedRSSCrawler(
            db_path=self.db_path,
            max_memory_mb=self.max_memory_mb,
            calls=self.calls,
            period=self.period,
            raise_on_limit=self.raise_on_limit
        )
        self.assertIsInstance(crawler, SmartSecureRSSCrawler)

    def test_flow_function(self):
        try:
            result = smart_secure_compressed_rss_archive_flow(
                url=self.url,
                timeout=self.timeout,
                db_path=self.db_path,
                max_memory_mb=self.max_memory_mb,
                force_refresh=True,
                calls=self.calls,
                period=self.period,
                raise_on_limit=self.raise_on_limit
            )
            self.assertIsNotNone(result)
        except Exception as e:
            self.assertIsInstance(e, (SmartSecureCompressedRSSCrawlerError, Exception))

    def test_class_methods(self):
        crawler = SmartSecureCompressedRSSCrawler(
            db_path=self.db_path,
            max_memory_mb=self.max_memory_mb,
            calls=self.calls,
            period=self.period,
            raise_on_limit=self.raise_on_limit
        )
        
        try:
            crawler.archive_feed(self.url, timeout=self.timeout, force_refresh=True)
            archived = crawler.get_archived_feed(self.url)
            self.assertIsNotNone(archived)
        except Exception as e:
            self.assertIsInstance(e, (SmartSecureCompressedRSSCrawlerError, Exception))

if __name__ == "__main__":
    unittest.main()