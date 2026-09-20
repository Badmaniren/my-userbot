import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_webhook_sync import MarketPortfolioWebhookSync, start_new, MarketParser, AutonomousSentinel, MarketPortfolioIntegrationHub

class TestMarketPortfolioWebhookSyncIntegration(unittest.TestCase):
    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.storage_file = f"test_storage_{self.random_suffix}.json"
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.price = round(random.uniform(10.0, 500.0), 2)
        self.webhook_url = f"https://example.com/webhook/{uuid.uuid4()}"
        self.url = f"https://market.example.com/api/{self.random_suffix}"
        self.telegram_token = f"token_{uuid.uuid4().hex}"
        self.chat_id = str(random.randint(100000, 999999))
        self.threshold = round(random.uniform(0.5, 5.0), 2)
        self.shift = random.randint(1, 10)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_webhook_sync_and_full_pipeline_integration(self):
        webhook_sync = MarketPortfolioWebhookSync(self.storage_file, self.webhook_url)
        
        sync_result = webhook_sync.trigger_webhook_sync(self.symbol, self.price)
        
        self.assertEqual(sync_result["status"], "success")
        self.assertEqual(sync_result["symbol"], self.symbol)
        self.assertEqual(sync_result["price"], self.price)
        self.assertEqual(sync_result["webhook_url"], self.webhook_url)

        self.assertTrue(os.path.exists(self.storage_file))
        
        loaded_data = webhook_sync.load_data(self.storage_file)
        self.assertIn(self.symbol, loaded_data)
        self.assertEqual(loaded_data[self.symbol], self.price)

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
        self.assertEqual(pipeline_result["price"], self.price)
        self.assertEqual(pipeline_result["url"], self.url)
        self.assertEqual(pipeline_result["token"], self.telegram_token)
        self.assertEqual(pipeline_result["chat_id"], self.chat_id)
        self.assertEqual(pipeline_result["shift"], self.shift)
        self.assertEqual(pipeline_result["storage"], self.storage_file)
        self.assertEqual(pipeline_result["msg"], f"alert_{self.symbol}")

if __name__ == "__main__":
    unittest.main()