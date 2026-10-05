import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_monitor import start_new, start_ened, export_audit_logs

class TestMarketPortfolioMonitorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = f"test_storage_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)
        self.storage_file = os.path.join(self.test_dir, f"portfolio_{uuid.uuid4().hex}.json")
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://api.test.internal/{uuid.uuid4().hex}"
        self.telegram_token = f"tok_{uuid.uuid4().hex}"
        self.chat_id = str(random.randint(100000, 999999))

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_pipeline_integration_flow(self):
        initial_price = round(random.uniform(10.0, 1000.0), 2)
        initial_data = {self.symbol: initial_price}
        
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        res_new = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res_new)

        res_ened = start_ened(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res_ened)

        audit_result = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_result)

        self.assertTrue(os.path.exists(self.storage_file))
        with open(self.storage_file, "r", encoding="utf-8") as f:
            persisted_data = json.load(f)
            self.assertIn(self.symbol, persisted_data)
            self.assertEqual(persisted_data[self.symbol], initial_price)

if __name__ == "__main__":
    unittest.main()