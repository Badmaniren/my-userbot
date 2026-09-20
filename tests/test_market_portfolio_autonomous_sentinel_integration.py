import unittest
import os
import uuid
import random
from skills.market_portfolio_autonomous_sentinel import run_autonomous_sentinel

class TestMarketPortfolioAutonomousSentinelIntegration(unittest.TestCase):

    def setUp(self):
        self.symbol = f"TICK_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://example.com/market/{uuid.uuid4().hex[:6]}"
        self.telegram_token = f"test_token_{uuid.uuid4().hex[:8]}"
        self.chat_id = str(random.randint(100000, 999999))
        self.storage_file = f"test_sentinel_storage_{uuid.uuid4().hex[:8]}.json"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_autonomous_sentinel_integration(self):
        initial_file_exists = os.path.exists(self.storage_file)
        self.assertFalse(initial_file_exists, "Файл хранилища не должен существовать до запуска теста.")

        result = run_autonomous_sentinel(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )

        self.assertIsInstance(result, dict, "Результат выполнения должен быть словарем.")
        self.assertIn("status", result, "В результате должен быть ключ status.")
        self.assertIn("forecast", result, "В результате должен быть ключ forecast.")
        
        file_created = os.path.exists(self.storage_file)
        self.assertTrue(file_created, "Модуль должен создавать или использовать файл хранилища данных.")

if __name__ == '__main__':
    unittest.main()