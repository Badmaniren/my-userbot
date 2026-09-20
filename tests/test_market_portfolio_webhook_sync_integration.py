import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_webhook_sync import MarketPortfolioWebhookSync, start_new, MarketPortfolioIntegrationHub, AutonomousSentinel, MarketParser

class TestMarketPortfolioWebhookSyncIntegration(unittest.TestCase):
    def setUp(self):
        self.random_suffix = str(uuid.uuid4())[:8]
        self.storage_file = f"test_storage_{self.random_suffix}.json"
        self.webhook_url = f"https://example.com/webhook/{self.random_suffix}"
        self.symbol = f"SYM_{random.randint(100, 999)}"
        self.price = round(random.uniform(10.0, 1000.0), 2)
        self.url = f"https://market.example.com/api/{self.symbol.lower()}"
        self.telegram_token = f"token_{self.random_suffix}"
        self.chat_id = str(random.randint(10000, 99999))
        self.threshold = round(random.uniform(0.1, 5.0), 2)
        self.shift = round(random.uniform(-10.0, 10.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_webhook_sync_and_start_new_integration(self):
        sync_module = MarketPortfolioWebhookSync(self.storage_file, self.webhook_url)
        
        store_result = sync_module.store_initial_state(self.symbol, self.price)
        self.assertTrue(os.path.exists(self.storage_file), "Storage file must be created during initial state storage.")

        loaded_data = sync_module.load_data(self.storage_file)
        self.assertIn(self.symbol, loaded_data)
        self.assertEqual(loaded_data[self.symbol], self.price)

        new_price = round(self.price * 1.05, 2)
        webhook_response = sync_module.trigger_webhook_sync(self.symbol, new_price)
        
        self.assertEqual(webhook_response["status"], "success")
        self.assertEqual(webhook_response["symbol"], self.symbol)
        self.assertEqual(webhook_response["price"], new_price)
        self.assertEqual(webhook_response["webhook_url"], self.webhook_url)

        pipeline_result = start_new(
            storage_file=self.storage_file,
            url=self.url,
            symbol=self.symbol,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            threshold=self.threshold,
            shift=self.shift
        )

        self.assertIsInstance(pipeline_result, dict)
        self.assertEqual(pipeline_result["symbol"], self.symbol)
        self.assertEqual(pipeline_result["url"], self.url)
        self.assertEqual(pipeline_result["token"], self.telegram_token)
        self.assertEqual(pipeline_result["chat_id"], self.chat_id)
        self.assertEqual(pipeline_result["shift"], self.shift)
        self.assertEqual(pipeline_result["storage"], self.storage_file)
        self.assertIn(self.symbol, pipeline_result["msg"])

        final_loaded = sync_module.load_data(self.storage_file)
        self.assertEqual(final_loaded[self.symbol], new_price)

if __name__ == "__main__":
    unittest.main()