import unittest
import os
import uuid
import random
from skills.market_telegram_pipeline import run_pipeline, run_market_telegram_pipeline

class TestMarketTelegramPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_market_storage_{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.chat_id = str(random.randint(10000000, 99999999))
        self.telegram_token = f"{random.randint(100000, 999999)}:ABC-{uuid.uuid4().hex[:9]}"
        self.url = "https://example.com"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_run_pipeline_integration(self):
        result = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertIsInstance(result, bool)
        self.assertTrue(os.path.exists(self.storage_file))

    def test_run_market_telegram_pipeline_integration(self):
        result = run_market_telegram_pipeline(
            storage_file=self.storage_file,
            symbol=self.symbol,
            chat_id=self.chat_id,
            url=self.url,
            telegram_token=self.telegram_token
        )
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("sent_symbol"), self.symbol)
        self.assertIn("sent_price", result)

if __name__ == "__main__":
    unittest.main()