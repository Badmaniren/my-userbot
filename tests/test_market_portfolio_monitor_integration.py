import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_monitor import start_new, export_audit_logs

class TestMarketPortfolioMonitorIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4()}.json"
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.url = f"https://api.telegram.org/bot{uuid.uuid4()}/sendMessage"
        self.telegram_token = str(uuid.uuid4())
        self.chat_id = str(random.randint(100000, 999999))
        self.initial_price = round(random.uniform(10.0, 1000.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_pipeline_and_audit_integration(self):
        initial_data = {self.symbol: self.initial_price}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        new_price = round(random.uniform(1001.0, 5000.0), 2)
        
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
            stored_data = json.load(f)
        
        self.assertIn(self.symbol, stored_data)

        audit_result = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_result)

if __name__ == "__main__":
    unittest.main()