import unittest
from unittest.mock import patch, MagicMock
from skills.resilient_secure_clean_url_crawler_v2 import (
    ResilientSecureCleanUrlCrawlerV2,
    ResilientSecureCleanUrlCrawlerV2Error
)

class TestResilientSecureCleanUrlCrawlerV2(unittest.TestCase):

    def test_init_defaults(self):
        crawler = ResilientSecureCleanUrlCrawlerV2()
        self.assertEqual(crawler.calls, 10)
        self.assertEqual(crawler.period, 1.0)
        self.assertTrue(crawler.raise_on_limit)
        self.assertIsNotNone(crawler.rate_limiter)

    def test_clean_url_custom_mapping(self):
        crawler = ResilientSecureCleanUrlCrawlerV2()
        with patch('skills.resilient_secure_clean_url_crawler_v2.clean_url') as mock_clean:
            mock_clean.return_value = "https://example.com/"
            res = crawler.clean_url("https://example.com/?utm_source=test")
            self.assertEqual(res, "https://example.com/clean")
            mock_clean.assert_called_once_with("https://example.com/?utm_source=test")

    def test_clean_url_regular(self):
        crawler = ResilientSecureCleanUrlCrawlerV2()
        with patch('skills.resilient_secure_clean_url_crawler_v2.clean_url') as mock_clean:
            mock_clean.return_value = "https://other.com/page"
            res = crawler.clean_url("https://other.com/page?ref=1")
            self.assertEqual(res, "https://other.com/page")
            mock_clean.assert_called_once_with("https://other.com/page?ref=1")

    def test_validate_crawled_link_success(self):
        crawler = ResilientSecureCleanUrlCrawlerV2()
        with patch('skills.resilient_clean_url_crawler.ResilientCleanUrlCrawler.validate_crawled_link') as mock_validate:
            mock_validate.return_value = True
            res = crawler.validate_crawled_link("https://example.com", timeout=3)
            self.assertTrue(res)
            mock_validate.assert_called_once_with("https://example.com", timeout=3)

    def test_validate_crawled_link_exception(self):
        crawler = ResilientSecureCleanUrlCrawlerV2()
        with patch('skills.resilient_clean_url_crawler.ResilientCleanUrlCrawler.validate_crawled_link', side_effect=Exception("Network error")):
            res = crawler.validate_crawled_link("https://example.com", timeout=3)
            self.assertFalse(res)

    def test_extract_and_clean_composition(self):
        crawler = ResilientSecureCleanUrlCrawlerV2()
        with patch('skills.resilient_clean_url_crawler.ResilientCleanUrlCrawler.extract_and_clean') as mock_extract:
            mock_extract.return_value = ["https://example.com/1"]
            res = crawler.extract_and_clean("<html></html>")
            self.assertEqual(res, ["https://example.com/1"])
            mock_extract.assert_called_once_with("<html></html>")

    def test_process_url_success(self):
        crawler = ResilientSecureCleanUrlCrawlerV2(raise_on_limit=True)
        with patch('skills.rate_limiter.RateLimiter.acquire') as mock_acquire, \
             patch('skills.resilient_clean_url_crawler.ResilientCleanUrlCrawler.process_url') as mock_process:
            mock_process.return_value = True
            res = crawler.process_url("https://example.com", timeout=5)
            self.assertTrue(res)
            mock_acquire.assert_called_once()
            mock_process.assert_called_once_with("https://example.com", timeout=5)

    def test_process_url_exception_raise_false(self):
        crawler = ResilientSecureCleanUrlCrawlerV2(raise_on_limit=False)
        with patch('skills.rate_limiter.RateLimiter.acquire') as mock_acquire, \
             patch('skills.resilient_clean_url_crawler.ResilientCleanUrlCrawler.process_url', side_effect=Exception("Failed")):
            mock_acquire.return_value = None
            with self.assertRaises(ResilientSecureCleanUrlCrawlerV2Error):
                crawler.process_url("https://example.com", timeout=5)

    def test_process_url_exception_raise_true(self):
        crawler = ResilientSecureCleanUrlCrawlerV2(raise_on_limit=True)
        with patch('skills.rate_limiter.RateLimiter.acquire') as mock_acquire, \
             patch('skills.resilient_clean_url_crawler.ResilientCleanUrlCrawler.process_url', side_effect=Exception("Failed")):
            mock_acquire.return_value = None
            res = crawler.process_url("https://example.com", timeout=5)
            self.assertFalse(res)