import unittest
from unittest.mock import patch, MagicMock
import io

from skills.resilient_secure_smart_aggregator_v5 import (
    ResilientSecureSmartAggregatorV5,
    ResilientSecureSmartAggregatorV5Error
)


class TestResilientSecureSmartAggregatorV5(unittest.TestCase):

    def setUp(self):
        self.aggregator = ResilientSecureSmartAggregatorV5(
            db_path=":memory:",
            max_memory_mb=50,
            calls=10,
            period=1.0,
            raise_on_limit=False
        )
        self.test_url = "https://example.com"
        self.timeout = 5

    def test_init_default_components(self):
        agg = ResilientSecureSmartAggregatorV5()
        self.assertIsNotNone(agg.hub)
        self.assertIsNotNone(agg.rss_crawler)
        self.assertIsNotNone(agg.sitemap_crawler)

    def test_coordinate_expansion(self):
        with patch.object(self.aggregator.hub, "coordinate_expansion", return_value={"hub_data": 1}) as m_hub, \
             patch.object(self.aggregator.rss_crawler, "coordinate_expansion", return_value={"rss_data": 2}) as m_rss, \
             patch.object(self.aggregator.sitemap_crawler, "coordinate_expansion", return_value={"sitemap_data": 3}) as m_site:

            res = self.aggregator.coordinate_expansion(self.test_url, self.timeout)
            self.assertEqual(res, {"hub_data": 1, "rss_data": 2, "sitemap_data": 3})
            m_hub.assert_called_once_with(self.test_url, self.timeout)
            m_rss.assert_called_once_with(self.test_url, self.timeout)
            m_site.assert_called_once_with(self.test_url, self.timeout)

    def test_coordinate_expansion_non_dict_returns(self):
        with patch.object(self.aggregator.hub, "coordinate_expansion", return_value="hub_str"), \
             patch.object(self.aggregator.rss_crawler, "coordinate_expansion", return_value="rss_str"), \
             patch.object(self.aggregator.sitemap_crawler, "coordinate_expansion", return_value="sitemap_str"):

            res = self.aggregator.coordinate_expansion(self.test_url, self.timeout)
            self.assertEqual(res, {"hub": "hub_str", "rss": "rss_str", "sitemap": "sitemap_str"})

    def test_coordinate_expansion_safe_bool(self):
        with patch.object(self.aggregator.hub, "coordinate_expansion_safe", return_value=True):
            res_true = self.aggregator.coordinate_expansion_safe(self.test_url, self.timeout)
            self.assertTrue(res_true)

        with patch.object(self.aggregator.hub, "coordinate_expansion_safe", side_effect=Exception("error")):
            res_false = self.aggregator.coordinate_expansion_safe(self.test_url, self.timeout)
            self.assertFalse(res_false)

    def test_validate_target_headers(self):
        with patch.object(self.aggregator.hub, "validate_target_headers", return_value=True):
            self.assertTrue(self.aggregator.validate_target_headers(self.test_url, self.timeout))

        with patch.object(self.aggregator.hub, "validate_target_headers", side_effect=Exception):
            self.assertFalse(self.aggregator.validate_target_headers(self.test_url, self.timeout))

    def test_validate_target_with_and_without_method(self):
        if hasattr(self.aggregator.hub, "validate_target"):
            with patch.object(self.aggregator.hub, "validate_target", return_value=True):
                self.assertTrue(self.aggregator.validate_target(self.test_url, self.timeout))
        else:
            with patch.object(self.aggregator.hub, "validate_target_headers", return_value=True):
                self.assertTrue(self.aggregator.validate_target(self.test_url, self.timeout))

        with patch.object(self.aggregator.hub, "validate_target_headers", side_effect=Exception):
            self.assertFalse(self.aggregator.validate_target(self.test_url, self.timeout))

    def test_process_stream(self):
        mock_stream = io.BytesIO(b"stream_data")
        with patch.object(self.aggregator.hub, "process_stream", return_value=mock_stream) as m_stream:
            res = self.aggregator.process_stream(self.test_url, self.timeout)
            self.assertEqual(res.read(), b"stream_data")
            m_stream.assert_called_once_with(self.test_url, self.timeout)

    def test_aggregate_rss_feed(self):
        with patch.object(self.aggregator.rss_crawler, "archive_feed", return_value=True) as m_archive:
            self.assertTrue(self.aggregator.aggregate_rss_feed(self.test_url, self.timeout, force_refresh=True))
            m_archive.assert_called_once_with(self.test_url, self.timeout, force_refresh=True)

        with patch.object(self.aggregator.rss_crawler, "archive_feed", side_effect=Exception):
            self.assertFalse(self.aggregator.aggregate_rss_feed(self.test_url, self.timeout))

    def test_aggregate_sitemap(self):
        pages = ["https://example.com/page1", "https://example.com/page2"]
        with patch.object(self.aggregator.sitemap_crawler, "crawl_and_clean", return_value=pages) as m_crawl:
            res = self.aggregator.aggregate_sitemap(self.test_url, self.timeout)
            self.assertIn("https://example.com/page1", res)
            m_crawl.assert_called_once_with(self.test_url, self.timeout)

        with patch.object(self.aggregator.sitemap_crawler, "crawl_and_clean", return_value=None):
            res_none = self.aggregator.aggregate_sitemap(self.test_url, self.timeout)
            self.assertEqual(res_none, [])

    def test_run_unified_expansion(self):
        with patch.object(self.aggregator.rss_crawler, "archive_feed", return_value="rss_feed_data"), \
             patch.object(self.aggregator.sitemap_crawler, "crawl_and_clean", return_value=["site1"]), \
             patch.object(self.aggregator.hub, "coordinate_expansion", return_value={"status": "ok"}):

            res = self.aggregator.run_unified_expansion(self.test_url, self.timeout)
            self.assertEqual(res['rss_data'], "rss_feed_data")
            self.assertEqual(res['sitemap_data'], ["site1"])
            self.assertEqual(res['hub_status'], {'status': 'ok'})

        with patch.object(self.aggregator.rss_crawler, "archive_feed", side_effect=Exception), \
             patch.object(self.aggregator.sitemap_crawler, "crawl_and_clean", side_effect=Exception), \
             patch.object(self.aggregator.hub, "coordinate_expansion", side_effect=Exception):

            res_err = self.aggregator.run_unified_expansion(self.test_url, self.timeout)
            self.assertIsNone(res_err['rss_data'])
            self.assertEqual(res_err['sitemap_data'], [])
            self.assertEqual(res_err['hub_status'], "failed")

    def test_get_cached_rss_content(self):
        if hasattr(self.aggregator.rss_crawler, "get_cached_feed"):
            with patch.object(self.aggregator.rss_crawler, "get_cached_feed", return_value="cached_feed_str"):
                self.assertEqual(self.aggregator.get_cached_rss_content(self.test_url), "cached_feed_str")

        with patch.object(self.aggregator.rss_crawler, "get_cached_feed", return_value=None, create=True), \
             patch.object(self.aggregator.rss_crawler, "get_cached_content", return_value="cached_content_str", create=True):
            self.assertEqual(self.aggregator.get_cached_rss_content(self.test_url), "cached_content_str")

        with patch.object(self.aggregator.rss_crawler, "get_cached_feed", return_value=None, create=True), \
             patch.object(self.aggregator.rss_crawler, "get_cached_content", return_value=None, create=True):
            self.assertEqual(self.aggregator.get_cached_rss_content(self.test_url), "cached_rss_content")

    def test_verify_sitemap_structure(self):
        if hasattr(self.aggregator.sitemap_crawler, "verify_sitemap_structure"):
            with patch.object(self.aggregator.sitemap_crawler, "verify_sitemap_structure", return_value=True):
                self.assertTrue(self.aggregator.verify_sitemap_structure(self.test_url, self.timeout))
        else:
            with patch.object(self.aggregator.sitemap_crawler, "crawl_and_clean", return_value=["page"]):
                self.assertTrue(self.aggregator.verify_sitemap_structure(self.test_url, self.timeout))

        with patch.object(self.aggregator.sitemap_crawler, "crawl_and_clean", side_effect=Exception):
            self.assertFalse(self.aggregator.verify_sitemap_structure(self.test_url, self.timeout))