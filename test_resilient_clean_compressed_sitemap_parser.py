import unittest
from unittest.mock import patch, MagicMock
import io

from skills.resilient_clean_compressed_sitemap_parser import (
    ResilientCleanCompressedSitemapParser,
    ResilientCleanCompressedSitemapParserError,
    resilient_clean_compressed_sitemap_parser_flow
)
from skills.clean_compressed_sitemap_parser_v3 import CleanCompressedSitemapParserError
from skills.rate_limiter import RateLimitExceeded


class TestResilientCleanCompressedSitemapParser(unittest.TestCase):

    def setUp(self):
        self.db_path = ":memory:"
        self.url = "https://example.com/sitemap.xml"
        self.timeout = 5
        self.parser = ResilientCleanCompressedSitemapParser(
            db_path=self.db_path,
            calls=10,
            period=1.0,
            raise_on_limit=True
        )

    def test_init(self):
        self.assertEqual(self.parser.db_path, self.db_path)
        self.assertIsNotNone(self.parser.rate_limiter)
        self.assertIsNotNone(self.parser.parser_v3)

    def test_parse_success(self):
        expected_links = ["https://example.com/page1", "https://example.com/page2"]
        with patch('skills.resilient_clean_compressed_sitemap_parser.RateLimiter.acquire') as mock_acquire, \
             patch('skills.clean_compressed_sitemap_parser_v3.CleanCompressedSitemapParserV3.parse') as mock_parse:
            
            mock_parse.return_value = expected_links
            result = self.parser.parse(self.url, self.timeout)
            
            mock_acquire.assert_called_once()
            mock_parse.assert_called_once_with(self.url, self.timeout)
            self.assertEqual(result, expected_links)

    def test_parse_rate_limit_exceeded(self):
        with patch('skills.resilient_clean_compressed_sitemap_parser.RateLimiter.acquire', side_effect=RateLimitExceeded("Limit")):
            with self.assertRaises(RateLimitExceeded):
                self.parser.parse(self.url, self.timeout)

    def test_parse_parser_error(self):
        with patch('skills.resilient_clean_compressed_sitemap_parser.RateLimiter.acquire'), \
             patch('skills.clean_compressed_sitemap_parser_v3.CleanCompressedSitemapParserV3.parse', side_effect=CleanCompressedSitemapParserError("Parser error")):
            
            with self.assertRaises(ResilientCleanCompressedSitemapParserError):
                self.parser.parse(self.url, self.timeout)

    def test_parse_and_clean_success(self):
        expected_cleaned = ["https://example.com/clean1"]
        with patch('skills.resilient_clean_compressed_sitemap_parser.RateLimiter.acquire') as mock_acquire, \
             patch('skills.clean_compressed_sitemap_parser_v3.CleanCompressedSitemapParserV3.parse_and_clean') as mock_pac:
            
            mock_pac.return_value = expected_cleaned
            result = self.parser.parse_and_clean(self.url, self.timeout)
            
            mock_acquire.assert_called_once()
            mock_pac.assert_called_once_with(self.url, self.timeout)
            self.assertEqual(result, expected_cleaned)

    def test_parse_and_clean_error(self):
        with patch('skills.resilient_clean_compressed_sitemap_parser.RateLimiter.acquire'), \
             patch('skills.clean_compressed_sitemap_parser_v3.CleanCompressedSitemapParserV3.parse_and_clean', side_effect=Exception("Unexpected")):
            
            with self.assertRaises(ResilientCleanCompressedSitemapParserError):
                self.parser.parse_and_clean(self.url, self.timeout)

    def test_validate_sitemap_true(self):
        with patch('skills.resilient_clean_compressed_sitemap_parser.RateLimiter.acquire') as mock_acquire, \
             patch('skills.clean_compressed_sitemap_parser_v3.CleanCompressedSitemapParserV3.validate_sitemap') as mock_val:
            
            mock_val.return_value = True
            res = self.parser.validate_sitemap(self.url, self.timeout)
            
            mock_acquire.assert_called_once()
            mock_val.assert_called_once_with(self.url, self.timeout)
            self.assertTrue(res)

    def test_validate_sitemap_false(self):
        with patch('skills.resilient_clean_compressed_sitemap_parser.RateLimiter.acquire'), \
             patch('skills.clean_compressed_sitemap_parser_v3.CleanCompressedSitemapParserV3.validate_sitemap', return_value=False):
            
            res = self.parser.validate_sitemap(self.url, self.timeout)
            self.assertFalse(res)

    def test_validate_sitemap_exception_returns_false(self):
        with patch('skills.resilient_clean_compressed_sitemap_parser.RateLimiter.acquire'), \
             patch('skills.clean_compressed_sitemap_parser_v3.CleanCompressedSitemapParserV3.validate_sitemap', side_effect=Exception("Fail")):
            
            res = self.parser.validate_sitemap(self.url, self.timeout)
            self.assertFalse(res)

    def test_functional_flow_success(self):
        expected = ["https://example.com/flow"]
        with patch('skills.resilient_clean_compressed_sitemap_parser.ResilientCleanCompressedSitemapParser.parse_and_clean', return_value=expected) as mock_pac:
            res = resilient_clean_compressed_sitemap_parser_flow(self.url, self.timeout, self.db_path)
            mock_pac.assert_called_once_with(self.url, self.timeout)
            self.assertEqual(res, expected)

    def test_functional_flow_error(self):
        with patch('skills.resilient_clean_compressed_sitemap_parser.ResilientCleanCompressedSitemapParser.parse_and_clean', side_effect=Exception("Flow fail")):
            with self.assertRaises(ResilientCleanCompressedSitemapParserError):
                resilient_clean_compressed_sitemap_parser_flow(self.url, self.timeout, self.db_path)


if __name__ == '__main__':
    unittest.main()