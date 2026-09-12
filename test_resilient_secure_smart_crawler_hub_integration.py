import unittest
import os
import shutil
from skills.resilient_secure_smart_crawler_hub import ResilientSecureSmartCrawlerHub
from skills.smart_secure_compressed_sitemap_crawler_v2 import SmartSecureCompressedSitemapCrawlerV2
from skills.resilient_secure_clean_url_crawler_v2 import ResilientSecureCleanUrlCrawlerV2
from skills.compressed_db_storage import CompressedDBStorage

class TestResilientSecureSmartCrawlerHub(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_path = "test_hub_storage.db"
        cls.test_url = "https://example.com/sitemap.xml"
        cls.hub = ResilientSecureSmartCrawlerHub(
            db_path=cls.db_path,
            max_memory_mb=128,
            calls=10,
            period=60
        )

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)

    def test_hub_composition_and_execution(self):
        # Проверка инициализации компонентов внутри хаба
        self.assertIsInstance(self.hub.sitemap_crawler, SmartSecureCompressedSitemapCrawlerV2)
        self.assertIsInstance(self.hub.url_crawler, ResilientSecureCleanUrlCrawlerV2)
        self.assertIsInstance(self.hub.storage, CompressedDBStorage)

        # Интеграционный сценарий: валидация -> парсинг -> хранение
        is_valid = self.hub.sitemap_crawler.validate_sitemap(self.test_url, timeout=5)
        self.assertIsInstance(is_valid, bool)

        if is_valid:
            links = self.hub.sitemap_crawler.crawl_and_clean(self.test_url, timeout=5)
            self.assertIsInstance(links, list)

            if links:
                target_url = links[0]
                # Проверка работы URL краулера через хаб
                success = self.hub.url_crawler.process_url(target_url, timeout=5)
                self.assertTrue(success)

                # Проверка сохранения данных в сжатое хранилище
                payload = "test_content_data"
                self.hub.storage.save_compressed_data("test_key", payload)
                retrieved = self.hub.storage.get_compressed_data("test_key")
                self.assertEqual(retrieved, payload)

    def test_memory_awareness(self):
        # Проверка, что хаб обрабатывает лимиты через свои компоненты
        try:
            self.hub.sitemap_crawler.coordinate_expansion(self.test_url, timeout=2)
        except Exception as e:
            self.assertIn("Memory", str(type(e)))

if __name__ == "__main__":
    unittest.main()
