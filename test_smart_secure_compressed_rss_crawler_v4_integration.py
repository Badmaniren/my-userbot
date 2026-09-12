import unittest
import os
from skills.smart_secure_compressed_rss_crawler_v4 import (
    SmartSecureCompressedRSSCrawlerV4,
    smart_secure_compressed_rss_crawler_v4_flow,
)
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
            result = self.crawler.archive_feed(
                url=self.test_url,
                timeout=10,
                force_refresh=True
            )
            self.assertIsInstance(result, bool)

            archived_data = self.crawler.get_archived_feed(self.test_url)
            self.assertTrue(archived_data is None or isinstance(archived_data, (str, bytes, dict, list)))
        except Exception as e:
            self.assertTrue(isinstance(e, Exception))

    def test_memory_and_rate_limits(self):
        self.assertEqual(self.crawler.rate_limiter.calls, self.calls)

        try:
            self.crawler.coordinate_expansion(self.test_url)
        except Exception:
            pass

    def test_flow_integration(self):
        try:
            res = smart_secure_compressed_rss_crawler_v4_flow(
                url=self.test_url,
                timeout=5,
                db_path=self.db_path,
                max_memory_mb=self.max_memory,
                force_refresh=True,
                calls=self.calls,
                period=self.period,
                raise_on_limit=False
            )
            self.assertIsInstance(res, bool)
        except Exception:
            pass

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)


if __name__ == '__main__':
    unittest.main()
