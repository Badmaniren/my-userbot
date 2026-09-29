import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_monitor import start_new

class TestMarketPortfolioMonitorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_storage"
        if not os.path.exists(self.test_dir):
            os.makedirs(self.test_dir)
        
        self.storage_file = os.path.join(self.test_dir, f"test_data_{uuid.uuid4().hex}.json")
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.url = f"https://api.test.com/{uuid.uuid4()}"
        self.telegram_token = f"bot{random.randint(100000, 999999)}:ABC-{uuid.uuid4()}"
        self.chat_id = str(random.randint(100000000, 999999999))

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_run_pipeline_integration(self):
        # Выполнение реального конвейера
        result = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )

        # Проверка возвращаемого значения
        self.assertTrue(result, "Pipeline should return True on successful execution")

        # Проверка создания и записи файла
        self.assertTrue(os.path.exists(self.storage_file), "Storage file was not created")
        
        with open(self.storage_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        # Проверка целостности данных
        self.assertIn(self.symbol, data, "Symbol not found in storage file")
        self.assertIsInstance(data[self.symbol], (int, float), "Price data should be numeric")

    def test_pipeline_data_persistence(self):
        # Проверка накопления данных при повторном вызове
        first_symbol = f"SYM_{uuid.uuid4().hex[:5]}"
        second_symbol = f"SYM_{uuid.uuid4().hex[:5]}"
        
        start_new(first_symbol, self.url, self.telegram_token, self.chat_id, self.storage_file)
        start_new(second_symbol, self.url, self.telegram_token, self.chat_id, self.storage_file)
        
        with open(self.storage_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        self.assertIn(first_symbol, data)
        self.assertIn(second_symbol, data)
        self.assertEqual(len(data), 2, "Storage should contain both symbols")

if __name__ == "__main__":
    unittest.main()