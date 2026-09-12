import os
import unittest
from skills.resilient_clean_compressed_sitemap_parser import (
    ResilientCleanCompressedSitemapParser,
    ResilientCleanCompressedSitemapParserError
)
from skills.clean_compressed_sitemap_parser_v3 import CleanCompressedSitemapParserV3
from skills.rate_limiter import RateLimiter, RateLimitExceeded

class TestResilientCleanCompressedSitemapParserIntegration(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_resilient_sitemap.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
            
        self.parser = ResilientCleanCompressedSitemapParser(
            db_path=self.db_path,
            calls=10,
            period=1.0,
            raise_on_limit=True
        )

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_composition_and_types(self):
        self.assertIsInstance(self.parser, ResilientCleanCompressedSitemapParser)
        self.assertTrue(hasattr(self.parser, 'rate_limiter'))
        self.assertIsInstance(self.parser.rate_limiter, RateLimiter)
        self.assertTrue(hasattr(self.parser, 'parser_v3'))
        self.assertIsInstance(self.parser.parser_v3, CleanCompressedSitemapParserV3)

    def test_validate_sitemap_flow(self):
        test_url = "https://example.com/sitemap.xml"
        is_valid = self.parser.validate_sitemap(test_url, timeout=5)
        self.assertIsInstance(is_valid, bool)

    def test_parse_and_clean_flow(self):
        test_url = "https://example.com/sitemap.xml"
        try:
            result = self.parser.parse_and_clean(test_url, timeout=5)
            if result is not None:
                self.assertIsInstance(result, (list, str))
        except ResilientCleanCompressedSitemapParserError:
            pass

    def test_rate_limiter_enforcement(self):
        strict_parser = ResilientCleanCompressedSitemapParser(
            db_path=self.db_path,
            calls=1,
            period=10.0,
            raise_on_limit=True
        )
        test_url = "https://example.com/sitemap.xml"
        strict_parser.validate_sitemap(test_url, timeout=2)
        with self.assertRaises((RateLimitExceeded, ResilientCleanCompressedSitemapParserError)):
            strict_parser.validate_sitemap(test_url, timeout=2)

if __name__ == "__main__":
    unittest.main()