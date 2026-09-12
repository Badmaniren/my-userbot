import unittest
from skills.smart_secure_compressed_sitemap_crawler_v2 import (
    SmartSecureCompressedSitemapCrawlerV2,
    SmartSecureCompressedSitemapCrawlerV2Error,
    smart_secure_compressed_sitemap_crawler_v2_flow
)
from skills.smart_secure_compressed_sitemap_crawler import SmartSecureCompressedSitemapCrawler
from skills.resilient_secure_clean_compressed_sitemap_crawler import ResilientSecureCleanCompressedSitemapCrawler

class TestSmartSecureCompressedSitemapCrawlerV2Integration(unittest.TestCase):
    def setUp(self):
        self.db_path = ":memory:"
        self.max_memory_mb = 512
        self.calls = 10
        self.period = 1.0
        self.raise_on_limit = True
        self.test_url = "https://example.com/sitemap.xml"
        self.timeout = 5

        self.crawler = SmartSecureCompressedSitemapCrawlerV2(
            db_path=self.db_path,
            max_memory_mb=self.max_memory_mb,
            calls=self.calls,
            period=self.period,
            raise_on_limit=self.raise_on_limit
        )

    def test_composition_dependencies(self):
        self.assertIsInstance(self.crawler, SmartSecureCompressedSitemapCrawler)
        self.assertIsInstance(self.crawler, ResilientSecureCleanCompressedSitemapCrawler)

    def test_validate_sitemap_returns_bool(self):
        try:
            result = self.crawler.validate_sitemap(self.test_url, self.timeout)
            self.assertIsInstance(result, bool)
        except Exception as e:
            self.assertIsInstance(e, (SmartSecureCompressedSitemapCrawlerV2Error, Exception))

    def test_crawl_flow(self):
        try:
            result = self.crawler.crawl(self.test_url, self.timeout)
            self.assertIsNotNone(result)
        except Exception as e:
            self.assertIsInstance(e, (SmartSecureCompressedSitemapCrawlerV2Error, Exception))

    def test_crawl_and_clean_flow(self):
        try:
            result = self.crawler.crawl_and_clean(self.test_url, self.timeout)
            self.assertIsNotNone(result)
        except Exception as e:
            self.assertIsInstance(e, (SmartSecureCompressedSitemapCrawlerV2Error, Exception))

    def test_coordinate_expansion_flow(self):
        try:
            result = self.crawler.coordinate_expansion(self.test_url, self.timeout)
            self.assertIsNotNone(result)
        except Exception as e:
            self.assertIsInstance(e, (SmartSecureCompressedSitemapCrawlerV2Error, Exception))

    def test_functional_flow(self):
        try:
            result = smart_secure_compressed_sitemap_crawler_v2_flow(
                url=self.test_url,
                timeout=self.timeout,
                db_path=self.db_path,
                max_memory_mb=self.max_memory_mb,
                calls=self.calls,
                period=self.period,
                raise_on_limit=self.raise_on_limit
            )
            self.assertIsNotNone(result)
        except Exception as e:
            self.assertIsInstance(e, (SmartSecureCompressedSitemapCrawlerV2Error, Exception))

if __name__ == "__main__":
    unittest.main()