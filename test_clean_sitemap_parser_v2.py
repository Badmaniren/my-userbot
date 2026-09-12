import unittest
from unittest.mock import patch, MagicMock
import io
import requests

from skills.clean_sitemap_parser_v2 import CleanSitemapParser, CleanSitemapParserError

class TestCleanSitemapParserV2(unittest.TestCase):

    def setUp(self):
        self.parser = CleanSitemapParser()

    def test_init_success(self):
        self.assertIsInstance(self.parser, CleanSitemapParser)

    def test_parse_sitemap_success(self):
        mock_xml = b'''<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url>
                <loc>https://EXAMPLE.COM/page1/?utm_source=test&amp;ref=1</loc>
            </url>
            <url>
                <loc>https://example.com/page2/</loc>
            </url>
        </urlset>'''

        with patch('skills.sitemap_parser.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = mock_xml
            mock_response.text = mock_xml.decode('utf-8')
            mock_get.return_value = mock_response

            urls = self.parser.parse("https://example.com/sitemap.xml", timeout=5)
            
            self.assertIsInstance(urls, list)
            self.assertGreaterEqual(len(urls), 2)
            self.assertIn("https://example.com/page1/", urls)
            self.assertNotIn("utm_source=test", urls[0])

    def test_parse_sitemap_network_error(self):
        with patch('skills.sitemap_parser.requests.get', side_effect=requests.RequestException("Timeout")):
            with self.assertRaises(CleanSitemapParserError):
                self.parser.parse("https://example.com/sitemap.xml", timeout=5)

    def test_validate_sitemap_true(self):
        mock_xml = b'''<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url><loc>https://example.com/</loc></url>
        </urlset>'''

        with patch('skills.sitemap_parser.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = mock_xml
            mock_get.return_value = mock_response

            result = self.parser.validate_sitemap("https://example.com/sitemap.xml", timeout=5)
            self.assertTrue(result)

    def test_validate_sitemap_false(self):
        with patch('skills.sitemap_parser.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_get.return_value = mock_response

            result = self.parser.validate_sitemap("https://example.com/sitemap.xml", timeout=5)
            self.assertFalse(result)

    def test_url_cleaning_integration(self):
        raw_urls = [
            "HTTP://EXAMPLE.COM/PATH/?utm_medium=cpc&id=123",
            "https://example.com/another/"
        ]

        with patch.object(CleanSitemapParser, 'parse', return_value=raw_urls):
            cleaned = self.parser.parse_and_clean("https://example.com/sitemap.xml", timeout=5)
            self.assertIn("http://example.com/path/?id=123", cleaned)
            self.assertNotIn("utm_medium=cpc", cleaned[0])

    def test_empty_sitemap_content(self):
        mock_xml = b''

        with patch('skills.sitemap_parser.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = mock_xml
            mock_response.text = ""
            mock_get.return_value = mock_response

            urls = self.parser.parse("https://example.com/sitemap.xml", timeout=5)
            self.assertEqual(urls, [])

if __name__ == '__main__':
    unittest.main()