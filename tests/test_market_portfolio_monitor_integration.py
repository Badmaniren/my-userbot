import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_monitor import start_new, start_ened, export_audit_logs, MarketParser, MarketReportGenerator

class TestMarketPortfolioMonitorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_storage_" + str(uuid.uuid4())
        os.makedirs(self.test_dir, exist_ok=True)
        self.storage_file = os.path.join(self.test_dir, f"portfolio_{uuid.uuid4().hex}.json")
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.url = f"https://api.example.com/webhook/{uuid.uuid4().hex}"
        self.telegram_token = f"token_{uuid.uuid4().hex}"
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

    def test_integration_pipeline_full_cycle(self):
        initial_price = round(random.uniform(10.0, 1000.0), 2)
        initial_data = {self.symbol: initial_price}
        
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

        parser = MarketParser(self.storage_file)
        loaded = parser.load_data(self.storage_file)
        self.assertIsInstance(loaded, dict)
        self.assertIn(self.symbol, loaded)
        self.assertEqual(loaded[self.symbol], initial_price)

        reporter = MarketReportGenerator(self.storage_file)
        report_text = reporter.generate_symbol_report(self.symbol)
        self.assertIn(self.symbol, report_text)
        self.assertIn(str(initial_price), report_text)

        audit_result = export_audit_logs(self.storage_file)
        self.assertTrue(audit_result)

    def test_integration_with_empty_storage(self):
        res = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res)
        self.assertTrue(os.path.exists(self.storage_file))

        parser = MarketParser(self.storage_file)
        data = parser.load_data(self.storage_file)
        self.assertIsInstance(data, dict)
        self.assertIn(self.symbol, data)

if __name__ == "__main__":
    unittest.main()