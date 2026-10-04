import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_monitor import start_new, start_ened, export_audit_logs, MarketParser

class TestMarketPortfolioMonitorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_storage_dir"
        os.makedirs(self.test_dir, exist_ok=True)
        self.storage_file = os.path.join(self.test_dir, f"storage_{uuid.uuid4().hex}.json")
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://api.mock-market-{uuid.uuid4().hex[:4]}.net/v1"
        self.telegram_token = f"bot{random.randint(100000, 999999)}:AA{uuid.uuid4().hex[:10]}"
        self.chat_id = str(random.randint(10000000, 99999999))

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        if os.path.exists(self.test_dir):
            try:
                os.rmdir(self.test_dir)
            except OSError:
                pass

    def test_pipeline_integration_and_data_integrity(self):
        initial_price = round(random.uniform(10.0, 5000.0), 2)
        initial_data = {self.symbol: initial_price}
        
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

        parser = MarketParser(storage_file=self.storage_file)
        loaded_data = parser.load_data(self.storage_file)
        self.assertIsInstance(loaded_data, dict)
        self.assertIn(self.symbol, loaded_data)
        self.assertEqual(loaded_data[self.symbol], initial_price)

        audit_status = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_status)

        new_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        result_ened = start_ened(
            symbol=new_symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(result_ened)

        updated_data = parser.load_data(self.storage_file)
        self.assertIn(new_symbol, updated_data)
        self.assertEqual(updated_data[new_symbol], 0.0)

    def test_corrupted_storage_handling(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("{invalid_json_payload_" + uuid.uuid4().hex)

        audit_status = export_audit_logs(storage_file=self.storage_file)
        self.assertFalse(audit_status)

        result = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(result)

        parser = MarketParser(storage_file=self.storage_file)
        loaded_data = parser.load_data(self.storage_file)
        self.assertIsInstance(loaded_data, dict)
        self.assertIn(self.symbol, loaded_data)

if __name__ == "__main__":
    unittest.main()