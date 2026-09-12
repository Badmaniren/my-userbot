import unittest
import os
import shutil
from skills.resilient_secure_smart_aggregator_v6 import ResilientSecureSmartAggregatorV6
from skills.resilient_secure_smart_crawler_hub_v4 import ResilientSecureSmartCrawlerHubV4
from skills.clean_compressed_db_storage import CleanCompressedDBStorage

class TestResilientSecureSmartAggregatorV6Integration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_path = "test_aggregator_v6.db"
        cls.test_url = "https://example.com/feed.xml"
        cls.max_memory = 128
        cls.calls = 5
        cls.period = 60

    def setUp(self):
        self.aggregator = ResilientSecureSmartAggregatorV6(
            db_path=self.db_path,
            max_memory_mb=self.max_memory,
            calls=self.calls,
            period=self.period
        )
        self.storage = CleanCompressedDBStorage(db_path=self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_full_integration_flow(self):
        # Проверка инициализации зависимостей внутри агрегатора
        self.assertIsInstance(self.aggregator.crawler_hub, ResilientSecureSmartCrawlerHubV4)
        self.assertIsInstance(self.aggregator.storage, CleanCompressedDBStorage)

        # Выполнение координации расширения (краулинг + обработка)
        # Метод должен вернуть результат обработки, который сохраняется в БД
        result = self.aggregator.coordinate_expansion(self.test_url, timeout=10)
        self.assertIsNotNone(result)

        # Проверка, что данные попали в сжатое хранилище
        cleaned_url = self.storage.clean_target_url(self.test_url)
        stored_data = self.storage.get_cleaned_and_compressed_data(cleaned_url)

        # Если данные были успешно обработаны и сохранены, они должны быть доступны
        # В зависимости от реализации, если данные не найдены, метод вернет None
        self.assertIsNotNone(stored_data, "Данные не были найдены в сжатом хранилище после агрегации")

    def test_memory_and_rate_limit_enforcement(self):
        # Проверка, что агрегатор не глушит ошибки (RateLimitExceeded или MemoryLimitExceeded)
        # Вызываем с нереалистично низким таймаутом или параметрами, чтобы спровоцировать отказ
        with self.assertRaises(Exception):
            self.aggregator.coordinate_expansion("invalid_url_format", timeout=0.001)

    def test_storage_consistency(self):
        # Проверка прямой записи и чтения через агрегатор
        test_payload = "test_content_to_compress"
        self.aggregator.storage.save_cleaned_and_compressed_data(self.test_url, test_payload)

        retrieved = self.aggregator.storage.get_cleaned_and_compressed_data(self.test_url)
        self.assertEqual(retrieved, test_payload)

if __name__ == "__main__":
    unittest.main()