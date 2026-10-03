import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_monitor import start_ened, export_audit_logs

class TestMarketPortfolioMonitorIntegration(unittest.TestCase):
    def setUp(self):
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://api.test.internal/{uuid.uuid4().hex[:4]}"
        self.telegram_token = f"tok_{uuid.uuid4().hex[:8]}"
        self.chat_id = str(random.randint(100000, 999999))
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_integration_pipeline_execution(self):
        self.assertFalse(os.path.exists(self.storage_file))
        
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
            file_content = f.read()
            self.assertTrue(len(file_content.strip()) > 0)
            parsed_data = json.loads(file_content)
            self.assertIn(self.symbol, parsed_data)
            
        audit_result = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_result)

if __name__ == "__main__":
    unittest.main()