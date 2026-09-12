import unittest
from unittest.mock import patch, MagicMock
import io

from skills.resilient_secure_smart_crawler_hub import ResilientSecureSmartCrawlerHub
from skills.smart_secure_compressed_sitemap_crawler_v2 import SmartSecureCompressedSitemapCrawlerV2Error
from skills.resilient_secure_clean_url_crawler_v2 import ResilientSecureCleanUrlCrawlerV2Error
from skills.compressed_db_storage import CompressedDBStorage

class TestResilientSecureSmartCrawlerHub(unittest.TestCase):

    def setUp(self):
        self.db_path = "test_hub.db"
        self.hub = ResilientSecureSmartCrawlerHub(
            db_path=self.db_path,
            max_memory_mb=128,
            calls=10,
            period=60
        )

    def test_initialization(self):
        self.assertIsInstance(self.hub.sitemap_crawler, object)
        self.assertIsInstance(self.hub.url_crawler, object)
        self.assertIsInstance(self.hub.storage, CompressedDBStorage)

    def test_crawl_sitemap_success(self):
        with patch('skills.smart_secure_compressed_sitemap_crawler_v2.SmartSecureCompressedSitemapCrawlerV2.crawl_and_clean') as mock_crawl:
            mock_crawl.return_value = ["http://example.com/1", "http://example.com/2"]

            result = self.hub.crawl_sitemap("http://example.com/sitemap.xml", timeout=10)

            self.assertTrue(len(result) > 0)
            mock_crawl.assert_called_once()

    def test_crawl_sitemap_failure(self):
        with patch('skills.smart_secure_compressed_sitemap_crawler_v2.SmartSecureCompressedSitemapCrawlerV2.crawl_and_clean') as mock_crawl:
            mock_crawl.side_effect = SmartSecureCompressedSitemapCrawlerV2Error("Failed")

            with self.assertRaises(SmartSecureCompressedSitemapCrawlerV2Error):
                self.hub.crawl_sitemap("http://bad-url.com", timeout=5)

    def test_process_url_securely(self):
        with patch('skills.resilient_secure_clean_url_crawler_v2.ResilientSecureCleanUrlCrawlerV2.process_url') as mock_proc:
            mock_proc.return_value = True

            res = self.hub.process_url_securely("http://example.com/page", timeout=5)
            self.assertTrue(res)
            mock_proc.assert_called_once_with("http://example.com/page", 5)

    def test_process_url_invalid(self):
        with patch('skills.resilient_secure_clean_url_crawler_v2.ResilientSecureCleanUrlCrawlerV2.process_url') as mock_proc:
            mock_proc.side_effect = ResilientSecureCleanUrlCrawlerV2Error("Invalid")

            res = self.hub.process_url_securely("http://invalid.com", timeout=5)
            self.assertFalse(res)

    def test_storage_integration(self):
        test_key = "test_key"
        test_data = b"compressed_payload_data"

        with patch('skills.compressed_db_storage.CompressedDBStorage.save_compressed_data') as mock_save:
            self.hub.storage.save_compressed_data(test_key, test_data)
            mock_save.assert_called_once_with(test_key, test_data)

    def test_memory_aware_execution(self):
        with patch('skills.memory_profiler.assert_memory_limit') as mock_mem, \
             patch('skills.smart_secure_compressed_sitemap_crawler_v2.SmartSecureCompressedSitemapCrawlerV2.crawl_and_clean'):
            # Проверка, что хаб вызывает проверку памяти перед тяжелыми операциями
            self.hub.crawl_sitemap("http://example.com/sitemap.xml", timeout=10)
            mock_mem.assert_called()

    def test_rate_limited_execution(self):
        with patch.object(self.hub.rate_limiter, 'acquire') as mock_acquire:
            self.hub.process_url_securely("http://example.com", timeout=5)
            mock_acquire.assert_called_once()

    def test_compressed_storage_retrieval(self):
        with patch('skills.compressed_db_storage.CompressedDBStorage.get_compressed_data') as mock_get:
            mock_get.return_value = b"data"

            res = self.hub.storage.get_compressed_data("key")
            self.assertEqual(res, b"data")
            self.assertTrue(isinstance(res, bytes))

if __name__ == '__main__':
    unittest.main()
