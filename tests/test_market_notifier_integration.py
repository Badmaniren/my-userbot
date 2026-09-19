import unittest
import os
import uuid
import random
from skills.market_notifier import MarketNotifier


class TestMarketNotifierIntegration(unittest.TestCase):
    def setUp(self):
        self.test_filename = f"test_market_data_{uuid.uuid4().hex}.json"
        self.notifier = MarketNotifier(self.test_filename)
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.random_price = round(random.uniform(10.0, 1000.0), 2)

    def tearDown(self):
        if os.path.exists(self.test_filename):
            try:
                os.remove(self.test_filename)
            except OSError:
                pass

    def test_process_and_notify_and_get_historical_data_integration(self):
        success = self.notifier.process_and_notify(
            symbol=self.symbol, 
            price=self.random_price
        )
        
        self.assertTrue(success, "Метод process_and_notify должен вернуть True при успешном сохранении")
        self.assertTrue(os.path.exists(self.test_filename), "Интеграционный тест требует реального создания файла хранилища")

        historical_data = self.notifier.get_historical_data()
        
        self.assertIsInstance(historical_data, (list, dict), "Исторические данные должны быть возвращены в виде коллекции")
        
        found = False
        if isinstance(historical_data, list):
            for item in historical_data:
                if item.get("symbol") == self.symbol and item.get("price") == self.random_price:
                    found = True
                    break
        elif isinstance(historical_data, dict):
            if self.symbol in historical_data:
                found = True

        self.assertTrue(
            found, 
            f"Сохраненные данные для символа {self.symbol} с ценой {self.random_price} не найдены через метод чтения истории"
        )


if __name__ == "__main__":
    unittest.main()