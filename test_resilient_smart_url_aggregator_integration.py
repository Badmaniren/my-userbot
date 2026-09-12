import unittest
import os
import tempfile
from skills.resilient_smart_url_aggregator import ResilientSmartUrlAggregator
from skills.resilient_secure_clean_url_crawler_v2 import ResilientSecureCleanUrlCrawlerV2
from skills.smart_secure_compressed_sitemap_crawler_v2 import SmartSecureCompressedSitemapCrawlerV2

class TestResilientSmartUrlAggregatorIntegration(unittest.TestCase):
    def setUp(self):
        self.db_path = tempfile.mktemp(suffix=".db")
        self.aggregator = ResilientSmartUrlAggregator(
            db_path=self.db_path,
            max_memory_mb=128,
            calls=10,
            period=60
        )
        self.url = "https://example.com/sitemap.xml"
        self.timeout = 10

    def test_aggregation_flow(self):
        # Проверка инициализации зависимостей внутри агрегатора
        self.assertIsInstance(self.aggregator.url_crawler, ResilientSecureCleanUrlCrawlerV2)
        self.assertIsInstance(self.aggregator.sitemap_crawler, SmartSecureCompressedSitemapCrawlerV2)

        # Интеграционный тест: выполнение полного цикла расширения
        # Метод coordinate_expansion должен использовать оба навыка для обработки URL
        result = self.aggregator.coordinate_expansion(self.url, self.timeout)

        # Проверка структуры результата (ожидаем список обработанных ссылок)
        self.assertIsInstance(result, list)

        # Проверка валидации через sitemap_crawler
        is_valid = self.aggregator.sitemap_crawler.validate_sitemap(self.url, self.timeout)
        self.assertIsInstance(is_valid, bool)

        # Проверка очистки URL через url_crawler
        cleaned_url = self.aggregator.url_crawler.clean_url(self.url)
        self.assertIsInstance(cleaned_url, str)
        self.assertTrue(len(cleaned_url) > 0)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

if __name__ == "__main__":
    unittest.main()