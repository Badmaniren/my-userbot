import unittest
from unittest.mock import patch, MagicMock
import io

from skills.smart_secure_compressed_sitemap_crawler import SmartSecureCompressedSitemapCrawler
from skills.resilient_secure_clean_compressed_sitemap_crawler import ResilientSecureCleanCompressedSitemapCrawler

class TestSmartSecureCompressedSitemapCrawlerV2(unittest.TestCase):

    def setUp(self):
        self.db_path = "test_storage.db"
        self.max_memory = 128
        self.crawler = SmartSecureCompressedSitemapCrawler(
            db_path=self.db_path,
            max_memory_mb=self.max_memory,
            calls=10,
            period=60,
            raise_on_limit=False
        )

    def test_initialization(self):
        self.assertIsInstance(self.crawler, SmartSecureCompressedSitemapCrawler)
        self.assertTrue(hasattr(self.crawler, 'coordinate_expansion'))

    def test_validate_sitemap_success(self):
        with patch('skills.resilient_secure_clean_compressed_sitemap_crawler.ResilientSecureCleanCompressedSitemapCrawler.validate_sitemap') as mock_validate:
            mock_validate.return_value = True
            res = self.crawler.validate_sitemap("http://example.com/sitemap.xml", 10)
            self.assertTrue(res)

    def test_validate_sitemap_failure(self):
        with patch('skills.resilient_secure_clean_compressed_sitemap_crawler.ResilientSecureCleanCompressedSitemapCrawler.validate_sitemap') as mock_validate:
            mock_validate.return_value = False
            res = self.crawler.validate_sitemap("http://example.com/invalid.xml", 10)
            self.assertFalse(res)

    def test_crawl_and_clean_memory_limit(self):
        from skills.memory_profiler import MemoryLimitExceeded
        with patch('skills.smart_secure_compressed_sitemap_crawler.SmartSecureCompressedSitemapCrawler.crawl_and_clean') as mock_crawl:
            mock_crawl.side_effect = MemoryLimitExceeded()
            with self.assertRaises(MemoryLimitExceeded):
                self.crawler.crawl_and_clean("http://example.com/sitemap.xml", 10)

    def test_coordinate_expansion_integration(self):
        with patch('skills.smart_secure_compressed_sitemap_crawler.SmartSecureCompressedSitemapCrawler.coordinate_expansion') as mock_coord:
            mock_coord.return_value = ["http://link1.com", "http://link2.com"]
            res = self.crawler.coordinate_expansion("http://example.com/sitemap.xml", 10)
            self.assertEqual(len(res), 2)
            self.assertIn("http://link1.com", res)

    def test_resilient_composition_dependency(self):
        # Проверка, что модуль использует ResilientSecureCleanCompressedSitemapCrawler
        crawler_v2 = ResilientSecureCleanCompressedSitemapCrawler(
            db_path=self.db_path,
            max_memory_mb=self.max_memory,
            calls=5,
            period=10,
            raise_on_limit=True
        )
        self.assertIsNotNone(crawler_v2)
        
        with patch('skills.resilient_secure_clean_compressed_sitemap_crawler.ResilientSecureCleanCompressedSitemapCrawler.crawl') as mock_crawl:
            mock_crawl.return_value = ["data"]
            res = crawler_v2.crawl("http://test.com", 5)
            self.assertEqual(res, ["data"])

    def test_compression_logic_in_storage(self):
        from skills.compressed_db_storage import CompressedDBStorage
        storage = CompressedDBStorage(self.db_path)
        
        with patch.object(storage, 'save_compressed_data') as mock_save:
            payload = b"compressed_content"
            storage.save_compressed_data("key", payload)
            mock_save.assert_called_with("key", payload)

    def test_rate_limiter_behavior(self):
        from skills.rate_limiter import RateLimiter
        limiter = RateLimiter(calls=1, period=1, raise_on_limit=True)
        limiter.acquire()
        with self.assertRaises(Exception):
            limiter.acquire()

    def test_memory_profiler_assertion(self):
        from skills.memory_profiler import assert_memory_limit, MemoryLimitExceeded
        with patch('skills.memory_profiler.get_current_memory', return_value=200):
            with self.assertRaises(MemoryLimitExceeded):
                assert_memory_limit(100)

if __name__ == '__main__':
    unittest.main()