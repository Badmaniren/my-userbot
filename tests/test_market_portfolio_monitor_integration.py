import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_monitor import start_new, start_ened, export_audit_logs

class TestMarketPortfolioMonitorIntegration(unittest.TestCase):
    def setUp(self):
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://api.mock-market-{uuid.uuid4().hex[:4]}.com/v1"
        self.telegram_token = f"token_{uuid.uuid4().hex[:8]}"
        self.chat_id = str(random.randint(100000, 999999))
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_pipeline_and_audit_export_integration(self):
        initial_price = round(random.uniform(10.0, 1000.0), 2)
        
        initial_data = {self.symbol: initial_price}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        result_new = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(result_new)

        result_ened = start_ened(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(result_ened)

        audit_exported = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_exported)

        with open(self.storage_file, "r", encoding="utf-8") as f:
            saved_content = json.load(f)
        
        self.assertIn(self.symbol, saved_content)
        self.assertEqual(saved_content[self.symbol], initial_price)

if __name__ == "__main__":
    unittest.main()