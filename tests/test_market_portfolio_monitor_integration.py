import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_monitor import start_ened, export_audit_logs

class TestMarketPortfolioMonitorIntegration(unittest.TestCase):
    def setUp(self):
        self.random_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.random_price = round(random.uniform(10.0, 5000.0), 2)
        self.chat_id = str(random.randint(100000, 999999))
        self.telegram_token = f"{random.randint(1000,9999)}:ABC-{uuid.uuid4().hex[:6]}"
        self.url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"
        
        initial_data = {self.random_symbol: self.random_price}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_integration_pipeline_execution(self):
        result = start_ened(
            symbol=self.random_symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(result)
        
        with open(self.storage_file, "r", encoding="utf-8") as f:
            persisted_data = json.load(f)
        
        self.assertIn(self.random_symbol, persisted_data)
        self.assertEqual(persisted_data[self.random_symbol], self.random_price)
        
        audit_status = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_status)

    def test_integration_corrupted_storage_error_handling(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("{invalid_json_structure")
            
        with self.assertRaises(json.JSONDecodeError):
            start_ened(
                symbol=self.random_symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                storage_file=self.storage_file
            )
            
        audit_status = export_audit_logs(storage_file=self.storage_file)
        self.assertFalse(audit_status)

if __name__ == "__main__":
    unittest.main()