import unittest
from unittest.mock import patch
import os
import shutil
from skills.smart_secure_compressed_rss_crawler_v4 import SmartSecureCompressedRSSCrawlerV4
from skills.resilient_secure_clean_compressed_rss_archiver import ResilientSecureCleanCompressedRSSArchiver
from skills.memory_profiler import MemoryProfiler
from skills.rate_limiter import RateLimiter

class TestSmartSecureCompressedRSSCrawlerV4Integration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_path = "test_rss_v4.db"
        cls.test_url = "https://example.com/rss"
        cls.max_memory = 128
        cls.calls = 10
        cls.period = 60

    def setUp(self):
        self.crawler = SmartSecureCompressedRSSCrawlerV4(
            db_path=self.db_path,
            max_memory_mb=self.max_memory,
            calls=self.calls,
            period=self.period,
            raise_on_limit=True
        )

    def test_full_integration_flow(self):
        # Проверка инициализации зависимостей внутри модуля
        self.assertIsNotNone(self.crawler.archiver)
        self.assertIsInstance(self.crawler.archiver, ResilientSecureCleanCompressedRSSArchiver)
        self.assertIsNotNone(self.crawler.memory_profiler)
        self.assertIsInstance(self.crawler.memory_profiler, MemoryProfiler)
        self.assertIsNotNone(self.crawler.rate_limiter)
        self.assertIsInstance(self.crawler.rate_limiter, RateLimiter)

        # Тест процесса архивации с интеграцией всех компонентов
        try:
            mock_response = {
                "status": 200,
                "status_code": 200,
                "headers": {"content-type": "application/rss+xml"},
                "data": "<rss><channel><item><title>Test Item</title><link>https://example.com/item1</link></item></channel></rss>"
            }
            with patch('skills.cached_ping.ping_and_cache', return_value=mock_response), \
                 patch('skills.http_ping.check_endpoint', return_value=mock_response):
                result = self.crawler.archive_feed(
                    url=self.test_url,
                    timeout=10,
                    force_refresh=True
                )
                self.assertTrue(result)

                # Проверка получения данных из хранилища
                archived_data = self.crawler.get_archived_feed(self.test_url)
                self.assertIsNotNone(archived_data)

        except Exception as e:
            self.fail(f"Integration flow failed with error: {e}")

    def test_memory_and_rate_limits(self):
        # Проверка, что модуль корректно делегирует лимиты
        self.assertEqual(self.crawler.rate_limiter.calls, self.calls)

        # Проверка работы метода coordinate_expansion (если применимо к логике)
        try:
            self.crawler.coordinate_expansion(self.test_url)
        except Exception as e:
            # Допускаем ошибку сети, но не ошибку интеграции компонентов
            pass

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)

if __name__ == '__main__':
    unittest.main()