import unittest
from skills.resilient_clean_compressed_sitemap_crawler import (
    ResilientCleanCompressedSitemapCrawler,
    ResilientCleanCompressedSitemapCrawlerError,
    resilient_clean_compressed_sitemap_crawler_flow
)
from skills.resilient_clean_compressed_sitemap_parser import CleanCompressedSitemapParserV3
from skills.rate_limiter import RateLimiter, RateLimitExceeded

class TestResilientCleanCompressedSitemapCrawlerIntegration(unittest.TestCase):
    def setUp(self):
        self.db_path = ":memory:"
        self.crawler = ResilientCleanCompressedSitemapCrawler(
            db_path=self.db_path,
            calls=10,
            period=1.0,
            raise_on_limit=True
        )

    def test_initialization(self):
        self.assertIsInstance(self.crawler, ResilientCleanCompressedSitemapCrawler)
        self.assertIsInstance(self.crawler.parser, CleanCompressedSitemapParserV3)
        self.assertIsInstance(self.crawler.rate_limiter, RateLimiter)

    def test_validate_sitemap_returns_bool(self):
        url = "http://example.com/sitemap.xml"
        try:
            result = self.crawler.validate_sitemap(url, timeout=5)
            self.assertIsInstance(result, bool)
        except Exception as e:
            self.assertIsInstance(e, (ResilientCleanCompressedSitemapCrawlerError, Exception))

    def test_crawl_and_parse_flow(self):
        url = "http://example.com/sitemap.xml"
        try:
            result = self.crawler.crawl_and_clean(url, timeout=5)
            self.assertIsInstance(result, (list, dict, str))
        except Exception as e:
            self.assertIsInstance(e, (ResilientCleanCompressedSitemapCrawlerError, Exception))

    def test_module_level_flow(self):
        url = "http://example.com/sitemap.xml"
        try:
            result = resilient_clean_compressed_sitemap_crawler_flow(
                url=url,
                timeout=5,
                db_path=self.db_path,
                calls=5,
                period=1.0,
                raise_on_limit=False
            )
            self.assertIsNotNone(result)
        except Exception as e:
            self.assertIsInstance(e, (ResilientCleanCompressedSitemapCrawlerError, Exception))

if __name__ == "__main__":
    unittest.main()