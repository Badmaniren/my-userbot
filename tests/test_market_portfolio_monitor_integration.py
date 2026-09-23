import unittest
import uuid
import random
import os
from skills.market_portfolio_monitor import start_new, run_pipeline, MarketParser, MarketReportGenerator
from skills.db_storage import save_to_db, load_from_db

class TestMarketPortfolioMonitorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.test_price = round(random.uniform(10.0, 1000.0), 2)
        self.test_chat_id = str(random.randint(100000, 999999))
        self.test_url = f"https://api.telegram.org/bot{uuid.uuid4().hex[:8]}/sendMessage"
        self.test_token = f"{random.randint(1000,9999)}:AA{uuid.uuid4().hex[:10]}"
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_pipeline_integration_without_mocks(self):
        result = start_new(
            symbol=self.test_symbol,
            url=self.test_url,
            telegram_token=self.test_token,
            chat_id=self.test_chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.storage_file))

        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.test_symbol, price=self.test_price)

        report_gen = MarketReportGenerator(storage_file=self.storage_file)
        report = report_gen.generate_symbol_report(symbol=self.test_symbol)
        
        self.assertIn(self.test_symbol, report)
        self.assertIn(str(self.test_price), report)

        raw_dump = report_gen.get_raw_stream_dump()
        self.assertIn(self.test_symbol, raw_dump)

        db_key = f"portfolio_{uuid.uuid4().hex[:6]}"
        save_to_db(db_key, {"symbol": self.test_symbol, "price": self.test_price})
        loaded_db_data = load_from_db(db_key)
        self.assertEqual(loaded_db_data["symbol"], self.test_symbol)
        self.assertEqual(loaded_db_data["price"], self.test_price)

if __name__ == "__main__":
    unittest.main()