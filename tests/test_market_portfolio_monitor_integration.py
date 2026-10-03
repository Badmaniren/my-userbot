import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_monitor import start_new, start_ened, export_audit_logs

class TestMarketPortfolioMonitorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_storage_dir"
        os.makedirs(self.test_dir, exist_ok=True)
        self.storage_file = os.path.join(self.test_dir, f"portfolio_{uuid.uuid4().hex}.json")
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.url = f"https://api.example.com/v1/{uuid.uuid4().hex}"
        self.telegram_token = f"token_{random.randint(100000, 999999)}"
        self.chat_id = str(random.randint(10000000, 99999999))

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        if os.path.exists(self.test_dir):
            try:
                os.rmdir(self.test_dir)
            except OSError:
                pass

    def test_pipeline_integration_flow(self):
        initial_data = {self.symbol: round(random.uniform(10.0, 1000.0), 2)}
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

        audit_status = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_status)

        with open(self.storage_file, "r", encoding="utf-8") as f:
            persisted_data = json.load(f)
        self.assertIn(self.symbol, persisted_data)

    def test_pipeline_with_non_existent_file(self):
        non_existent_file = os.path.join(self.test_dir, f"missing_{uuid.uuid4().hex}.json")

        result = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=non_existent_file
        )
        self.assertTrue(result)
        self.assertTrue(os.path.exists(non_existent_file))

        if os.path.exists(non_existent_file):
            os.remove(non_existent_file)

if __name__ == "__main__":
    unittest.main()