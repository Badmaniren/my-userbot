import unittest
import os
import uuid
import random
from skills.market_telegram_pipeline import run_market_telegram_pipeline
from skills.market_parser import MarketParser
from skills.db_storage import load_data

class TestMarketTelegramPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.storage_filename = f"test_market_data_{self.random_suffix}.json"
        self.test_symbol = f"SYM_{self.random_suffix}"
        self.test_price = round(random.uniform(10.0, 1000.0), 2)
        self.test_url = f"https://example.com/api/{self.random_suffix}"
        self.chat_id = f"@{self.random_suffix}_channel"

    def tearDown(self):
        if os.path.exists(self.storage_filename):
            try:
                os.remove(self.storage_filename)
            except OSError:
                pass

    def test_pipeline_integration_flow(self):
        parser = MarketParser(storage_file=self.storage_filename)
        parser.fetch_and_store(symbol=self.test_symbol, price=self.test_price)

        self.assertTrue(os.path.exists(self.storage_filename), "Файл хранилища должен быть создан")

        loaded_data = load_data(self.storage_filename)
        self.assertIn(self.test_symbol, loaded_data, "Сохраненный символ должен присутствовать в данных")
        self.assertEqual(loaded_data[self.test_symbol], self.test_price, "Цена в хранилище должна совпадать с исходной")

        pipeline_result = run_market_telegram_pipeline(
            storage_file=self.storage_filename,
            symbol=self.test_symbol,
            chat_id=self.chat_id
        )

        self.assertIsInstance(pipeline_result, dict, "Результат работы пайплайна должен быть словарем")
        self.assertIn("status", pipeline_result, "Результат должен содержать статус выполнения")
        self.assertEqual(pipeline_result["status"], "success", "Статус выполнения пайплайна должен быть успешным")
        self.assertEqual(pipeline_result.get("sent_symbol"), self.test_symbol, "Пайплайн должен обработать правильный символ")
        self.assertEqual(pipeline_result.get("sent_price"), self.test_price, "Пайплайн должен передать корректную цену")

if __name__ == "__main__":
    unittest.main()