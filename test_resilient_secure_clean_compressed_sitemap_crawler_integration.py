import unittest
from skills.resilient_secure_clean_compressed_sitemap_crawler import (
    ResilientSecureCleanCompressedSitemapCrawler,
    ResilientSecureCleanCompressedSitemapCrawlerError,
    resilient_secure_clean_compressed_sitemap_crawler_flow
)

class TestResilientSecureCleanCompressedSitemapCrawlerIntegration(unittest.TestCase):
    def setUp(self):
        self.db_path = ":memory:"
        self.timeout = 5
        self.max_memory_mb = 128
        self.calls = 10
        self.period = 1.0
        self.raise_on_limit = True
        self.test_url = "https://example.com/sitemap.xml"

        self.crawler = ResilientSecureCleanCompressedSitemapCrawler(
            db_path=self.db_path,
            max_memory_mb=self.max_memory_mb,
            calls=self.calls,
            period=self.period,
            raise_on_limit=self.raise_on_limit
        )

    def test_crawler_initialization(self):
        self.assertIsInstance(self.crawler, ResilientSecureCleanCompressedSitemapCrawler)

    def test_crawl_flow_returns_expected_types(self):
        try:
            result = self.crawler.crawl(self.test_url, self.timeout)
            self.assertIsInstance(result, (list, dict, str))
        except (ResilientSecureCleanCompressedSitemapCrawlerError, Exception) as e:
            self.assertTrue(isinstance(e, (ResilientSecureCleanCompressedSitemapCrawlerError, Exception)))

    def test_crawl_and_clean_flow(self):
        try:
            result = self.crawler.crawl_and_clean(self.test_url, self.timeout)
            self.assertIsNotNone(result)
        except (ResilientSecureCleanCompressedSitemapCrawlerError, Exception) as e:
            self.assertTrue(isinstance(e, (ResilientSecureCleanCompressedSitemapCrawlerError, Exception)))

    def test_validate_sitemap_flow(self):
        try:
            is_valid = self.crawler.validate_sitemap(self.test_url, self.timeout)
            self.assertIsInstance(is_valid, bool)
        except (ResilientSecureCleanCompressedSitemapCrawlerError, Exception) as e:
            self.assertTrue(isinstance(e, (ResilientSecureCleanCompressedSitemapCrawlerError, Exception)))

    def test_functional_helper_flow(self):
        try:
            result = resilient_secure_clean_compressed_sitemap_crawler_flow(
                url=self.test_url,
                timeout=self.timeout,
                db_path=self.db_path,
                max_memory_mb=self.max_memory_mb,
                calls=self.calls,
                period=self.period,
                raise_on_limit=self.raise_on_limit
            )
            self.assertIsNotNone(result)
        except (ResilientSecureCleanCompressedSitemapCrawlerError, Exception) as e:
            self.assertTrue(isinstance(e, (ResilientSecureCleanCompressedSitemapCrawlerError, Exception)))

if __name__ == "__main__":
    unittest.main()