import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_monitor import start_new, start_ened, export_audit_logs

class TestMarketPortfolioMonitorIntegration(unittest.TestCase):
    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.storage_file = f"test_portfolio_storage_{self.random_suffix}.json"
        self.symbol = f"SYM_{random.randint(100, 999)}"
        self.url = f"https://api.test.local/{uuid.uuid4().hex[:6]}"
        self.telegram_token = f"token_{uuid.uuid4().hex[:6]}"
        self.chat_id = str(random.randint(100000, 999999))

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_integration_pipeline_execution(self):
        initial_data = {self.symbol: round(random.uniform(10.0, 500.0), 2)}
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

        self.assertTrue(os.path.exists(self.storage_file))
        audit_res = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_res)

        with open(self.storage_file, "r", encoding="utf-8") as f:
            content = f.read()
            parsed = json.loads(content)
            self.assertIn(self.symbol, parsed)

if __name__ == "__main__":
    unittest.main()