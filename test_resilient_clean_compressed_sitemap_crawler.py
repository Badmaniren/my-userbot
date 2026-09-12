import unittest
from unittest.mock import patch
import io

from skills.resilient_clean_compressed_sitemap_crawler import (
    ResilientCleanCompressedSitemapCrawler,
    ResilientCleanCompressedSitemapCrawlerError,
    resilient_clean_compressed_sitemap_crawler_flow
)

class TestResilientCleanCompressedSitemapCrawler(unittest.TestCase):

    def setUp(self):
        self.db_path = ":memory:"
        self.calls = 5
        self.period = 1.0
        self.raise_on_limit = True
        self.crawler = ResilientCleanCompressedSitemapCrawler(
            db_path=self.db_path,
            calls=self.calls,
            period=self.period,
            raise_on_limit=self.raise_on_limit
        )
        self.test_url = "https://example.com/sitemap.xml"
        self.timeout = 5

    def test_initialization(self):
        self.assertIsNotNone(self.crawler)
        self.assertEqual(self.crawler.db_path, self.db_path)
        self.assertIsNotNone(self.crawler.rate_limiter)
        self.assertIsNotNone(self.crawler.parser)

    @patch('skills.resilient_clean_compressed_sitemap_parser.ResilientCleanCompressedSitemapParser.parse')
    def test_crawl_success(self, mock_parse):
        mock_parse.return_value = ["https://example.com/page1", "https://example.com/page2"]
        result = self.crawler.crawl(self.test_url, self.timeout)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertIn("https://example.com/page1", result)

    @patch('skills.resilient_clean_compressed_sitemap_parser.ResilientCleanCompressedSitemapParser.parse')
    def test_crawl_empty(self, mock_parse):
        mock_parse.return_value = []
        result = self.crawler.crawl(self.test_url, self.timeout)
        self.assertEqual(result, [])

    @patch('skills.resilient_clean_compressed_sitemap_parser.ResilientCleanCompressedSitemapParser.parse')
    def test_crawl_exception_handling(self, mock_parse):
        mock_parse.side_effect = Exception("Parsing failed")
        with self.assertRaises(ResilientCleanCompressedSitemapCrawlerError):
            self.crawler.crawl(self.test_url, self.timeout)

    @patch('skills.resilient_clean_compressed_sitemap_parser.ResilientCleanCompressedSitemapParser.parse_and_clean')
    def test_crawl_and_clean_success(self, mock_parse_clean):
        mock_parse_clean.return_value = ["https://example.com/clean1"]
        result = self.crawler.crawl_and_clean(self.test_url, self.timeout)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)

    @patch('skills.resilient_clean_compressed_sitemap_parser.ResilientCleanCompressedSitemapParser.parse_and_clean')
    def test_crawl_and_clean_exception(self, mock_parse_clean):
        mock_parse_clean.side_effect = Exception("Clean error")
        with self.assertRaises(ResilientCleanCompressedSitemapCrawlerError):
            self.crawler.crawl_and_clean(self.test_url, self.timeout)

    @patch('skills.resilient_clean_compressed_sitemap_parser.ResilientCleanCompressedSitemapParser.validate_sitemap')
    def test_validate_sitemap_true(self, mock_validate):
        mock_validate.return_value = True
        res = self.crawler.validate_sitemap(self.test_url, self.timeout)
        self.assertTrue(res)

    @patch('skills.resilient_clean_compressed_sitemap_parser.ResilientCleanCompressedSitemapParser.validate_sitemap')
    def test_validate_sitemap_false(self, mock_validate):
        mock_validate.return_value = False
        res = self.crawler.validate_sitemap(self.test_url, self.timeout)
        self.assertFalse(res)

    @patch('skills.resilient_clean_compressed_sitemap_parser.ResilientCleanCompressedSitemapParser.validate_sitemap')
    def test_validate_sitemap_error_returns_false(self, mock_validate):
        mock_validate.side_effect = Exception("Validation error")
        res = self.crawler.validate_sitemap(self.test_url, self.timeout)
        self.assertFalse(res)

    @patch('skills.rate_limiter.RateLimiter.acquire')
    @patch('skills.resilient_clean_compressed_sitemap_parser.ResilientCleanCompressedSitemapParser.parse')
    def test_rate_limiter_integration(self, mock_parse, mock_acquire):
        mock_parse.return_value = ["https://example.com/p"]
        mock_acquire.return_value = None
        result = self.crawler.crawl(self.test_url, self.timeout)
        mock_acquire.assert_called_once()
        self.assertEqual(result, ["https://example.com/p"])

    @patch('skills.resilient_clean_compressed_sitemap_crawler.ResilientCleanCompressedSitemapCrawler.crawl')
    def test_flow_function(self, mock_crawl):
        mock_crawl.return_value = ["https://example.com/flow"]
        res = resilient_clean_compressed_sitemap_crawler_flow(self.test_url, self.timeout, self.db_path)
        self.assertEqual(res, ["https://example.com/flow"])

if __name__ == '__main__':
    unittest.main()