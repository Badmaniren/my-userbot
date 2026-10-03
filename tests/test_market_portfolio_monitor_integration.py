import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_monitor import start_new, start_ened, export_audit_logs

class TestMarketPortfolioMonitorIntegration(unittest.TestCase):
    def setUp(self):
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://api.example.com/v1/market/{uuid.uuid4().hex[:4]}"
        self.telegram_token = f"bot{random.randint(100000, 999999)}:AAG{uuid.uuid4().hex[:6]}"
        self.chat_id = str(random.randint(10000000, 99999999))
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_pipeline_execution_and_storage_flow(self):
        initial_price = round(random.uniform(10.0, 1500.0), 2)
        initial_data = {self.symbol: initial_price}
        
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        pipeline_result = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )

        self.assertTrue(pipeline_result)
        self.assertTrue(os.path.exists(self.storage_file))

        audit_status = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_status)

        alias_result = start_ened(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(alias_result)

        with open(self.storage_file, "r", encoding="utf-8") as f:
            stored_content = json.load(f)
        
        self.assertIn(self.symbol, stored_content)
        self.assertEqual(stored_content[self.symbol], initial_price)

if __name__ == "__main__":
    unittest.main()