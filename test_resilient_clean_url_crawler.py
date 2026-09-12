import unittest
from unittest.mock import patch, MagicMock
import io
from skills.resilient_clean_url_crawler import ResilientCleanUrlCrawler, ResilientCleanUrlCrawlerError


class TestResilientCleanUrlCrawler(unittest.TestCase):

    def setUp(self):
        self.crawler = ResilientCleanUrlCrawler(calls=10, period=1.0, raise_on_limit=True)

    def test_init_defaults(self):
        crawler = ResilientCleanUrlCrawler()
        self.assertIsNotNone(crawler)

    @patch('skills.resilient_clean_url_crawler.rate_limiter.RateLimiter.acquire')
    @patch('skills.resilient_clean_url_crawler.clean_url_crawler.CleanUrlCrawler.process_url')
    def test_process_url_success(self, mock_process_url, mock_acquire):
        mock_process_url.return_value = True
        result = self.crawler.process_url("https://example.com/path?utm_source=test", 5.0)
        self.assertTrue(result)
        mock_acquire.assert_called_once()
        mock_process_url.assert_called_once()

    @patch('skills.resilient_clean_url_crawler.rate_limiter.RateLimiter.acquire')
    @patch('skills.resilient_clean_url_crawler.clean_url_crawler.CleanUrlCrawler.process_url')
    def test_process_url_failure(self, mock_process_url, mock_acquire):
        mock_process_url.return_value = False
        result = self.crawler.process_url("https://example.com/invalid", 5.0)
        self.assertFalse(result)

    @patch('skills.resilient_clean_url_crawler.rate_limiter.RateLimiter.acquire')
    @patch('skills.resilient_clean_url_crawler.clean_url_crawler.CleanUrlCrawler.validate_crawled_link')
    def test_validate_crawled_link_success(self, mock_validate, mock_acquire):
        mock_validate.return_value = True
        result = self.crawler.validate_crawled_link("https://example.com/page", 3.0)
        self.assertTrue(result)
        mock_acquire.assert_called_once()
        mock_validate.assert_called_once()

    @patch('skills.resilient_clean_url_crawler.rate_limiter.RateLimiter.acquire')
    @patch('skills.resilient_clean_url_crawler.clean_url_crawler.CleanUrlCrawler.validate_crawled_link')
    def test_validate_crawled_link_false(self, mock_validate, mock_acquire):
        mock_validate.return_value = False
        result = self.crawler.validate_crawled_link("https://example.com/broken", 3.0)
        self.assertFalse(result)

    @patch('skills.resilient_clean_url_crawler.rate_limiter.RateLimiter.acquire')
    @patch('skills.resilient_clean_url_crawler.clean_url_crawler.CleanUrlCrawler.extract_and_clean')
    def test_extract_and_clean_success(self, mock_extract, mock_acquire):
        mock_extract.return_value = ["https://example.com/clean1", "https://example.com/clean2"]
        html_content = "<html><body><a href='/clean1'>Link</a></body></html>"
        result = self.crawler.extract_and_clean(html_content)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        mock_acquire.assert_called_once()

    @patch('skills.resilient_clean_url_crawler.rate_limiter.RateLimiter.acquire')
    @patch('skills.resilient_clean_url_crawler.clean_url_crawler.CleanUrlCrawler.process_url')
    def test_process_url_exception_handling(self, mock_process_url, mock_acquire):
        mock_process_url.side_effect = Exception("Network error")
        result = self.crawler.process_url("https://example.com/error", 2.0)
        self.assertFalse(result)

    @patch('skills.resilient_clean_url_crawler.rate_limiter.RateLimiter.acquire')
    @patch('skills.resilient_clean_url_crawler.clean_url_crawler.CleanUrlCrawler.validate_crawled_link')
    def test_validate_crawled_link_exception_handling(self, mock_validate, mock_acquire):
        mock_validate.side_effect = Exception("Timeout error")
        result = self.crawler.validate_crawled_link("https://example.com/timeout", 2.0)
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()