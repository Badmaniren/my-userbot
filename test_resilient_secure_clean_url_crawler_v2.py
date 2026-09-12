import unittest
from unittest.mock import patch, MagicMock
import io
import requests

from skills.resilient_secure_clean_url_crawler_v2 import (
    ResilientSecureCleanUrlCrawlerV2,
    ResilientSecureCleanUrlCrawlerV2Error
)

class TestResilientSecureCleanUrlCrawlerV2(unittest.TestCase):

    def setUp(self):
        self.crawler = ResilientSecureCleanUrlCrawlerV2(
            calls=10,
            period=1.0,
            raise_on_limit=True
        )

    def test_init_defaults(self):
        crawler = ResilientSecureCleanUrlCrawlerV2()
        self.assertIsInstance(crawler, ResilientSecureCleanUrlCrawlerV2)

    def test_clean_url_composition(self):
        with patch('skills.url_cleaner.clean_url') as mock_clean:
            mock_clean.return_value = "https://example.com/clean"
            result = self.crawler.clean_url("https://example.com/?utm_source=test")
            self.assertEqual(result, "https://example.com/clean")
            mock_clean.assert_called_once_with("https://example.com/?utm_source=test")

    def test_validate_crawled_link_success(self):
        with patch('skills.resilient_clean_url_crawler.ResilientCleanUrlCrawler.validate_crawled_link') as mock_validate:
            mock_validate.return_value = True
            res = self.crawler.validate_crawled_link("https://example.com", 5)
            self.assertTrue(res)

    def test_validate_crawled_link_failure(self):
        with patch('skills.resilient_clean_url_crawler.ResilientCleanUrlCrawler.validate_crawled_link') as mock_validate:
            mock_validate.return_value = False
            res = self.crawler.validate_crawled_link("https://example.com", 5)
            self.assertFalse(res)

    def test_validate_crawled_link_exception_handling(self):
        with patch('skills.resilient_clean_url_crawler.ResilientCleanUrlCrawler.validate_crawled_link') as mock_validate:
            mock_validate.side_effect = Exception("Network down")
            res = self.crawler.validate_crawled_link("https://example.com", 5)
            self.assertFalse(res)

    def test_extract_and_clean(self):
        html = '<a href="https://example.com/?utm_campaign=1">Link</a>'
        with patch('skills.resilient_clean_url_crawler.ResilientCleanUrlCrawler.extract_and_clean') as mock_extract:
            mock_extract.return_value = ["https://example.com/"]
            links = self.crawler.extract_and_clean(html)
            self.assertIsInstance(links, list)
            self.assertEqual(links, ["https://example.com/"])

    def test_process_url_success(self):
        with patch('skills.resilient_clean_url_crawler.ResilientCleanUrlCrawler.process_url') as mock_process:
            mock_process.return_value = True
            res = self.crawler.process_url("https://example.com", 5)
            self.assertTrue(res)

    def test_process_url_failure_returns_false(self):
        with patch('skills.resilient_clean_url_crawler.ResilientCleanUrlCrawler.process_url') as mock_process:
            mock_process.side_effect = requests.RequestException("Timeout")
            res = self.crawler.process_url("https://example.com", 5)
            self.assertFalse(res)

    def test_process_url_raises_custom_error_when_configured(self):
        crawler_strict = ResilientSecureCleanUrlCrawlerV2(raise_on_limit=False)
        with patch('skills.resilient_clean_url_crawler.ResilientCleanUrlCrawler.process_url') as mock_process:
            mock_process.side_effect = Exception("Fatal error")
            with self.assertRaises(ResilientSecureCleanUrlCrawlerV2Error):
                crawler_strict.process_url("https://example.com", 5)

    def test_rate_limiter_integration(self):
        with patch('skills.rate_limiter.RateLimiter.acquire') as mock_acquire:
            mock_acquire.return_value = True
            res = self.crawler.process_url("https://example.com", 5)
            mock_acquire.assert_called_once()

    def test_io_bytes_handling_in_requests(self):
        fake_response = MagicMock()
        fake_response.content = b'<html></html>'
        fake_response.raw = io.BytesIO(b'<html></html>')
        
        with patch('requests.get', return_value=fake_response) as mock_get:
            res = self.crawler.process_url("https://example.com", 5)
            self.assertIsInstance(res, bool)


if __name__ == '__main__':
    unittest.main()