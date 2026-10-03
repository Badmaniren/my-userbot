import unittest
import uuid
import random
import os
import tempfile
from skills.market_portfolio_monitor import start_new, start_ened, export_audit_logs
from skills.db_storage import save_to_db, load_from_db

class TestMarketPortfolioMonitorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.test_dir.name, f"audit_{uuid.uuid4()}.json")
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.url = f"https://api.mockmarket.io/v1/{uuid.uuid4()}"
        self.telegram_token = f"token_{uuid.uuid4()}"
        self.chat_id = str(random.randint(100000000, 999999999))

    def tearDown(self):
        self.test_dir.cleanup()

    def test_full_integration_pipeline_without_mocks(self):
        # Генерируем случайные параметры ликвидности и цены
        random_price = round(random.uniform(10.0, 5000.0), 2)
        
        # Интеграция с реальным хранилищем db_storage
        initial_db_data = {self.symbol: random_price, "liquidity_index": random.randint(1, 100)}
        save_to_db(self.storage_file, initial_db_data)

        # Проверяем работу start_new (без моков, сквозной вызов пайплайна)
        pipeline_result = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(pipeline_result)

        # Проверяем работу алиаса start_ened
        alias_result = start_ened(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(alias_result)

        # Проверяем реальное состояние хранилища после пайплайна
        loaded_data = load_from_db(self.storage_file)
        self.assertIsInstance(loaded_data, dict)
        self.assertIn(self.symbol, loaded_data)
        self.assertEqual(loaded_data[self.symbol], random_price)

        # Проверяем экспорт аудиторских логов
        audit_exported = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_exported)

if __name__ == "__main__":
    unittest.main()