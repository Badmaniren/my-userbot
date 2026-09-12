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
        mock_crawler = MagicMock()
        mock_crawler.process_url.return_value = True

        mock_sitemap = MagicMock()
        mock_sitemap.crawl_and_clean.return_value = ["http://example.com/data"]

        mock_storage = MagicMock()
        mock_storage.save_compressed_data.return_value = None

        aggregator = ResilientSmartUrlAggregatorV2(
            crawler=mock_crawler,
            sitemap_crawler=mock_sitemap,
            storage=mock_storage
        )

        result = aggregator.aggregate("http://target.url", timeout=10)
        self.assertTrue(result)
        mock_crawler.process_url.assert_called_once_with("http://target.url", timeout=10)
        mock_sitemap.crawl_and_clean.assert_called_once_with("http://target.url", timeout=10)
        mock_storage.save_compressed_data.assert_called_once()

    def test_aggregate_flow_crawler_failure(self):
        mock_crawler = MagicMock()
        mock_crawler.process_url.return_value = False

        aggregator = ResilientSmartUrlAggregatorV2(crawler=mock_crawler)
        result = aggregator.aggregate("http://bad.url", timeout=5)
        self.assertFalse(result)

    def test_storage_exception_handling(self):
        mock_storage = MagicMock()
        mock_storage.save_compressed_data.side_effect = Exception("DB Error")

        aggregator = ResilientSmartUrlAggregatorV2(storage=mock_storage)
        with self.assertRaises(Exception):
            aggregator.save_to_storage("key", "data")

    def test_sitemap_validation_logic(self):
        mock_sitemap = MagicMock()
        mock_sitemap.validate_sitemap.return_value = True

        aggregator = ResilientSmartUrlAggregatorV2(sitemap_crawler=mock_sitemap)
        res = aggregator.validate_source("http://sitemap.xml", 5)
        self.assertTrue(res)

        mock_sitemap.validate_sitemap.return_value = False
        res = aggregator.validate_source("http://invalid.xml", 5)
        self.assertFalse(res)

    def test_memory_limit_handling(self):
        with patch('skills.resilient_smart_url_aggregator_v2.memory_profiler.assert_memory_limit') as MockAssert:
            MockAssert.side_effect = Exception("MemoryLimitExceeded")

            with self.assertRaises(Exception):
                self.aggregator.check_resources()

    def test_compressed_data_retrieval(self):
        mock_storage = MagicMock()
        mock_storage.get_compressed_data.return_value = b'compressed_payload'

        aggregator = ResilientSmartUrlAggregatorV2(storage=mock_storage)
        data = aggregator.get_data("test_key")
        self.assertEqual(data, b'compressed_payload')

    def test_integration_with_mocked_io(self):
        with patch('skills.resilient_smart_url_aggregator_v2.requests.get') as mock_get:
            mock_get.return_value.content = io.BytesIO(b'<html></html>').read()
            mock_get.return_value.status_code = 200

            res = self.aggregator.process_raw_content("http://example.com")
            self.assertTrue(res)

if __name__ == '__main__':
    unittest.main()
