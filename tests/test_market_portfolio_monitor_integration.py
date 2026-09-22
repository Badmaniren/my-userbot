import unittest
import os
import json
import uuid
import random
from skills import db_storage
from skills import market_portfolio_monitor

class TestMarketPortfolioMonitorIntegration(unittest.TestCase):
    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.symbol = f"TEST_{self.random_suffix}"
        self.storage_file = f"test_storage_{self.random_suffix}.json"
        self.chat_id = str(random.randint(100000, 999999))
        self.telegram_token = f"token_{self.random_suffix}"
        self.url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_run_pipeline_integration(self):
        try:
            result = market_portfolio_monitor.run_pipeline(
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                storage_file=self.storage_file
            )
            self.assertTrue(result)
            self.assertTrue(os.path.exists(self.storage_file))
            
            with open(self.storage_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertIn(self.symbol, data)
        except Exception as e:
            self.fail(f"Integration pipeline failed with exception: {e}")

    def report_generator_integration(self):
        try:
            parser = market_portfolio_monitor.MarketParser(storage_file=self.storage_file)
            random_price = round(random.uniform(10.0, 1000.0), 2)
            parser.fetch_and_store(symbol=self.symbol, price=random_price)

            gen = market_portfolio_monitor.MarketReportGenerator(storage_file=self.storage_file)
            report = gen.generate_symbol_report(symbol=self.symbol)
            self.assertIn(self.symbol, report)
            self.assertIn(str(random_price), report)
        except Exception as e:
            self.fail(f"Report generator integration failed: {e}")

if __name__ == "__main__":
    unittest.main()