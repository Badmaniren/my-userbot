import unittest
from unittest.mock import patch
from skills.clean_sitemap_parser_v2 import CleanSitemapParserV2
from skills.sitemap_parser import SitemapParser
from skills.url_cleaner import clean_url

class TestCleanSitemapParserV2Integration(unittest.TestCase):
    def setUp(self):
        self.parser = CleanSitemapParserV2()
        self.sample_sitemap_content = """<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url>
                <loc>https://EXAMPLE.com/page?utm_source=test&amp;param=1</loc>
            </url>
        </urlset>"""

    @patch('skills.sitemap_parser.SitemapParser.parse')
    def setup_mock_parse(self, mock_parse):
        mock_parse.return_value = [
            "https://EXAMPLE.com/page?utm_source=test&param=1"
        ]

    def test_composition_and_cleaning(self):
        with patch.object(SitemapParser, 'parse', return_value=[
            "https://EXAMPLE.com/page?utm_source=test&param=1"
        ]):
            result = self.parser.parse("https://example.com/sitemap.xml", timeout=5)
            self.assertIsInstance(result, list)
            self.assertTrue(len(result) > 0)
            self.assertEqual(result[0], clean_url("https://EXAMPLE.com/page?utm_source=test&param=1"))

    def test_validation_flow(self):
        with patch.object(SitemapParser, 'validate_sitemap', return_value=True):
            is_valid = self.parser.validate_sitemap("https://example.com/sitemap.xml", timeout=5)
            self.assertIsInstance(is_valid, bool)
            self.assertTrue(is_valid)

if __name__ == '__main__':
    unittest.main()