import unittest
from unittest.mock import patch, MagicMock
import io

from skills.resilient_secure_smart_crawler_hub_analytics_exporter import (
    ResilientSecureSmartCrawlerHubAnalyticsExporter,
    ResilientSecureSmartCrawlerHubAnalyticsExporterError
)


class TestResilientSecureSmartCrawlerHubAnalyticsExporter(unittest.TestCase):

    def setUp(self):
        self.db_path = ":memory:"
        self.max_memory_mb = 128
        self.calls = 10
        self.period = 1.0
        self.raise_on_limit = False
        self.exporter = ResilientSecureSmartCrawlerHubAnalyticsExporter(
            db_path=self.db_path,
            max_memory_mb=self.max_memory_mb,
            calls=self.calls,
            period=self.period,
            raise_on_limit=self.raise_on_limit
        )

    def test_init_and_composition(self):
        self.assertIsNotNone(self.exporter)
        self.assertIsNotNone(self.exporter.analytics_v2)
        self.assertIsNotNone(self.exporter.storage)

    def test_validate_target_headers_success(self):
        url = "https://example.com"
        timeout = 5
        with patch('skills.resilient_secure_smart_crawler_hub_analytics_v2.ResilientSecureSmartCrawlerHubAnalyticsV2.validate_target_headers', return_value=True) as mock_val:
            res = self.exporter.validate_target_headers(url, timeout)
            self.assertTrue(res)
            mock_val.assert_called_once_with(url, timeout)

    def test_validate_target_headers_failure(self):
        url = "https://example.com"
        timeout = 5
        with patch('skills.resilient_secure_smart_crawler_hub_analytics_v2.ResilientSecureSmartCrawlerHubAnalyticsV2.validate_target_headers', return_value=False) as mock_val:
            res = self.exporter.validate_target_headers(url, timeout)
            self.assertFalse(res)
            mock_val.assert_called_once_with(url, timeout)

    def test_coordinate_expansion_safe_success(self):
        url = "https://example.com"
        timeout = 5
        with patch('skills.resilient_secure_smart_crawler_hub_analytics_v2.ResilientSecureSmartCrawlerHubAnalyticsV2.coordinate_expansion_safe', return_value=True) as mock_coord:
            res = self.exporter.coordinate_expansion_safe(url, timeout)
            self.assertTrue(res)
            mock_coord.assert_called_once_with(url, timeout)

    def test_coordinate_expansion_safe_failure(self):
        url = "https://example.com"
        timeout = 5
        with patch('skills.resilient_secure_smart_crawler_hub_analytics_v2.ResilientSecureSmartCrawlerHubAnalyticsV2.coordinate_expansion_safe', return_value=False) as mock_coord:
            res = self.exporter.coordinate_expansion_safe(url, timeout)
            self.assertFalse(res)
            mock_coord.assert_called_once_with(url, timeout)

    def test_export_analytics_report(self):
        url = "https://example.com/report"
        raw_payload = "sample analytics data"
        cleaned_url = "https://example.com/report"
        
        with patch('skills.clean_compressed_db_storage.CleanCompressedDBStorage.clean_target_url', return_value=cleaned_url) as mock_clean_url, \
             patch('skills.clean_compressed_db_storage.CleanCompressedDBStorage.save_cleaned_and_compressed_data') as mock_save:
            
            self.exporter.export_analytics_report(url, raw_payload)
            mock_clean_url.assert_called_once_with(url)
            mock_save.assert_called_once()

    def test_get_exported_report(self):
        url = "https://example.com/report"
        cleaned_url = "https://example.com/report"
        expected_payload = "decompressed payload"

        with patch('skills.clean_compressed_db_storage.CleanCompressedDBStorage.clean_target_url', return_value=cleaned_url) as mock_clean_url, \
             patch('skills.clean_compressed_db_storage.CleanCompressedDBStorage.get_cleaned_and_compressed_data', return_value=expected_payload) as mock_get:
            
            res = self.exporter.get_exported_report(url)
            self.assertEqual(res, expected_payload)
            mock_clean_url.assert_called_once_with(url)
            mock_get.assert_called_once_with(cleaned_url)

    def test_export_analytics_report_exception_handling(self):
        url = "https://example.com/report"
        raw_payload = "bad data"

        with patch('skills.clean_compressed_db_storage.CleanCompressedDBStorage.clean_target_url', side_effect=Exception("Storage error")):
            with self.assertRaises(ResilientSecureSmartCrawlerHubAnalyticsExporterError):
                self.exporter.export_analytics_report(url, raw_payload)


if __name__ == '__main__':
    unittest.main()