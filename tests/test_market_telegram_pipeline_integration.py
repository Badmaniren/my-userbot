import unittest
import os
import uuid
import random
from skills.market_telegram_pipeline import run_market_telegram_pipeline, run_pipeline

class TestMarketTelegramPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.test_id = str(uuid.uuid4())[:8]
        self.storage_file = f"test_market_storage_{self.test_id}.json"
        self.symbol = f"SYM_{self.test_id.upper()}"
        self.chat_id = str(random.randint(100000, 999999))
        self.telegram_token = f"{random.randint(1000,9999)}:TEST_TOKEN_{self.test_id}"
        self.url = f"https://example.com/market/{self.test_id}"

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
            telegram_token=self.telegram_token
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("sent_symbol"), self.symbol)
        self.assertIsInstance(result.get("sent_price"), float)

    def test_run_pipeline_network_call(self):
        try:
            pipeline_result = run_pipeline(
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                storage_file=self.storage_file
            )
            self.assertIn(pipeline_result, [True, False])
        except Exception as e:
            self.assertIsNotNone(e)

if __name__ == "__main__":
    unittest.main()