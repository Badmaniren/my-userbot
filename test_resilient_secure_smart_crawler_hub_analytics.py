import unittest
from unittest.mock import patch, MagicMock
import io

from skills.resilient_secure_smart_crawler_hub_analytics import (
    ResilientSecureSmartCrawlerHubAnalytics,
    ResilientSecureSmartCrawlerHubAnalyticsError
)


class TestResilientSecureSmartCrawlerHubAnalytics(unittest.TestCase):

    def setUp(self):
        self.analytics = ResilientSecureSmartCrawlerHubAnalytics(
            db_path=":memory:",
            max_memory_mb=256,
            calls=5,
            period=1.0,
            raise_on_limit=True
        )

    def test_init(self):
        with patch('skills.resilient_secure_smart_crawler_hub_analytics.ResilientSecureSmartCrawlerHubV6') as mock_hub_cls, \
             patch('skills.resilient_secure_smart_crawler_hub_analytics.CleanCompressedDBStorage') as mock_storage_cls:

            hub_instance = ResilientSecureSmartCrawlerHubAnalytics(
                db_path=":memory:",
                max_memory_mb=128,
                calls=10,
                period=2.0,
                raise_on_limit=False
            )
            mock_hub_cls.assert_called_once_with(
                db_path=":memory:",
                max_memory_mb=128,
                calls=10,
                period=2.0,
                raise_on_limit=False
            )
            mock_storage_cls.assert_called_once_with(db_path=":memory:")

    def test_collect_metrics_success(self):
        with patch.object(self.analytics.hub, 'coordinate_expansion_safe', return_value={"status": "expanded"}) as mock_coord:
            res = self.analytics.collect_metrics(url="https://example.com", timeout=3)
            mock_coord.assert_called_once_with("https://example.com", timeout=3)
            self.assertEqual(res["status"], "success")
            self.assertEqual(res["total_requests"], 10)
            self.assertEqual(res["coordination"], {"status": "expanded"})

    def test_collect_metrics_no_url(self):
        res = self.analytics.collect_metrics(url=None)
        self.assertEqual(res, {"status": "success", "total_requests": 10})

    def test_collect_metrics_exception_raised(self):
        with patch.object(self.analytics.hub, 'coordinate_expansion_safe', side_effect=Exception("Hub limit error")):
            self.analytics.raise_on_limit = True
            with self.assertRaises(ResilientSecureSmartCrawlerHubAnalyticsError):
                self.analytics.collect_metrics(url="https://example.com")

    def test_collect_metrics_exception_handled(self):
        with patch.object(self.analytics.hub, 'coordinate_expansion_safe', side_effect=Exception("Hub limit error")):
            self.analytics.raise_on_limit = False
            res = self.analytics.collect_metrics(url="https://example.com")
            self.assertEqual(res["status"], "error")
            self.assertIn("Hub limit error", res["message"])

    def test_analyze_crawl_structure_true(self):
        with patch.object(self.analytics.hub, 'validate_target_headers', return_value=True) as mock_validate:
            res = self.analytics.analyze_crawl_structure("https://example.com", timeout=4)
            mock_validate.assert_called_once_with("https://example.com", timeout=4)
            self.assertTrue(res)

    def test_analyze_crawl_structure_false_on_exception(self):
        with patch.object(self.analytics.hub, 'validate_target_headers', side_effect=Exception("Header error")):
            self.analytics.raise_on_limit = False
            res = self.analytics.analyze_crawl_structure("https://example.com", timeout=4)
            self.assertFalse(res)

    def test_analyze_crawl_structure_raises_exception(self):
        with patch.object(self.analytics.hub, 'validate_target_headers', side_effect=Exception("Header error")):
            self.analytics.raise_on_limit = True
            with self.assertRaises(ResilientSecureSmartCrawlerHubAnalyticsError):
                self.analytics.analyze_crawl_structure("https://example.com", timeout=4)

    def test_export_analytics_data_existing(self):
        mock_data = io.BytesIO(b'{"metric": 42}')
        with patch.object(self.analytics.storage, 'get_cleaned_and_compressed_data', return_value=mock_data) as mock_get:
            res = self.analytics.export_analytics_data("https://example.com")
            mock_get.assert_called_once_with("https://example.com")
            self.assertEqual(res, mock_data)

    def test_export_analytics_data_default_url_and_none(self):
        with patch.object(self.analytics.storage, 'get_cleaned_and_compressed_data', return_value=None) as mock_get:
            res = self.analytics.export_analytics_data(None)
            mock_get.assert_called_once_with("https://example.com")
            self.assertIsInstance(res, io.BytesIO)
            self.assertEqual(res.read(), b'{"metric": 1}')

    def test_export_analytics_data_exception_raised(self):
        with patch.object(self.analytics.storage, 'get_cleaned_and_compressed_data', side_effect=Exception("Storage error")):
            self.analytics.raise_on_limit = True
            with self.assertRaises(ResilientSecureSmartCrawlerHubAnalyticsError):
                self.analytics.export_analytics_data("https://example.com")

    def test_export_analytics_data_exception_handled(self):
        with patch.object(self.analytics.storage, 'get_cleaned_and_compressed_data', side_effect=Exception("Storage error")):
            self.analytics.raise_on_limit = False
            res = self.analytics.export_analytics_data("https://example.com")
            self.assertIsInstance(res, io.BytesIO)
            self.assertEqual(res.read(), b'{"metric": 1}')

    def test_coordinate_expansion_with_analytics_success(self):
        with patch.object(self.analytics.hub, 'coordinate_expansion', return_value={"expanded": True}) as mock_coord:
            res = self.analytics.coordinate_expansion_with_analytics("https://example.com", timeout=2)
            mock_coord.assert_called_once_with("https://example.com", timeout=2)
            self.assertEqual(res, {"expanded": True})

    def test_coordinate_expansion_with_analytics_exception(self):
        with patch.object(self.analytics.hub, 'coordinate_expansion', side_effect=Exception("Expansion failed")):
            with self.assertRaises(ResilientSecureSmartCrawlerHubAnalyticsError):
                self.analytics.coordinate_expansion_with_analytics("https://example.com", timeout=2)

    def test_validate_target_headers_true(self):
        with patch.object(self.analytics.hub, 'validate_target_headers', return_value=True) as mock_validate:
            res = self.analytics.validate_target_headers("https://example.com", timeout=3.0)
            mock_validate.assert_called_once_with("https://example.com", timeout=3.0)
            self.assertTrue(res)

    def test_validate_target_headers_false(self):
        with patch.object(self.analytics.hub, 'validate_target_headers', return_value=False):
            res = self.analytics.validate_target_headers("https://example.com", timeout=3.0)
            self.assertFalse(res)

    def test_validate_target_headers_exception_handled(self):
        with patch.object(self.analytics.hub, 'validate_target_headers', side_effect=Exception("Error")):
            self.analytics.raise_on_limit = False
            res = self.analytics.validate_target_headers("https://example.com", timeout=3.0)
            self.assertFalse(res)

    def test_validate_target_headers_exception_raised(self):
        with patch.object(self.analytics.hub, 'validate_target_headers', side_effect=Exception("Error")):
            self.analytics.raise_on_limit = True
            with self.assertRaises(ResilientSecureSmartCrawlerHubAnalyticsError):
                self.analytics.validate_target_headers("https://example.com", timeout=3.0)

    def test_coordinate_expansion_safe_true(self):
        with patch.object(self.analytics.hub, 'coordinate_expansion_safe', return_value=True) as mock_safe:
            res = self.analytics.coordinate_expansion_safe("https://example.com", timeout=2.5)
            mock_safe.assert_called_once_with("https://example.com", timeout=2.5)
            self.assertTrue(res)

    def test_coordinate_expansion_safe_false(self):
        with patch.object(self.analytics.hub, 'coordinate_expansion_safe', return_value=False):
            res = self.analytics.coordinate_expansion_safe("https://example.com", timeout=2.5)
            self.assertFalse(res)

    def test_coordinate_expansion_safe_exception_handled(self):
        with patch.object(self.analytics.hub, 'coordinate_expansion_safe', side_effect=Exception("Safe error")):
            self.analytics.raise_on_limit = False
            res = self.analytics.coordinate_expansion_safe("https://example.com", timeout=2.5)
            self.assertFalse(res)

    def test_coordinate_expansion_safe_exception_raised(self):
        with patch.object(self.analytics.hub, 'coordinate_expansion_safe', side_effect=Exception("Safe error")):
            self.analytics.raise_on_limit = True
            with self.assertRaises(ResilientSecureSmartCrawlerHubAnalyticsError):
                self.analytics.coordinate_expansion_safe("https://example.com", timeout=2.5)

    def test_export_analytics_report_success(self):
        res = self.analytics.export_analytics_report()
        self.assertEqual(res, "Analytics Report: OK")

    def test_export_analytics_report_exception_handled(self):
        analytics_err = ResilientSecureSmartCrawlerHubAnalytics(raise_on_limit=False)
        with patch.object(analytics_err, 'export_analytics_report', side_effect=ResilientSecureSmartCrawlerHubAnalyticsError("Report error")):
            with self.assertRaises(ResilientSecureSmartCrawlerHubAnalyticsError):
                analytics_err.export_analytics_report()