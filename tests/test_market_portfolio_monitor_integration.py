import unittest
import os
import uuid
import random
from skills.market_portfolio_monitor import (
    MarketParser,
    MarketReportGenerator,
    run_market_telegram_pipeline
)

class TestMarketPortfolioMonitorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_id = str(uuid.uuid4())[:8]
        self.storage_file = f"test_storage_{self.test_id}.json"
        self.symbol = f"COIN_{self.test_id}"
        self.random_price = round(random.uniform(10.0, 1000.0), 2)
        self.url = f"https://example.com/price/{self.symbol.lower()}"
        self.telegram_token = f"fake_token_{self.test_id}"
        self.chat_id = f"chat_{self.test_id}"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_market_portfolio_monitor_full_pipeline(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.random_price)

        self.assertTrue(os.path.exists(self.storage_file), "Storage file should be created after fetch_and_store")

        loaded_data = parser.load_data(self.storage_file)
        self.assertIsNotNone(loaded_data, "Loaded data should not be None")
        
        if isinstance(loaded_data, dict):
            self.assertIn(self.symbol, loaded_data)
            self.assertEqual(loaded_data[self.symbol], self.random_price)

        report_gen = MarketReportGenerator(storage_file=self.storage_file)
        symbol_report = report_gen.generate_symbol_report(symbol=self.symbol)
        self.assertIsNotNone(symbol_report, "Symbol report must be generated")

        market_report = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
        self.assertIsNotNone(market_report, "Market report must be generated")

        raw_dump = report_gen.get_raw_stream_dump()
        self.assertIsNotNone(raw_dump, "Raw stream dump must be available")

        pipeline_result = run_market_telegram_pipeline(
            storage_file=self.storage_file,
            symbol=self.symbol,
            chat_id=self.chat_id,
            url=self.url,
            telegram_token=self.telegram_token
        )
        self.assertIsNotNone(pipeline_result, "Pipeline execution must return a result")

if __name__ == "__main__":
    unittest.main()