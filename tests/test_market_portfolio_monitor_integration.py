import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_monitor import start_new, start_ened, export_audit_logs

class TestMarketPortfolioMonitorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.dirname(__file__) if '__file__' in locals() else "."
        self.storage_file = os.path.join(self.test_dir, f"test_storage_{uuid.uuid4().hex}.json")
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.url = f"https://api.mock-liquidity-provider.net/v1/{uuid.uuid4().hex[:8]}"
        self.telegram_token = f"bot{random.randint(100000, 999999)}:AAG{uuid.uuid4().hex[:10]}"
        self.chat_id = f"-100{random.randint(100000000, 999999999)}"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_pipeline_integration_flow(self):
        initial_data = {self.symbol: round(random.uniform(10.0, 5000.0), 2)}
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

        audit_exported = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_exported)

        with open(self.storage_file, "r", encoding="utf-8") as f:
            persisted_data = json.load(f)
            self.assertIn(self.symbol, persisted_data)

if __name__ == "__main__":
    unittest.main()