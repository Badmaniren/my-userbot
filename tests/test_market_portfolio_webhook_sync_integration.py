import unittest
import os
import uuid
import random
from skills.market_portfolio_webhook_sync import MarketPortfolioWebhookSync

class TestMarketPortfolioWebhookSyncIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4()}.json"
        self.webhook_url = f"https://example.com/webhook/{uuid.uuid4()}"
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.initial_price = round(random.uniform(10.0, 500.0), 2)
        self.critical_price = round(random.uniform(600.0, 1000.0), 2)
        
        self.sync_module = MarketPortfolioWebhookSync(self.storage_file, self.webhook_url)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_webhook_sync_pipeline_real_execution(self):
        self.sync_module.store_initial_state(self.symbol, self.initial_price)
        self.assertTrue(os.path.exists(self.storage_file), "Файл хранилища должен быть создан реальным вызовом.")

        dispatch_result = self.sync_module.trigger_webhook_sync(self.symbol, self.critical_price)
        self.assertIsInstance(dispatch_result, dict, "Результат должен быть словарем с данными отправки.")
        self.assertIn("status", dispatch_result)
        self.assertEqual(dispatch_result["status"], "success")
        self.assertEqual(dispatch_result["symbol"], self.symbol)
        self.assertEqual(dispatch_result["price"], self.critical_price)

        updated_data = self.sync_module.load_data(self.storage_file)
        self.assertIn(self.symbol, updated_data)
        self.assertEqual(updated_data[self.symbol], self.critical_price)

if __name__ == "__main__":
    unittest.main()