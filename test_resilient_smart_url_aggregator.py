import unittest
from unittest.mock import patch, MagicMock
import io
from skills.resilient_smart_url_aggregator import ResilientSmartUrlAggregator

class TestResilientSmartUrlAggregator(unittest.TestCase):

    def setUp(self):
        self.db_path = "test_storage.db"
        self.aggregator = ResilientSmartUrlAggregator(db_path=self.db_path)

    def test_aggregate_expansion_success(self):
        url = "https://example.com"
        timeout = 10

        with patch.object(self.aggregator.url_crawler, 'process_url', return_value=True) as mock_process, \
             patch.object(self.aggregator.sitemap_crawler, 'coordinate_expansion', return_value=["https://example.com/page1"]) as mock_coord:

            result = self.aggregator.aggregate_expansion(url, timeout)

            self.assertTrue(result)
            mock_process.assert_called_once_with(url, timeout)
            mock_coord.assert_called_once_with(url, timeout)

    def test_aggregate_expansion_crawler_failure(self):
        url = "https://bad-url.com"

        with patch.object(self.aggregator.url_crawler, 'process_url', return_value=False):
            result = self.aggregator.aggregate_expansion(url, 5)
            self.assertFalse(result)

    def test_memory_safety_enforcement(self):
        url = "https://example.com"

        with patch('skills.resilient_smart_url_aggregator.memory_profiler.assert_memory_limit') as mock_mem:
            mock_mem.side_effect = RuntimeError("MemoryLimitExceeded")

            with self.assertRaises(RuntimeError):
                self.aggregator.aggregate_expansion(url, 5)

    def test_rate_limiting_handling(self):
        url = "https://example.com"

        with patch.object(self.aggregator.url_crawler, 'process_url', side_effect=Exception("RateLimitExceeded")):
            result = self.aggregator.aggregate_expansion(url, 5)
            self.assertFalse(result)

    def test_sitemap_validation_integration(self):
        url = "https://example.com/sitemap.xml"

        with patch.object(self.aggregator.sitemap_crawler, 'validate_sitemap', return_value=True) as mock_val:
            res = self.aggregator.validate_target(url, 5)
            self.assertTrue(res)
            mock_val.assert_called_once_with(url, 5)

    def test_invalid_url_handling(self):
        url = "not-a-url"

        with patch.object(self.aggregator.url_crawler, 'process_url', return_value=False):
            result = self.aggregator.aggregate_expansion(url, 5)
            self.assertFalse(result)

    def test_resource_cleanup_on_failure(self):
        url = "https://example.com"

        with patch('skills.resilient_smart_url_aggregator.memory_profiler.force_gc') as mock_gc:
            with patch.object(self.aggregator.url_crawler, 'process_url', side_effect=ValueError("Crash")):
                self.aggregator.aggregate_expansion(url, 5)
                mock_gc.assert_called()