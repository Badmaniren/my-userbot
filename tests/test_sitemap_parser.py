import unittest
from unittest.mock import patch, MagicMock
import io
from skills.sitemap_parser import SitemapParser, SitemapParserError

class TestSitemapParser(unittest.TestCase):

    def setUp(self):
        self.parser = SitemapParser()
        self.sample_sitemap = b"""<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url><loc>http://example.com/page1</loc></url>
            <url><loc>http://example.com/page2</loc></url>
        </urlset>"""
        
        self.sample_index = b"""<?xml version="1.0" encoding="UTF-8"?>
        <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <sitemap><loc>http://example.com/sitemap1.xml</loc></sitemap>
        </sitemapindex>"""

    def test_parse_valid_sitemap(self):
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.content = self.sample_sitemap
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            links = self.parser.parse("http://example.com/sitemap.xml")
            self.assertEqual(len(links), 2)
            self.assertIn("http://example.com/page1", links)

    def test_parse_sitemap_index(self):
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.content = self.sample_index
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            links = self.parser.parse("http://example.com/sitemap_index.xml")
            self.assertTrue(len(links) > 0)

    def test_parse_invalid_xml_raises(self):
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.content = b"not xml"
            mock_get.return_value = mock_response
            
            with self.assertRaises(SitemapParserError):
                self.parser.parse("http://example.com/bad.xml")

    def test_validate_sitemap_url_success(self):
        with patch('requests.head') as mock_head:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_head.return_value = mock_response
            
            res = self.parser.validate_sitemap("http://example.com/sitemap.xml", timeout=5)
            self.assertTrue(res)

    def test_validate_sitemap_url_failure(self):
        with patch('requests.head') as mock_head:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_head.return_value = mock_response
            
            res = self.parser.validate_sitemap("http://example.com/404.xml", timeout=5)
            self.assertFalse(res)

    def test_extract_links_empty_content(self):
        links = self.parser.extract_links(b"")
        self.assertEqual(links, [])

    def test_parse_network_timeout(self):
        with patch('requests.get', side_effect=Exception("Timeout")):
            with self.assertRaises(SitemapParserError):
                self.parser.parse("http://example.com/timeout.xml")

    def test_is_sitemap_index_detection(self):
        self.assertTrue(self.parser.is_sitemap_index(self.sample_index))
        self.assertFalse(self.parser.is_sitemap_index(self.sample_sitemap))

if __name__ == '__main__':
    unittest.main()