import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_monitor import start_ened, export_audit_logs

class TestMarketPortfolioMonitorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_storage_dir"
        os.makedirs(self.test_dir, exist_ok=True)
        self.storage_file = os.path.join(self.test_dir, f"storage_{uuid.uuid4()}.json")
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.url = f"https://api.telegram.org/bot{uuid.uuid4()}/sendMessage"
        self.telegram_token = str(uuid.uuid4())
        self.chat_id = str(random.randint(100000, 999999))

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass
        if os.path.exists(self.test_dir):
            try:
                os.rmdir(self.test_dir)
            except OSError:
                pass

    def test_integration_pipeline_and_storage(self):
        initial_data = {self.symbol: round(random.uniform(10.0, 1000.0), 2)}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        result = start_ened(
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
            parsed = json.loads(content)
            self.assertIn(self.symbol, parsed)
            self.assertEqual(parsed[self.symbol], initial_data[self.symbol])

        audit_export = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_export)

if __name__ == "__main__":
    unittest.main()