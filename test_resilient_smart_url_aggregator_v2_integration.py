import unittest
import os
import shutil
from unittest.mock import patch
from skills.resilient_smart_url_aggregator_v2 import ResilientSmartUrlAggregatorV2
from skills.resilient_secure_clean_url_crawler_v2 import ResilientSecureCleanUrlCrawlerV2
from skills.smart_secure_compressed_sitemap_crawler_v2 import SmartSecureCompressedSitemapCrawlerV2
from skills.compressed_db_storage import CompressedDBStorage

class TestResilientSmartUrlAggregatorIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_path = "test_integration.db"
        cls.test_url = "https://example.com"
        cls.timeout = 10

        cls.crawler = ResilientSecureCleanUrlCrawlerV2(calls=10, period=60, raise_on_limit=True)
        cls.sitemap_crawler = SmartSecureCompressedSitemapCrawlerV2(
            db_path=cls.db_path,
            max_memory_mb=128,
            calls=10,
            period=60,
            raise_on_limit=True
        )
        cls.storage = CompressedDBStorage(db_path=cls.db_path)

        cls.aggregator = ResilientSmartUrlAggregatorV2(
            crawler=cls.crawler,
            sitemap_crawler=cls.sitemap_crawler,
            storage=cls.storage
        )

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)

    def test_full_aggregation_flow(self):
        # Проверка интеграции: агрегатор должен использовать компоненты для обработки URL
        # 1. Валидация через краулер
        is_valid = self.aggregator.validate_target(self.test_url, self.timeout)
        self.assertIsInstance(is_valid, bool)

        # 2. Агрегация данных (краулинг + сайтмап + сохранение)
        with patch.object(self.crawler, 'process_url', return_value=True), \
             patch.object(self.sitemap_crawler, 'crawl_and_clean', return_value=["https://example.com/item"]):
            result = self.aggregator.aggregate(self.test_url, self.timeout)
            self.assertTrue(result)

            # 3. Проверка сохранения в сжатую БД через сжатое хранилище
            stored_data = self.storage.get_compressed_data(self.test_url)
            self.assertIsNotNone(stored_data)

    def test_resilience_and_caching(self):
        # Проверка кэширования: повторный вызов должен вернуть данные из хранилища
        with patch.object(self.crawler, 'process_url', return_value=True), \
             patch.object(self.sitemap_crawler, 'crawl_and_clean', return_value=["https://example.com/item"]):
            self.aggregator.aggregate(self.test_url, self.timeout)
            cached_data = self.aggregator.get_cached_aggregation(self.test_url)
            self.assertIsNotNone(cached_data)

    def test_sitemap_integration(self):
        # Проверка специфичного взаимодействия с SmartSecureCompressedSitemapCrawlerV2
        with patch.object(self.sitemap_crawler, 'validate_sitemap', return_value=True):
            sitemap_valid = self.aggregator.check_sitemap_health(self.test_url, self.timeout)
            self.assertIsInstance(sitemap_valid, bool)
            self.assertTrue(sitemap_valid)

if __name__ == '__main__':
    unittest.main()
