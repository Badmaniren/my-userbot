import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_monitor import start_new, run_pipeline

class TestMarketPortfolioMonitorIntegration(unittest.TestCase):
    def setUp(self):
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://api.example.com/v1/{uuid.uuid4().hex[:8]}"
        self.telegram_token = f"{random.randint(100000, 999999)}:AA{uuid.uuid4().hex[:10]}"
        self.chat_id = str(random.randint(10000000, 99999999))
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_integration_pipeline_execution_and_storage(self):
        result = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.storage_file))
        
        with open(self.storage_file, "r", encoding="utf-8") as f:
            content = f.read()
            data = json.loads(content)
            self.assertIn(self.symbol, data)

    def test_integration_run_pipeline_data_flow(self):
        pipeline_result = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )

        self.assertTrue(pipeline_itude := pipeline_result)

        with open(self.storage_file, "r", encoding="utf-8") as f:
            persisted_data = json.load(f)
            self.assertEqual(persisted_data.get(self.symbol), 0.0)

if __name__ == "__main__":
    unittest.main()