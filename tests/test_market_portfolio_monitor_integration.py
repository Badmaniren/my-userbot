import unittest
import os
import json
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

class TestMarketPortfolioMonitorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_id = str(uuid.uuid4())[:8]
        self.storage_file = f"test_storage_{self.test_id}.json"
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.url = f"https://api.test.local/{self.test_id}"
        self.telegram_token = f"token_{self.test_id}"
        self.chat_id = str(random.randint(100000, 999999))

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_full_pipeline_and_aliases_integration(self):
        initial_price = round(random.uniform(10.0, 500.0), 2)
        
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=initial_price)
        
        self.assertTrue(os.path.exists(self.storage_file), "Storage file must be created by fetch_and_store")
        
        loaded_data = parser.load_data(self.storage_file)
        self.assertIsInstance(loaded_data, dict)
        self.assertIn(self.symbol, loaded_data)
        self.assertEqual(loaded_data[self.symbol], initial_price)

        new_price = round(initial_price * 1.05, 2)
        
        pipeline_result = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(pipeline_result)

        start_new_result = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(start_new_result)

        start_ened_result = start_ened(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(start_ened_result)

        report_gen = MarketReportGenerator(storage_file=self.storage_file)
        symbol_report = report_gen.generate_symbol_report(symbol=self.symbol)
        self.assertIn(self.symbol, symbol_report)

        raw_dump = report_gen.get_raw_stream_dump()
        self.assertIsInstance(raw_dump, str)
        self.assertIn(self.symbol, raw_dump)

        market_report = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
        self.assertIn(self.symbol, market_report)

        tg_pipeline = run_market_telegram_pipeline(
            storage_file=self.storage_file,
            symbol=self.symbol,
            chat_id=self.chat_id,
            url=self.url,
            telegram_token=self.telegram_token
        )
        self.assertIsInstance(tg_pipeline, dict)
        self.assertEqual(tg_pipeline.get("status"), "success")
        self.assertEqual(tg_pipeline.get("symbol"), self.symbol)
        self.assertEqual(tg_pipeline.get("chat_id"), self.chat_id)
        self.assertEqual(tg_pipeline.get("url"), self.url)

        audit_exported = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_exported)

    def test_empty_or_nonexistent_storage(self):
        non_existent_file = f"non_existent_{self.test_id}.json"
        
        parser = MarketParser(storage_file=non_existent_file)
        data = parser.load_data(non_existent_file)
        self.assertEqual(data, {})

        report_gen = MarketReportGenerator(storage_file=non_existent_file)
        report = report_gen.generate_symbol_report(symbol=self.symbol)
        self.assertIn("No data", report)

        dump = report_gen.get_raw_stream_dump()
        self.assertEqual(dump, "{}")

        audit_result = export_audit_logs(storage_file=non_existent_file)
        self.assertFalse(audit_result)

if __name__ == "__main__":
    unittest.main()