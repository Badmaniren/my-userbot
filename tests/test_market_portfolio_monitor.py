import unittest
from unittest.mock import patch
import os
import json
import uuid
import random
import io
from skills.market_portfolio_monitor import (
    run_pipeline,
    start_new,
    MarketParser,
    MarketReportGenerator,
    generate_market_report,
    run_market_telegram_pipeline,
    run_compliance_export,
    export_audit_logs
)

class TestMarketPortfolioMonitor(unittest.TestCase):

    def setUp(self):
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://{uuid.uuid4().hex[:8]}.com/api"
        self.telegram_token = f"{random.randint(1000,9999)}:BOT_{uuid.uuid4().hex[:6]}"
        self.chat_id = str(random.randint(100000, 999999))
        self.storage_file = f"test_store_{uuid.uuid4().hex[:8]}.json"
        self.price = round(random.uniform(10.0, 1000.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_market_parser_fetch_and_load(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)
        
        self.assertTrue(os.path.exists(self.storage_file))
        loaded_data = parser.load_data(self.storage_file)
        self.assertIsInstance(loaded_data, dict)
        self.assertIn(self.symbol, loaded_data)
        self.assertEqual(loaded_data[self.symbol], self.price)

    def test_market_parser_load_data_missing(self):
        non_existent_file = f"missing_{uuid.uuid4().hex}.json"
        parser = MarketParser(storage_file=non_existent_file)
        data = parser.load_data(non_existent_file)
        self.assertIsNone(data)

    def test_market_report_generator_with_data(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)
        
        generator = MarketReportGenerator(storage_file=self.storage_file)
        report = generator.generate_symbol_report(symbol=self.symbol)
        
        self.assertIn(self.symbol, report)
        self.assertIn(str(self.price), report)

    def test_market_report_generator_no_data(self):
        generator = MarketReportGenerator(storage_file=self.storage_file)
        report = generator.generate_symbol_report(symbol=self.symbol)
        
        self.assertIn(self.symbol, report)
        self.assertIn("No data", report)

    def test_market_report_generator_raw_stream_dump(self):
        raw_content = json.dumps({self.symbol: self.price})
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", return_value=io.StringIO(raw_content)):
            generator = MarketReportGenerator(storage_file=self.storage_file)
            dump = generator.get_raw_stream_dump()
            self.assertEqual(dump, raw_content)

    def test_market_report_generator_raw_stream_dump_missing(self):
        generator = MarketReportGenerator(storage_file=self.storage_file)
        with patch("os.path.exists", return_value=False):
            dump = generator.get_raw_stream_dump()
            self.assertEqual(dump, "{}")

    def test_generate_market_report_wrapper(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)
        
        report = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
        self.assertIn(self.symbol, report)
        self.assertIn(str(self.price), report)

    def test_run_market_telegram_pipeline(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)
        
        result = run_market_telegram_pipeline(
            storage_file=self.storage_file,
            symbol=self.symbol,
            chat_id=self.chat_id,
            url=self.url,
            telegram_token=self.telegram_token
        )
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("symbol"), self.symbol)
        self.assertEqual(result.get("price"), self.price)
        self.assertEqual(result.get("chat_id"), self.chat_id)
        self.assertEqual(result.get("url"), self.url)

    def test_run_pipeline_execution(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)

        success = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(success)

    def test_start_new_execution(self):
        success = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(success)

    def test_run_compliance_export(self):
        res = run_compliance_export(storage_file=self.storage_file)
        self.assertTrue(res)

    def test_export_audit_logs(self):
        res = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(res)

if __name__ == "__main__":
    unittest.main()