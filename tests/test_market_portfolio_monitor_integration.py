import unittest
import os
import tempfile
import uuid
import random
from skills.market_portfolio_monitor import (
    run_pipeline,
    start_new,
    start_ened,
    MarketParser,
    MarketReportGenerator,
    generate_market_report,
    run_market_telegram_pipeline,
    export_audit_logs
)
from skills.db_storage import MarketParser as DBMarketParser
from skills.market_portfolio_collector_agent import MarketParser as CollectorMarketParser, PortfolioValuation

class TestMarketPortfolioMonitorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.test_dir.name, f"test_storage_{uuid.uuid4().hex}.json")
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://api.test-market-{uuid.uuid4().hex[:4]}.com/v1"
        self.telegram_token = f"bot{random.randint(100000, 999999)}:AAG{uuid.uuid4().hex[:10]}"
        self.chat_id = str(random.randint(10000, 99999999))

    def tearDown(self):
        self.test_dir.cleanup()

    def test_full_pipeline_integration_without_mocks(self):
        random_price = round(random.uniform(10.0, 5000.0), 2)
        
        initial_data = {self.symbol: random_price}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            import json
            json.dump(initial_data, f)

        res_pipeline = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res_pipeline)

        res_start_new = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res_start_new)

        res_start_ened = start_ened(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res_start_ened)

        parser = MarketParser(storage_file=self.storage_file)
        loaded = parser.load_data(self.storage_file)
        self.assertIsInstance(loaded, dict)
        self.assertIn(self.symbol, loaded)

        report_gen = MarketReportGenerator(storage_file=self.storage_file)
        symbol_report = report_gen.generate_symbol_report(symbol=self.symbol)
        self.assertIn(self.symbol, symbol_report)
        self.assertIn(str(random_price), symbol_report)

        raw_dump = report_gen.get_raw_stream_dump()
        self.assertIsInstance(raw_dump, str)
        self.assertIn(self.symbol, raw_dump)

        gen_report = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
        self.assertIn(self.symbol, gen_report)

        telegram_res = run_market_telegram_pipeline(
            storage_file=self.storage_file,
            symbol=self.symbol,
            chat_id=self.chat_id,
            url=self.url,
            telegram_token=self.telegram_token
        )
        self.assertEqual(telegram_res["status"], "success")
        self.assertEqual(telegram_res["symbol"], self.symbol)
        self.assertEqual(telegram_res["price"], random_price)
        self.assertEqual(telegram_res["chat_id"], self.chat_id)
        self.assertEqual(telegram_res["url"], self.url)

        audit_status = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_status)

        db_parser = DBMarketParser(storage_file=self.storage_file)
        self.assertIsNotNone(db_parser)

        collector_storage = os.path.join(self.test_dir.name, f"collector_{uuid.uuid4().hex}.json")
        collector_parser = CollectorMarketParser(storage_file=collector_storage)
        collector_parser.fetch_and_store(self.symbol, random_price)
        valuation = PortfolioValuation(storage_file=collector_storage)
        summary = valuation.get_total_summary(self.url)
        self.assertEqual(summary["summary"], "ok")

    def test_resilience_corrupted_storage_integration(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("{corrupted_json_syntax_without_closing")

        parser = MarketParser(storage_file=self.storage_file)
        data = parser.load_data(self.storage_file)
        self.assertEqual(data, {})

        parser.fetch_and_store(symbol=self.symbol, price=123.45)

        loaded_again = parser.load_data(self.storage_file)
        self.assertIn(self.symbol, loaded_again)
        self.assertEqual(loaded_again[self.symbol], 123.45)

        audit_status = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_status)

if __name__ == "__main__":
    unittest.main()