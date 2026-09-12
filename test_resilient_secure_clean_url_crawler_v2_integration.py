import unittest
from unittest.mock import patch
from skills.resilient_secure_clean_url_crawler_v2 import ResilientSecureCleanUrlCrawlerV2
from skills.url_cleaner import UrlCleanerError

class TestResilientSecureCleanUrlCrawlerV2Integration(unittest.TestCase):

    def setUp(self):
        self.crawler = ResilientSecureCleanUrlCrawlerV2(
            calls=10,
            period=1.0,
            raise_on_limit=True
        )
        self.test_url = "https://Example.com/path?utm_source=test&ref=123"

    @patch('skills.resilient_clean_url_crawler.ResilientCleanUrlCrawler.process_url')
    def test_process_url_integration(self, mock_process):
        mock_process.return_value = True
        result = self.crawler.process_url(self.test_url, timeout=5)
        self.assertIsInstance(result, bool)
        self.assertTrue(result)
        mock_process.assert_called_once()

    @patch('skills.resilient_clean_url_crawler.ResilientCleanUrlCrawler.validate_crawled_link')
    def test_validate_crawled_link_integration(self, mock_validate):
        mock_validate.return_value = True
        result = self.crawler.validate_crawled_link(self.test_url, timeout=5)
        self.assertIsInstance(result, bool)
        self.assertTrue(result)
        mock_validate.assert_called_once()

    @patch('skills.resilient_clean_url_crawler.ResilientCleanUrlCrawler.extract_and_clean')
    def test_extract_and_clean_integration(self, mock_extract):
        sample_html = '<html><a href="https://Example.com/page?utm_campaign=summer">Link</a></html>'
        cleaned_links = ["https://example.com/page"]
        mock_extract.return_value = cleaned_links
        
        result = self.crawler.extract_and_clean(sample_html)
        self.assertIsInstance(result, list)
        self.assertEqual(result, cleaned_links)
        mock_extract.assert_called_once_with(sample_html)

    def test_url_cleaner_composition(self):
        from skills.url_cleaner import clean_url
        cleaned = clean_url(self.test_url)
        self.assertIsInstance(cleaned, str)
        self.assertNotIn("utm_source", cleaned)
        self.assertEqual(cleaned, "https://example.com/path?ref=123")

if __name__ == '__main__':
    unittest.main()