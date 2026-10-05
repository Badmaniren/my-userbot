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
    start_ened,
    MarketParser,
    MarketReportGenerator,
    generate_market_report,
    run_market_telegram_pipeline,
    export_audit_logs
)

class TestMarketPortfolioMonitor(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://{uuid.uuid4().hex}.com/api"
        self.telegram_token = f"{random.randint(100000, 999999)}:{uuid.uuid4().hex[:10]}"
        self.chat_id = f"@{uuid.uuid4().hex[:8]}"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_market_parser_fetch_and_store_and_load(self):
        parser = MarketParser(self.storage_file)
        random_price = round(random.uniform(10.0, 1000.0), 4)
        
        parser.fetch_and_store(self.symbol, random_price)
        data = parser.load_data(self.storage_file)
        
        self.assertIsInstance(data, dict)
        self.assertIn(self.symbol, data)
        self.assertEqual(data[self.symbol], random_price)

    def test_market_parser_load_data_invalid_json(self):
        corrupted_content = f"{{invalid_json_{uuid.uuid4().hex}"
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(corrupted_content)
            
        parser = MarketParser(self.storage_file)
        data = parser.load_data(self.storage_file)
        self.assertEqual(data, {})

    def test_market_parser_load_data_empty_file(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("   ")
            
        parser = MarketParser(self.storage_file)
        data = parser.load_data(self.storage_file)
        self.assertEqual(data, {})

    def test_market_parser_load_data_non_existent(self):
        non_file = f"{uuid.uuid4().hex}.json"
        parser = MarketParser(non_file)
        data = parser.load_data(non_file)
        self.assertIsNone(data)

    def test_market_report_generator_symbol_report(self):
        parser = MarketParser(self.storage_file)
        random_price = round(random.uniform(1.0, 500.0), 2)
        parser.fetch_and_store(self.symbol, random_price)
        
        gen = MarketReportGenerator(self.storage_file)
        report = gen.generate_symbol_report(self.symbol)
        
        self.assertIn(self.symbol, report)
        self.assertIn(str(random_price), report)

    def test_market_report_generator_symbol_report_no_data(self):
        gen = MarketReportGenerator(self.storage_file)
        report = gen.generate_symbol_report(self.symbol)
        self.assertIn("No data", report)

    def test_market_report_generator_get_raw_stream_dump(self):
        random_text = uuid.uuid4().hex
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(random_text)
            
        gen = MarketReportGenerator(self.storage_file)
        dump = gen.get_raw_stream_dump()
        self.assertEqual(dump, random_text)

    def test_market_report_generator_get_raw_stream_dump_none(self):
        gen = MarketReportGenerator(storage_file=None)
        dump = gen.get_raw_stream_dump()
        self.assertEqual(dump, "{}")

    def test_generate_market_report_wrapper(self):
        parser = MarketParser(self.storage_file)
        val = random.randint(100, 999)
        parser.fetch_and_store(self.symbol, val)
        
        res = generate_market_report(self.storage_file, self.symbol)
        self.assertIn(str(val), res)

    def test_run_market_telegram_pipeline(self):
        parser = MarketParser(self.storage_file)
        price_val = round(random.uniform(50.0, 150.0), 2)
        parser.fetch_and_store(self.symbol, price_val)
        
        result = run_market_telegram_pipeline(
            storage_file=self.storage_file,
            symbol=self.symbol,
            chat_id=self.chat_id,
            url=self.url,
            telegram_token=self.telegram_token
        )
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["symbol"], self.symbol)
        self.assertEqual(result["price"], price_val)
        self.assertEqual(result["chat_id"], self.chat_id)
        self.assertEqual(result["url"], self.url)

    def test_run_pipeline_execution(self):
        parser = MarketParser(self.storage_file)
        initial_price = round(random.uniform(10.0, 50.0), 2)
        parser.fetch_and_store(self.symbol, initial_price)
        
        success = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(success)

    def test_start_new_and_ened_aliases(self):
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, 123.45)
        
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

    def test_export_audit_logs_valid_dict(self):
        data = {self.symbol: random.randint(1, 100)}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(data, f)
            
        self.assertTrue(export_audit_logs(self.storage_file))

    def test_export_audit_logs_empty(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("   ")
            
        self.assertFalse(export_audit_logs(self.storage_file))

    def test_export_audit_logs_non_existent(self):
        self.assertFalse(export_audit_logs(f"{uuid.uuid4().hex}.json"))

    def test_export_audit_logs_malformed_bracket(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("{unclosed_json")
            
        self.assertTrue(export_audit_logs(self.storage_file))

if __name__ == '__main__':
    unittest.main()