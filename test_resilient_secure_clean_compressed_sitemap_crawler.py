import unittest
from unittest.mock import patch, MagicMock
import io

from skills.resilient_secure_clean_compressed_sitemap_crawler import (
    ResilientSecureCleanCompressedSitemapCrawler,
    ResilientSecureCleanCompressedSitemapCrawlerError,
    resilient_secure_clean_compressed_sitemap_crawler_flow
)

class TestResilientSecureCleanCompressedSitemapCrawler(unittest.TestCase):

    def setUp(self):
        self.db_path = ":memory:"
        self.crawler = ResilientSecureCleanCompressedSitemapCrawler(
            db_path=self.db_path,
            max_memory_mb=128,
            calls=10,
            period=1.0,
            raise_on_limit=True
        )

    def test_init_sets_attributes(self):
        self.assertEqual(self.crawler.db_path, self.db_path)
        self.assertEqual(self.crawler.max_memory_mb, 128)

    def test_validate_sitemap_success(self):
        url = "https://example.com/sitemap.xml"
        with patch("skills.resilient_secure_clean_compressed_sitemap_crawler.resilient_clean_compressed_sitemap_crawler.ResilientCleanCompressedSitemapCrawler.validate_sitemap", return_value=True) as mock_validate:
            res = self.crawler.validate_sitemap(url, timeout=5)
            self.assertTrue(res)
            mock_validate.assert_called_once_with(url, 5)

    def test_validate_sitemap_failure(self):
        url = "https://example.com/bad-sitemap.xml"
        with patch("skills.resilient_secure_clean_compressed_sitemap_crawler.resilient_clean_compressed_sitemap_crawler.ResilientCleanCompressedSitemapCrawler.validate_sitemap", return_value=False) as mock_validate:
            res = self.crawler.validate_sitemap(url, timeout=5)
            self.assertFalse(res)

    def test_crawl_success(self):
        url = "https://example.com/sitemap.xml"
        expected_links = ["https://example.com/page1", "https://example.com/page2"]
        with patch("skills.resilient_secure_clean_compressed_sitemap_crawler.resilient_clean_compressed_sitemap_crawler.ResilientCleanCompressedSitemapCrawler.crawl", return_value=expected_links) as mock_crawl:
            links = self.crawler.crawl(url, timeout=5)
            self.assertEqual(links, expected_links)
            mock_crawl.assert_called_once_with(url, 5)

    def test_crawl_error_raises_custom_exception(self):
        url = "https://example.com/error-sitemap.xml"
        with patch("skills.resilient_secure_clean_compressed_sitemap_crawler.resilient_clean_compressed_sitemap_crawler.ResilientCleanCompressedSitemapCrawler.crawl", side_effect=Exception("Crawl failed")):
            with self.assertRaises(ResilientSecureCleanCompressedSitemapCrawlerError):
                self.crawler.crawl(url, timeout=5)

    def test_crawl_and_clean_success(self):
        url = "https://example.com/sitemap.xml"
        cleaned_links = ["https://example.com/cleaned1"]
        with patch("skills.resilient_secure_clean_compressed_sitemap_crawler.resilient_clean_compressed_sitemap_crawler.ResilientCleanCompressedSitemapCrawler.crawl_and_clean", return_value=cleaned_links) as mock_cac:
            res = self.crawler.crawl_and_clean(url, timeout=5)
            self.assertEqual(res, cleaned_links)
            mock_cac.assert_called_once_with(url, 5)

    def test_crawl_and_clean_error_raises_custom_exception(self):
        url = "https://example.com/sitemap.xml"
        with patch("skills.resilient_secure_clean_compressed_sitemap_crawler.resilient_clean_compressed_sitemap_crawler.ResilientCleanCompressedSitemapCrawler.crawl_and_clean", side_effect=Exception("Clean failed")):
            with self.assertRaises(ResilientSecureCleanCompressedSitemapCrawlerError):
                self.crawler.crawl_and_clean(url, timeout=5)

    def test_flow_function(self):
        url = "https://example.com/sitemap.xml"
        expected_links = ["https://example.com/1"]
        with patch("skills.resilient_secure_clean_compressed_sitemap_crawler.ResilientSecureCleanCompressedSitemapCrawler.crawl", return_value=expected_links) as mock_crawl:
            res = resilient_secure_clean_compressed_sitemap_crawler_flow(
                url=url,
                timeout=10,
                db_path=":memory:",
                max_memory_mb=64,
                calls=5,
                period=2.0,
                raise_on_limit=False
            )
            self.assertEqual(res, expected_links)
            mock_crawl.assert_called_once_with(url, 10)

    def test_memory_limit_enforcement(self):
        url = "https://example.com/sitemap.xml"
        with patch("skills.resilient_secure_clean_compressed_sitemap_crawler.memory_profiler.assert_memory_limit", side_effect=Exception("Memory limit exceeded")):
            with self.assertRaises(ResilientSecureCleanCompressedSitemapCrawlerError):
                self.crawler.crawl(url, timeout=5)

    def test_rate_limiter_integration(self):
        url = "https://example.com/sitemap.xml"
        with patch("skills.resilient_secure_clean_compressed_sitemap_crawler.rate_limiter.RateLimiter.acquire") as mock_acquire:
            with patch("skills.resilient_secure_clean_compressed_sitemap_crawler.resilient_clean_compressed_sitemap_crawler.ResilientCleanCompressedSitemapCrawler.crawl", return_value=[]):
                self.crawler.crawl(url, timeout=5)
                mock_acquire.assert_called()