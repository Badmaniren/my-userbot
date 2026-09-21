import unittest
import os
import uuid
import random
from skills.market_telegram_pipeline import run_pipeline, run_market_telegram_pipeline

class TestMarketTelegramPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.storage_file = f"test_market_storage_{self.random_suffix}.json"
        self.symbol = f"SYM_{random.randint(100, 999)}"
        self.chat_id = str(random.randint(100000, 999999))
        self.token = f"{random.randint(1000, 9999)}:TEST-TOKEN-{self.random_suffix}"
        self.url = f"https://example.com/market/{self.random_suffix}"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_run_market_telegram_pipeline_integration(self):
        result = run_market_telegram_pipeline(
            storage_file=self.storage_file,
            symbol=self.symbol,
            chat_id=self.chat_id,
            url=self.url,
            telegram_token=self.token
        )
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("sent_symbol"), self.symbol)
        self.assertIn("sent_price", result)

    def test_run_pipeline_integration(self):
        success = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        
        self.assertIsInstance(success, bool)

if __name__ == "__main__":
    unittest.main()