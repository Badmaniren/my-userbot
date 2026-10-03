import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_monitor import start_ened, MarketParser, export_audit_logs

class TestMarketPortfolioMonitorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = f"test_storage_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)
        self.storage_file = os.path.join(self.test_dir, f"portfolio_{uuid.uuid4().hex}.json")
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.url = f"https://api.test.internal/{uuid.uuid4().hex}"
        self.telegram_token = f"token_{uuid.uuid4().hex}"
        self.chat_id = str(random.randint(100000, 999999))

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_integration_pipeline_execution(self):
        initial_price = round(random.uniform(10.0, 1000.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=initial_price)

        new_price = round(initial_price + random.uniform(1.0, 50.0), 2)
        
        result = start_ened(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )

        self.assertTrue(result)

        loaded_data = parser.load_data(self.storage_file)
        self.assertIsInstance(loaded_data, dict)
        self.assertIn(self.symbol, loaded_data)

        audit_result = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_result)

    def test_integration_corrupted_storage_error_handling(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("{invalid_json_payload")

        with self.assertRaises(Exception):
            parser = MarketParser(storage_file=self.storage_file)
            parser.load_data(self.storage_file)

        audit_result = export_audit_logs(storage_file=self.storage_file)
        self.assertFalse(audit_result)

if __name__ == "__main__":
    unittest.main()