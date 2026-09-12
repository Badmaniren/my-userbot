import unittest
from unittest.mock import patch, MagicMock
import requests
import io

from skills.clean_sitemap_parser_v2 import CleanSitemapParser, CleanSitemapParserV2, CleanSitemapParserError

class TestCleanSitemapParserV2(unittest.TestCase):

    def setUp(self):
        self.parser = CleanSitemapParserV2()

    def test_parse_sitemap_success(self):
        with patch('skills.sitemap_parser.SitemapParser.parse') as mock_parse:
            mock_parse.return_value = [
                'https://example.com/page1/?ref=1',
                'https://example.com/page2/'
            ]
            urls = self.parser.parse('https://example.com/sitemap.xml')
            self.assertIn('https://example.com/page1/?ref=1', urls)
            self.assertIn('https://example.com/page2/', urls)

    def test_url_cleaning_integration(self):
        with patch('skills.sitemap_parser.SitemapParser.parse') as mock_parse:
            mock_parse.return_value = [
                'HTTP://EXAMPLE.COM/PATH/?utm_medium=cpc&id=123',
                'https://example.com/another/'
            ]
            cleaned = self.parser.parse('https://example.com/sitemap.xml')
            self.assertIn('http://example.com/path/?id=123', cleaned)

    def test_validate_sitemap_true(self):
        with patch('skills.sitemap_parser.SitemapParser.validate_sitemap') as mock_validate:
            mock_validate.return_value = True
            result = self.parser.validate_sitemap('https://example.com/sitemap.xml')
            self.assertTrue(result)

    def test_validate_sitemap_false(self):
        with patch('skills.sitemap_parser.SitemapParser.validate_sitemap') as mock_validate:
            mock_validate.return_value = False
            result = self.parser.validate_sitemap('https://example.com/sitemap.xml')
            self.assertFalse(result)

    def test_validate_sitemap_exception(self):
        with patch('skills.sitemap_parser.SitemapParser.validate_sitemap') as mock_validate:
            mock_validate.side_effect = Exception('Validation error')
            result = self.parser.validate_sitemap('https://example.com/sitemap.xml')
            self.assertFalse(result)

    def test_parse_request_exception(self):
        with patch('skills.sitemap_parser.SitemapParser.parse') as mock_parse:
            mock_parse.side_effect = requests.RequestException('Network down')
            with self.assertRaises(CleanSitemapParserError):
                self.parser.parse('https://example.com/sitemap.xml')

    def test_parse_general_exception(self):
        with patch('skills.sitemap_parser.SitemapParser.parse') as mock_parse:
            mock_parse.side_effect = Exception('Unexpected error')
            with self.assertRaises(CleanSitemapParserError):
                self.parser.parse('https://example.com/sitemap.xml')

    def test_parse_and_clean_alias(self):
        with patch('skills.sitemap_parser.SitemapParser.parse') as mock_parse:
            mock_parse.return_value = ['https://example.com/test/']
            urls = self.parser.parse_and_clean('https://example.com/sitemap.xml')
            self.assertEqual(urls, ['https://example.com/test/'])

if __name__ == '__main__':
    unittest.main()