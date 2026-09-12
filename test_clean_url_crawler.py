import unittest
from unittest.mock import patch, MagicMock
import io

from skills.clean_url_crawler import CleanUrlCrawler


class TestCleanUrlCrawler(unittest.TestCase):

    def setUp(self):
        self.crawler = CleanUrlCrawler()

    def test_composition_dependencies(self):
        with patch('skills.clean_url_crawler.LinkExtractor') as mock_le, \
             patch('skills.clean_url_crawler.url_cleaner') as mock_uc:
            
            mock_le_instance = mock_le.return_value
            mock_le_instance.extract.return_value = ["http://example.com/page?utm_source=test"]
            mock_uc.clean_url.side_effect = lambda u: u.split("?")[0]

            html = "<html><a href='http://example.com/page?utm_source=test'>Link</a></html>"
            result = self.crawler.extract_and_clean(html)

            mock_le_instance.extract.assert_called_once_with(html)
            mock_uc.clean_url.assert_called_once()
            self.assertIn("http://example.com/page", result)

    def test_extract_and_clean_valid_links(self):
        with patch('skills.clean_url_crawler.LinkExtractor') as mock_le, \
             patch('skills.clean_url_crawler.url_cleaner') as mock_uc:
            
            mock_le.return_value.extract.return_value = [
                "HTTPS://EXAMPLE.COM/PATH/?utm_medium=cpc&ref=123",
                "http://example.org/about/"
            ]
            mock_uc.clean_url.side_effect = lambda u: u.lower().split("?")[0]

            result = self.crawler.extract_and_clean("<html></html>")
            self.assertIsInstance(result, list)
            self.assertTrue(len(result) == 2)
            self.assertIn("https://example.com/path/", result)
            self.assertIn("http://example.org/about/", result)

    def test_validate_crawled_link_success(self):
        with patch('skills.clean_url_crawler.LinkExtractor') as mock_le:
            mock_le.return_value.validate_link.return_value = True
            
            res = self.crawler.validate_crawled_link("http://example.com", timeout=5)
            self.assertTrue(res)

    def test_validate_crawled_link_failure(self):
        with patch('skills.clean_url_crawler.LinkExtractor') as mock_le:
            mock_le.return_value.validate_link.return_value = False
            
            res = self.crawler.validate_crawled_link("http://broken-link.com", timeout=5)
            self.assertFalse(res)

    def test_validate_crawled_link_exception_handled(self):
        with patch('skills.clean_url_crawler.LinkExtractor') as mock_le:
            mock_le.return_value.validate_link.side_effect = Exception("Connection error")
            
            res = self.crawler.validate_crawled_link("http://error.com", timeout=5)
            self.assertFalse(res)

    def test_process_crawled_url_with_cache(self):
        with patch('skills.clean_url_crawler.LinkExtractor') as mock_le:
            mock_le.return_value.process_with_cache.return_value = True

            res = self.crawler.process_url("http://example.com/cached", timeout=3)
            self.assertTrue(res)

    def test_stream_io_mocking_compliance(self):
        with patch('skills.clean_url_crawler.LinkExtractor') as mock_le:
            mock_le.return_value.extract.return_value = ["http://example.com"]
            mock_stream = io.BytesIO(b"<html><a href='http://example.com'>Test</a></html>")
            
            content = mock_stream.read().decode('utf-8')
            res = self.crawler.extract_and_clean(content)
            self.assertIsInstance(res, list)