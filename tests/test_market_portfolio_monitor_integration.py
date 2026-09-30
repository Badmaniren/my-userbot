import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_monitor import start_new, start_ened, export_audit_logs

class TestMarketPortfolioMonitorIntegration(unittest.TestCase):
    def setUp(self):
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://api.market.net/v1/{uuid.uuid4().hex[:4]}"
        self.telegram_token = f"{random.randint(100000, 999999)}:ABC-{uuid.uuid4().hex[:8]}"
        self.chat_id = str(random.randint(100000000, 999999999))
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_market_portfolio_monitor_full_pipeline(self):
        initial_result = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(initial_result)
        self.assertTrue(os.path.exists(self.storage_file))

        with open(self.storage_file, "r", encoding="utf-8") as f:
            file_content = f.read()
            self.assertTrue(len(file_content.strip()) > 0)
            data = json.loads(file_content)
            self.assertIn(self.symbol, data)

        alias_result = start_ened(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(alias_result)

        audit_exported = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_exported)

    def test_export_audit_logs_invalid_file(self):
        invalid_file = f"invalid_{uuid.uuid4().hex}.json"
        with open(invalid_file, "w", encoding="utf-8") as f:
            f.write("NOT_A_JSON_DATA")
        
        try:
            audit_result = export_audit_logs(storage_file=invalid_file)
            self.assertFalse(audit_result)
        finally:
            if os.path.exists(invalid_file):
                os.remove(invalid_file)

if __name__ == "__main__":
    unittest.main()