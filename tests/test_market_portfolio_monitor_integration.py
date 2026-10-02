import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_monitor import start_new, start_ened, export_audit_logs

class TestMarketPortfolioMonitorIntegration(unittest.TestCase):
    def setUp(self):
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://api.telegram.org/bot{uuid.uuid4().hex}"
        self.telegram_token = str(uuid.uuid4())
        self.chat_id = str(random.randint(100000, 999999))
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_market_portfolio_monitor_full_pipeline(self):
        initial_check = export_audit_logs(self.storage_file)
        self.assertFalse(initial_check)

        result_new = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(result_new)

        self.assertTrue(os.path.exists(self.storage_file))

        result_ened = start_ened(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(result_ened)

        audit_check = export_audit_logs(self.storage_file)
        self.assertTrue(audit_check)

        with open(self.storage_file, "r", encoding="utf-8") as f:
            raw_content = f.read()
            parsed_data = json.loads(raw_content)
            self.assertIn(self.symbol, parsed_data)

if __name__ == "__main__":
    unittest.main()