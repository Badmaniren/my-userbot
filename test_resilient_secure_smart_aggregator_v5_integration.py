import unittest
import os
import shutil
from skills.resilient_secure_smart_aggregator_v5 import ResilientSecureSmartAggregatorV5
from skills.resilient_secure_smart_crawler_hub_v4 import ResilientSecureSmartCrawlerHubV4
from skills.smart_secure_compressed_rss_crawler import SmartSecureCompressedRSSCrawler
from skills.smart_secure_compressed_sitemap_crawler_v2 import SmartSecureCompressedSitemapCrawlerV2

class TestResilientSecureSmartAggregatorV5Integration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_path = "test_aggregator_db.sqlite"
        cls.test_url = "https://example.com"
        cls.timeout = 10
        cls.max_memory = 50
        cls.calls = 5
        cls.period = 60

        cls.hub = ResilientSecureSmartCrawlerHubV4(cls.db_path, cls.max_memory, cls.calls, cls.period, True)
        cls.rss_crawler = SmartSecureCompressedRSSCrawler(cls.db_path, cls.max_memory, cls.calls, cls.period, True)
        cls.sitemap_crawler = SmartSecureCompressedSitemapCrawlerV2(cls.db_path, cls.max_memory, cls.calls, cls.period, True)

        cls.aggregator = ResilientSecureSmartAggregatorV5(
            hub=cls.hub,
            rss_crawler=cls.rss_crawler,
            sitemap_crawler=cls.sitemap_crawler
        )

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)

    def test_unified_data_expansion_flow(self):
        """
        Интеграционный тест: проверка цепочки вызовов между хабом, RSS и Sitemap краулерами.
        """
        # 1. Проверка валидации заголовков через хаб
        is_valid = self.aggregator.validate_target(self.test_url, self.timeout)
        self.assertIsInstance(is_valid, bool)

        # 2. Выполнение комплексного сбора данных
        # Ожидаем, что агрегатор вызовет методы всех трех зависимостей
        result = self.aggregator.run_unified_expansion(self.test_url, self.timeout)

        self.assertIn('rss_data', result)
        self.assertIn('sitemap_data', result)
        self.assertIn('hub_status', result)

    def test_resilience_and_caching(self):
        """
        Проверка того, что агрегатор корректно использует кэшированные данные из RSS и Sitemap модулей.
        """
        # Заполняем кэш через RSS краулер
        self.rss_crawler.archive_feed(self.test_url, self.timeout, force_refresh=True)

        # Запрашиваем через агрегатор
        cached_rss = self.aggregator.get_cached_rss_content(self.test_url)
        self.assertIsNotNone(cached_rss)
        self.assertIsInstance(cached_rss, str)

    def test_sitemap_processing_integration(self):
        """
        Проверка интеграции с парсером Sitemap V2.
        """
        is_sitemap_valid = self.aggregator.verify_sitemap_structure(self.test_url, self.timeout)
        self.assertIsInstance(is_sitemap_valid, bool)

if __name__ == '__main__':
    unittest.main()