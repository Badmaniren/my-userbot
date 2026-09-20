import unittest
import os
import uuid
import random
from skills.market_threshold_checker import MarketThresholdChecker
from skills.market_parser import MarketParser
from skills.db_storage import MarketParser as DBStorageMarketParser

class TestMarketThresholdCheckerIntegration(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.test_url = f"http://example.com/price/{uuid.uuid4().hex}"
        self.threshold = round(random.uniform(10.0, 100.0), 2)

        self.checker = MarketThresholdChecker(
            storage_file=self.storage_file,
            threshold=self.threshold
        )

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_threshold_checker_composition_and_alert(self):
        random_price = round(self.threshold + random.uniform(1.0, 50.0), 2)

        self.assertTrue(
            hasattr(self.checker, 'parser') or hasattr(self.checker, 'storage'),
            "Модуль MarketThresholdChecker должен использовать компоненты парсера и хранилища"
        )

        alert_result = self.checker.check_and_alert(self.symbol, self.test_url, random_price)

        self.assertIsNotNone(alert_result, "Интеграционный метод должен возвращать результат проверки")

        self.assertTrue(
            os.path.exists(self.storage_file),
            "Интеграция должна создавать или использовать файл хранилища для записи данных"
        )

        storage_instance = DBStorageMarketParser(self.storage_file)
        loaded_data = storage_instance.load_data(self.storage_file)

        self.assertIn(self.symbol, loaded_data, "Данные должны быть реально сохранены в хранилище в ходе интеграционного вызова")

if __name__ == '__main__':
    unittest.main()