import unittest
from unittest.mock import patch, MagicMock
import io

from skills.resilient_clean_compressed_sitemap_parser_v2 import (
    ResilientCleanCompressedSitemapParserV2,
    ResilientCleanCompressedSitemapParserV2Error
)

class TestResilientCleanCompressedSitemapParserV2(unittest.TestCase):

    def setUp(self):
        self.db_path = ":memory:"
        self.parser = ResilientCleanCompressedSitemapParserV2(
            db_path=self.db_path,
            max_memory_mb=512,
            calls=10,
            period=1.0,
            raise_on_limit=True
        )

    def test_init_composition(self):
        self.assertIsNotNone(self.parser)
        self.assertEqual(self.parser.db_path, self.db_path)

    def test_parse_success(self):
        test_url = "https://example.com/sitemap.xml"
        mock_links = ["https://example.com/page1", "https://example.com/page2"]
        
        with patch('skills.resilient_clean_compressed_sitemap_parser.ResilientCleanCompressedSitemapParser.parse') as mock_base_parse:
            mock_base_parse.return_value = mock_links
            result = self.parser.parse(test_url, timeout=5)
            self.assertEqual(result, mock_links)
            mock_base_parse.assert_called_once_with(test_url, 5)

    def test_parse_memory_limit_exceeded(self):
        test_url = "https://example.com/sitemap.xml"
        
        with patch('skills.memory_profiler.assert_memory_limit') as mock_assert_mem:
            mock_assert_mem.side_effect = Exception("Memory limit exceeded")
            with self.assertRaises(Exception):
                self.parser.parse(test_url, timeout=5)

    def test_parse_and_clean_success(self):
        test_url = "https://example.com/sitemap.xml"
        mock_cleaned_data = [{"url": "https://example.com/page1"}]
        
        with patch('skills.resilient_clean_compressed_sitemap_parser.ResilientCleanCompressedSitemapParser.parse_and_clean') as mock_base_clean:
            mock_base_clean.return_value = mock_cleaned_data
            result = self.parser.parse_and_clean(test_url, timeout=5)
            self.assertEqual(result, mock_cleaned_data)
            mock_base_clean.assert_called_once_with(test_url, 5)

    def test_validate_sitemap_true(self):
        test_url = "https://example.com/sitemap.xml"
        
        with patch('skills.resilient_clean_compressed_sitemap_parser.ResilientCleanCompressedSitemapParser.validate_sitemap') as mock_validate:
            mock_validate.return_value = True
            res = self.parser.validate_sitemap(test_url, timeout=5)
            self.assertTrue(res)

    def test_validate_sitemap_false(self):
        test_url = "https://example.com/invalid_sitemap.xml"
        
        with patch('skills.resilient_clean_compressed_sitemap_parser.ResilientCleanCompressedSitemapParser.validate_sitemap') as mock_validate:
            mock_validate.return_value = False
            res = self.parser.validate_sitemap(test_url, timeout=5)
            self.assertFalse(res)

    def test_rate_limiter_integration(self):
        test_url = "https://example.com/sitemap.xml"
        
        with patch('skills.rate_limiter.RateLimiter.acquire') as mock_acquire:
            with patch('skills.resilient_clean_compressed_sitemap_parser.ResilientCleanCompressedSitemapParser.parse') as mock_parse:
                mock_parse.return_value = []
                self.parser.parse(test_url, timeout=5)
                mock_acquire.assert_called_once()

    def test_stream_io_handling(self):
        test_url = "https://example.com/sitemap.xml"
        stream_data = io.BytesIO(b'<sitemapindex><sitemap><loc>https://example.com/sub.xml</loc></sitemap></sitemapindex>')
        
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.raw = stream_data
            mock_response.content = stream_data.getvalue()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            with patch('skills.resilient_clean_compressed_sitemap_parser.ResilientCleanCompressedSitemapParser.parse') as mock_parse:
                mock_parse.return_value = ["https://example.com/sub.xml"]
                result = self.parser.parse(test_url, timeout=5)
                self.assertIsInstance(result, list)

if __name__ == '__main__':
    unittest.main()