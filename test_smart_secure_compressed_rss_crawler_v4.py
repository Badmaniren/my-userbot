import unittest
from unittest.mock import MagicMock, patch
import io
from skills.smart_secure_compressed_rss_crawler_v4 import SmartSecureCompressedRSSCrawlerV4
from skills.resilient_secure_clean_compressed_rss_archiver import SecureCleanCompressedRSSArchiverError
from skills.memory_profiler import MemoryLimitExceeded
from skills.rate_limiter import RateLimitExceeded

class TestSmartSecureCompressedRSSCrawlerV4(unittest.TestCase):

    def setUp(self):
        self.db_path = "test_db.sqlite"
        self.max_memory = 128
        self.crawler = SmartSecureCompressedRSSCrawlerV4(
            db_path=self.db_path,
            max_memory_mb=self.max_memory,
            calls=10,
            period=60
        )
        self.test_url = "https://example.com/rss"

    def test_archive_feed_success(self):
        with patch('skills.smart_secure_compressed_rss_crawler_v4.resilient_secure_clean_compressed_rss_archiver.SecureCleanCompressedRSSArchiver') as mock_archiver:
            instance = mock_archiver.return_value
            instance.archive_feed.return_value = True

            result = self.crawler.archive_feed(self.test_url, timeout=10, force_refresh=False)
            self.assertTrue(result)
            instance.archive_feed.assert_called_once_with(self.test_url, 10, False)

    def test_archive_feed_memory_limit_exceeded(self):
        with patch('skills.smart_secure_compressed_rss_crawler_v4.resilient_secure_clean_compressed_rss_archiver.SecureCleanCompressedRSSArchiver') as mock_archiver:
            instance = mock_archiver.return_value
            instance.archive_feed.side_effect = MemoryLimitExceeded()

            with self.assertRaises(MemoryLimitExceeded):
                self.crawler.archive_feed(self.test_url, 10, False)

    def test_archive_feed_rate_limit_exceeded(self):
        with patch('skills.smart_secure_compressed_rss_crawler_v4.resilient_secure_clean_compressed_rss_archiver.SecureCleanCompressedRSSArchiver') as mock_archiver:
            instance = mock_archiver.return_value
            instance.archive_feed.side_effect = RateLimitExceeded()

            with self.assertRaises(RateLimitExceeded):
                self.crawler.archive_feed(self.test_url, 10, False)

    def test_get_archived_feed_valid(self):
        expected_data = "compressed_data_blob"
        with patch('skills.smart_secure_compressed_rss_crawler_v4.resilient_secure_clean_compressed_rss_archiver.SecureCleanCompressedRSSArchiver') as mock_archiver:
            instance = mock_archiver.return_value
            instance.get_archived_feed.return_value = expected_data

            result = self.crawler.get_archived_feed(self.test_url)
            self.assertEqual(result, expected_data)

    def test_coordinate_expansion_logic(self):
        with patch('skills.smart_secure_compressed_rss_crawler_v4.memory_profiler.assert_memory_limit') as mock_mem:
            with patch('skills.smart_secure_compressed_rss_crawler_v4.rate_limiter.RateLimiter') as mock_rate:
                # Проверка инициализации и вызова координации
                res = self.crawler.coordinate_expansion(self.test_url)
                self.assertTrue(res)
                mock_mem.assert_called()

    def test_integration_flow_failure(self):
        with patch('skills.smart_secure_compressed_rss_crawler_v4.resilient_secure_clean_compressed_rss_archiver.SecureCleanCompressedRSSArchiver') as mock_archiver:
            instance = mock_archiver.return_value
            instance.archive_feed.side_effect = SecureCleanCompressedRSSArchiverError("Critical Failure")

            with self.assertRaises(SecureCleanCompressedRSSArchiverError):
                self.crawler.archive_feed(self.test_url, 5, True)

    def test_memory_profiling_decorator_usage(self):
        # Проверка, что метод профилируется
        with patch('skills.smart_secure_compressed_rss_crawler_v4.memory_profiler.profile_memory') as mock_profile:
            self.crawler.archive_feed(self.test_url, 10, False)
            self.assertTrue(mock_profile.called)

if __name__ == '__main__':
    unittest.main()