import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_monitor import start_new, start_ened, export_audit_logs, MarketParser, MarketReportGenerator

class IntegrationTestMarketPortfolioMonitor(unittest.TestCase):

    def setUp(self):
        self.symbol = f"SYM_{uuid.uuid4().hex[:8].upper()}"
        self.url = f"https://api.test.market/{uuid.uuid4().hex[:6]}"
        self.telegram_token = f"token_{uuid.uuid4().hex[:10]}"
        self.chat_id = str(random.randint(100000, 999999))
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_full_pipeline_integration(self):
        initial_price = round(random.uniform(10.0, 500.0), 2)

        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=initial_price)

        self.assertTrue(os.path.exists(self.storage_file))

        result_start_new = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(result_start_new)

        new_price = round(initial_price + random.uniform(1.0, 50.0), 2)
        result_start_ened = start_ened(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(result_start_ened)

        report_gen = MarketReportGenerator(storage_file=self.storage_file)
        report_text = report_gen.generate_symbol_report(symbol=self.symbol)
        self.assertIn(self.symbol, report_text)

        audit_exported = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_exported)

        loaded_data = parser.load_data(self.storage_file)
        self.assertIsInstance(loaded_data, dict)
        self.assertIn(self.symbol, loaded_data)

if __name__ == "__main__":
    unittest.main()