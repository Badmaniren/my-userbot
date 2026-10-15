import unittest
from unittest.mock import patch, MagicMock
import urllib.error

from skills.smart_crawler import (
    SmartCrawler,
    CrawlerError,
    RateLimitExceeded,
    MemoryLimitExceeded,
    JsonExtractorError
)

class TestSmartCrawlerInquisition(unittest.TestCase):
    def setUp(self):
        self.crawler = SmartCrawler()

    @patch('skills.smart_crawler.HeadersRotator.rotate_headers')
    @patch('skills.smart_crawler.RateLimiter.acquire')
    @patch('skills.smart_crawler.cached_ping.ping_and_cache')
    @patch('skills.smart_crawler.link_extractor.LinkExtractor.extract')
    def test_expansion_protocol_success(self, mock_extract, mock_ping, mock_acquire, mock_rotate):
        mock_rotate.return_value = {'User-Agent': 'InquisitorBot/1.0'}
        mock_ping.return_value = True
        mock_extract.return_value = ['http://target.com/data1', 'http://target.com/data2']

        result = self.crawler.coordinate_expansion('http://target.com', timeout=5)
        
        mock_acquire.assert_called_once()
        mock_ping.assert_called_once_with('http://target.com', timeout=5)
        self.assertEqual(len(result), 2)
        self.assertIn('http://target.com/data1', result)

    @patch('skills.smart_crawler.RateLimiter.acquire')
    def test_heresy_rate_limit_exceeded(self, mock_acquire):
        mock_acquire.side_effect = RateLimitExceeded("Rate limit breached. HERESY.")

        with self.assertRaises(RateLimitExceeded):
            self.crawler.coordinate_expansion('http://target.com', timeout=5)

    @patch('skills.smart_crawler.HeadersRotator.rotate_headers')
    @patch('skills.smart_crawler.RateLimiter.acquire')
    @patch('skills.smart_crawler.cached_ping.ping_and_cache')
    def test_heresy_endpoint_dead(self, mock_ping, mock_acquire, mock_rotate):
        mock_rotate.return_value = {'User-Agent': 'InquisitorBot/1.0'}
        mock_ping.return_value = False

        with self.assertRaises(CrawlerError) as ctx:
            self.crawler.coordinate_expansion('http://dead-target.com', timeout=5)
        self.assertIn('Target unresponsive', str(ctx.exception))

    @patch('skills.smart_crawler.HeadersRotator.rotate_headers')
    @patch('skills.smart_crawler.RateLimiter.acquire')
    @patch('skills.smart_crawler.cached_ping.ping_and_cache')
    def test_heresy_http_error_500(self, mock_ping, mock_acquire, mock_rotate):
        mock_rotate.return_value = {'User-Agent': 'InquisitorBot/1.0'}
        mock_ping.side_effect = urllib.error.HTTPError('http://target.com', 500, 'Internal Server Error', {}, None)

        with self.assertRaises(urllib.error.HTTPError):
            self.crawler.coordinate_expansion('http://target.com', timeout=5)

    @patch('skills.smart_crawler.HeadersRotator.rotate_headers')
    @patch('skills.smart_crawler.RateLimiter.acquire')
    @patch('skills.smart_crawler.cached_ping.ping_and_cache')
    @patch('skills.smart_crawler.link_extractor.LinkExtractor.extract')
    def test_heresy_memory_limit_exceeded(self, mock_extract, mock_ping, mock_acquire, mock_rotate):
        mock_rotate.return_value = {'User-Agent': 'InquisitorBot/1.0'}
        mock_ping.return_value = True
        mock_extract.side_effect = MemoryLimitExceeded("Memory threshold obliterated.")

        with self.assertRaises(MemoryLimitExceeded):
            self.crawler.coordinate_expansion('http://target.com', timeout=5)

    @patch('skills.smart_crawler.HeadersRotator.rotate_headers')
    @patch('skills.smart_crawler.RateLimiter.acquire')
    @patch('skills.smart_crawler.cached_ping.ping_and_cache')
    @patch('skills.smart_crawler.link_extractor.LinkExtractor.extract')
    def test_heresy_malformed_json_extraction(self, mock_extract, mock_ping, mock_acquire, mock_rotate):
        mock_rotate.return_value = {'User-Agent': 'InquisitorBot/1.0'}
        mock_ping.return_value = True
        mock_extract.side_effect = JsonExtractorError("Corrupted data syntax.")

        with self.assertRaises(JsonExtractorError):
            self.crawler.coordinate_expansion('http://target.com', timeout=5)

    @patch('skills.smart_crawler.HeadersRotator.rotate_headers')
    @patch('skills.smart_crawler.RateLimiter.acquire')
    @patch('skills.smart_crawler.cached_ping.ping_and_cache')
    @patch('skills.smart_crawler.link_extractor.LinkExtractor.extract')
    def test_edge_case_empty_extraction(self, mock_extract, mock_ping, mock_acquire, mock_rotate):
        mock_rotate.return_value = {'User-Agent': 'InquisitorBot/1.0'}
        mock_ping.return_value = True
        mock_extract.return_value = []

        result = self.crawler.coordinate_expansion('http://target.com', timeout=5)
        self.assertEqual(result, [])

    @patch('skills.smart_crawler.HeadersRotator.rotate_headers')
    @patch('skills.smart_crawler.RateLimiter.acquire')
    @patch('skills.smart_crawler.cached_ping.ping_and_cache')
    def test_heresy_timeout_anomaly(self, mock_ping, mock_acquire, mock_rotate):
        mock_rotate.return_value = {'User-Agent': 'InquisitorBot/1.0'}
        mock_ping.side_effect = TimeoutError("Target execution timed out.")

        with self.assertRaises(TimeoutError):
            self.crawler.coordinate_expansion('http://target.com', timeout=1)

    def test_inquisitorial_sanitization_failure(self):
        with self.assertRaises(TypeError):
            self.crawler.coordinate_expansion(None, timeout=5)