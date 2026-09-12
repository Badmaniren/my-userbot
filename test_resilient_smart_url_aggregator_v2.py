import unittest
from unittest.mock import patch, MagicMock
import io

from skills.resilient_smart_url_aggregator_v2 import ResilientSmartUrlAggregatorV2

class TestResilientSmartUrlAggregatorV2(unittest.TestCase):

    def setUp(self):
        self.db_path = "test_storage.db"
        self.aggregator = ResilientSmartUrlAggregatorV2(db_path=self.db_path)

    def test_initialization(self):
        self.assertIsNotNone(self.aggregator)
        self.assertEqual(self.aggregator.db_path, self.db_path)

    def test_aggregate_flow_success(self):
        with patch('skills.resilient_smart_url_aggregator_v2.resilient_secure_clean_url_crawler_v2.ResilientSecureCleanUrlCrawlerV2') as MockCrawler, \
             patch('skills.resilient_smart_url_aggregator_v2.smart_secure_compressed_sitemap_crawler_v2.SmartSecureCompressedSitemapCrawlerV2') as MockSitemap, \
             patch('skills.resilient_smart_url_aggregator_v2.compressed_db_storage.CompressedDBStorage') as MockStorage:

            instance_crawler = MockCrawler.return_value
            instance_crawler.process_url.return_value = True

            instance_sitemap = MockSitemap.return_value
            instance_sitemap.crawl_and_clean.return_value = ["http://example.com/data"]

            instance_storage = MockStorage.return_value
            instance_storage.save_compressed_data.return_value = None

            aggregator = ResilientSmartUrlAggregatorV2(db_path=self.db_path)
            result = aggregator.aggregate("http://target.url", timeout=10)
            self.assertTrue(result)

    def test_aggregate_flow_crawler_failure(self):
        with patch('skills.resilient_smart_url_aggregator_v2.resilient_secure_clean_url_crawler_v2.ResilientSecureCleanUrlCrawlerV2') as MockCrawler:
            instance = MockCrawler.return_value
            instance.process_url.return_value = False

            aggregator = ResilientSmartUrlAggregatorV2(db_path=self.db_path)
            result = aggregator.aggregate("http://bad.url", timeout=5)
            self.assertFalse(result)

    def test_storage_exception_handling(self):
        with patch('skills.resilient_smart_url_aggregator_v2.compressed_db_storage.CompressedDBStorage') as MockStorage:
            instance = MockStorage.return_value
            instance.save_compressed_data.side_effect = Exception("DB Error")

            aggregator = ResilientSmartUrlAggregatorV2(db_path=self.db_path)
            with self.assertRaises(Exception):
                aggregator.save_to_storage("key", "data")

    def test_sitemap_validation_logic(self):
        with patch('skills.resilient_smart_url_aggregator_v2.smart_secure_compressed_sitemap_crawler_v2.SmartSecureCompressedSitemapCrawlerV2') as MockSitemap:
            instance = MockSitemap.return_value
            instance.validate_sitemap.return_value = True

            aggregator = ResilientSmartUrlAggregatorV2(db_path=self.db_path)
            res = aggregator.validate_source("http://sitemap.xml", 5)
            self.assertTrue(res)

            instance.validate_sitemap.return_value = False
            res = aggregator.validate_source("http://invalid.xml", 5)
            self.assertFalse(res)

    def test_memory_limit_handling(self):
        with patch('skills.resilient_smart_url_aggregator_v2.memory_profiler.assert_memory_limit') as MockAssert:
            MockAssert.side_effect = Exception("MemoryLimitExceeded")

            with self.assertRaises(Exception):
                self.aggregator.check_resources()

    def test_compressed_data_retrieval(self):
        with patch('skills.resilient_smart_url_aggregator_v2.compressed_db_storage.CompressedDBStorage') as MockStorage:
            instance = MockStorage.return_value
            instance.get_compressed_data.return_value = b'compressed_payload'

            aggregator = ResilientSmartUrlAggregatorV2(db_path=self.db_path)
            data = aggregator.get_data("test_key")
            self.assertEqual(data, b'compressed_payload')

    def test_integration_with_mocked_io(self):
        with patch('skills.resilient_smart_url_aggregator_v2.requests.get') as mock_get:
            mock_get.return_value.content = io.BytesIO(b'<html></html>').read()
            mock_get.return_value.status_code = 200

            res = self.aggregator.process_raw_content("http://example.com")
            self.assertTrue(res)