import unittest
from unittest.mock import patch
import os
import json
import uuid
import random
import io
from skills.market_portfolio_monitor import (
    MarketParser,
    MarketReportGenerator,
    run_pipeline,
    start_new,
    start_ened,
    generate_market_report,
    run_market_telegram_pipeline,
    export_audit_logs
)

class TestMarketPortfolioMonitor(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://api.testnet.{uuid.uuid4().hex[:8]}.org/v1"
        self.telegram_token = f"bot:{uuid.uuid4().hex[:16]}"
        self.chat_id = str(random.randint(10000000, 99999999))
        self.price = round(random.uniform(10.0, 5000.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_market_parser_fetch_and_load_data(self):
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, self.price)
        
        loaded_data = parser.load_data(self.storage_file)
        self.assertIsInstance(loaded_data, dict)
        self.assertIn(self.symbol, loaded_data)
        self.assertEqual(loaded_data[self.symbol], self.price)

    def test_market_parser_load_nonexistent_file(self):
        non_existent = f"missing_{uuid.uuid4().hex}.json"
        parser = MarketParser(non_existent)
        result = parser.load_data(non_existent)
        self.assertIsNone(result)

    def test_market_parser_load_corrupted_json(self):
        corrupted_content = f"{{invalid_json_{uuid.uuid4().hex}}}"
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(corrupted_content)
            
        parser = MarketParser(self.storage_file)
        with patch("builtins.open", return_value=io.StringIO(corrupted_content)):
            result = parser.load_data(self.storage_file)
            self.assertIsNone(result)

    def test_market_report_generator_symbol_report(self):
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, self.price)
        
        gen = MarketReportGenerator(self.storage_file)
        report = gen.generate_symbol_report(self.symbol)
        
        self.assertIn(self.symbol, report)
        self.assertIn(str(self.price), report)

    def test_market_report_generator_no_data(self):
        gen = MarketReportGenerator(self.storage_file)
        report = gen.generate_symbol_report(self.symbol)
        
        self.assertIn(self.symbol, report)
        self.assertIn("No data", report)

    def test_market_report_generator_raw_stream_dump(self):
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, self.price)
        
        gen = MarketReportGenerator(self.storage_file)
        dump = gen.get_raw_stream_dump()
        
        self.assertIsInstance(dump, str)
        parsed_dump = json.loads(dump)
        self.assertEqual(parsed_dump[self.symbol], self.price)

    def test_generate_market_report_function(self):
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, self.price)
        
        report = generate_market_report(self.storage_file, self.symbol)
        self.assertIn(self.symbol, report)

    def test_run_market_telegram_pipeline(self):
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, self.price)
        
        res = run_market_telegram_pipeline(
            storage_file=self.storage_file,
            symbol=self.symbol,
            chat_id=self.chat_id,
            url=self.url,
            telegram_token=self.telegram_token
        )
        
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["symbol"], self.symbol)
        self.assertEqual(res["price"], self.price)
        self.assertEqual(res["chat_id"], self.chat_id)
        self.assertEqual(res["url"], self.url)

    def test_export_audit_logs_valid(self):
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, self.price)
        
        result = export_audit_logs(self.storage_file)
        self.assertTrue(result)

    def test_export_audit_logs_empty(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("   ")
            
        result = export_audit_logs(self.storage_file)
        self.assertFalse(result)

    def test_export_audit_logs_missing(self):
        result = export_audit_logs(f"ghost_{uuid.uuid4().hex}.json")
        self.assertFalse(result)

    def test_run_pipeline_execution(self):
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, self.price)
        
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

    def test_start_ened_execution(self):
        success = start_ened(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(success)

if __name__ == "__main__":
    unittest.main()