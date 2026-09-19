import unittest
import os
import uuid
import random
from skills.market_notifier import MarketNotifier
from skills.market_parser import MarketParser
from skills.db_storage import db_storage

class TestMarketNotifierIntegration(unittest.TestCase):

    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.storage_filename = f"test_market_storage_{self.random_suffix}.json"
        self.notifier = MarketNotifier(storage_file=self.storage_filename)

    def tearDown(self):
        if os.path.exists(self.storage_filename):
            try:
                os.remove(self.storage_filename)
            except OSError:
                pass

    def test_market_notifier_end_to_end_flow(self):
        symbol = f"COIN_{uuid.uuid4().hex[:6].upper()}"
        random_price = round(random.uniform(10.0, 50000.0), 2)
        test_url = f"https://example.com/market/{uuid.uuid4().hex[:6]}"

        result = self.notifier.process_and_notify(symbol=symbol, price=random_price, url=test_url)

        self.assertTrue(result, "Комбайн должен успешно обработать и отправить уведомление")
        self.assertTrue(os.path.exists(self.storage_filename), "Файл локального хранилища должен быть создан")

        loaded_data = self.notifier.parser.load_data(self.storage_filename)
        self.assertIn(symbol, loaded_data, "Символ должен быть сохранен в хранилище через реальный навык парсера/БД")
        self.assertEqual(loaded_data[symbol], random_price, "Сохраненное значение цены должно совпадать со сгенерированным")

if __name__ == '__main__':
    unittest.main()