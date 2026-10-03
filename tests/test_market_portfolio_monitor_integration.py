import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_monitor import start_ened, export_audit_logs

class TestMarketPortfolioMonitorIntegration(unittest.TestCase):
    def setUp(self):
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://api.market.example/v1/{uuid.uuid4().hex[:4]}"
        self.telegram_token = f"bot{random.randint(100000, 999999)}:{uuid.uuid4().hex[:12]}"
        self.chat_id = f"-{random.randint(100000000, 999999999)}"
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_pipeline_and_audit_export_integration(self):
        self.assertFalse(os.path.exists(self.storage_file))
        
        pipeline_result = start_ened(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        
        self.assertTrue(pipeline_result)
        self.assertTrue(os.path.exists(self.storage_file))
        
        with open(self.storage_file, "r", encoding="utf-8") as f:
            file_content = f.read()
            self.assertTrue(len(file_content) > 0)
            parsed_data = json.loads(file_content)
            self.assertIn(self.symbol, parsed_data)

        audit_result = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_result)

if __name__ == "__main__":
    unittest.main()