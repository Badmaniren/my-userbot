import unittest
from unittest.mock import patch
import json
import os
import io
import uuid
import random
import string

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
        self.random_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.random_url = f"https://api.{uuid.uuid4().hex[:8]}.com/v1"
        self.random_token = f"{random.randint(100000, 999999)}:AA{uuid.uuid4().hex[:20]}"
        self.random_chat_id = str(random.randint(1000000, 99999999))
        self.random_storage_file = f"temp_storage_{uuid.uuid4().hex}.json"

    def tearDown(self):
        if os.path.exists(self.random_storage_file):
            try:
                os.remove(self.random_storage_file)
            except OSError:
                pass

    def test_market_parser_load_data_none_and_missing(self):
        parser = MarketParser(self.random_storage_file)
        self.assertIsNone(parser.load_data(None))
        self.assertEqual(parser.load_data(self.random_storage_file), {})

    def test_market_parser_fetch_and_load_valid_json(self):
        random_price = round(random.uniform(10.0, 1000.0), 4)
        parser = MarketParser(self.random_storage_file)
        parser.fetch_and_store(self.random_symbol, random_price)
        
        loaded_data = parser.load_data(self.random_storage_file)
        self.assertIsInstance(loaded_data, dict)
        self.assertIn(self.random_symbol, loaded_data)
        self.assertEqual(loaded_data[self.random_symbol], random_price)

    def test_market_parser_load_corrupted_json(self):
        corrupted_content = f"{{invalid_json_{uuid.uuid4().hex}}"
        with open(self.random_storage_file, "w", encoding="utf-8") as f:
            f.write(corrupted_content)
        
        parser = MarketParser(self.random_storage_file)
        loaded_data = parser.load_data(self.random_storage_file)
        self.assertEqual(loaded_data, {})

    def test_market_parser_load_bytes_stream(self):
        random_price = round(random.uniform(1.0, 50.0), 2)
        payload = json.dumps({self.random_symbol: random_price}).encode("utf-8")
        
        parser = MarketParser(None)
        with patch("builtins.open", unittest.mock.mock_open(read_data=payload)) as mock_file:
            with patch("os.path.exists", return_value=True):
                loaded = parser.load_data(self.random_storage_file)
                self.assertIsInstance(loaded, dict)
                self.assertEqual(loaded.get(self.random_symbol), random_price)

    def test_market_report_generator_symbol_report(self):
        random_price = round(random.uniform(500.0, 5000.0), 2)
        parser = MarketParser(self.random_storage_file)
        parser.fetch_and_store(self.random_symbol, random_price)

        report_gen = MarketReportGenerator(storage_file=self.random_storage_file)
        report = report_gen.generate_symbol_report(self.random_symbol)
        
        self.assertIn(self.random_symbol, report)
        self.assertIn(str(random_price), report)

    def test_market_report_generator_no_data_report(self):
        report_gen = MarketReportGenerator(storage_file=self.random_storage_file)
        report = report_gen.generate_symbol_report(self.random_symbol)
        self.assertIn("No data", report)

    def test_market_report_generator_get_raw_stream_dump(self):
        random_text = ''.join(random.choices(string.ascii_letters + string.digits, k=30))
        with open(self.random_storage_file, "w", encoding="utf-8") as f:
            f.write(random_text)

        report_gen = MarketReportGenerator(storage_file=self.random_storage_file)
        dump = report_gen.get_raw_stream_dump()
        self.assertEqual(dump, random_text)

    def test_generate_market_report_helper(self):
        random_price = round(random.uniform(0.1, 99.9), 2)
        parser = MarketParser(self.random_storage_file)
        parser.fetch_and_store(self.random_symbol, random_price)

        res = generate_market_report(storage_file=self.random_storage_file, symbol=self.random_symbol)
        self.assertIn(self.random_symbol, res)

    def test_run_market_telegram_pipeline(self):
        random_price = round(random.uniform(100.0, 200.0), 2)
        parser = MarketParser(self.random_storage_file)
        parser.fetch_and_store(self.random_symbol, random_price)

        pipeline_res = run_market_telegram_pipeline(
            storage_file=self.random_storage_file,
            symbol=self.random_symbol,
            chat_id=self.random_chat_id,
            url=self.random_url,
            telegram_token=self.random_token
        )

        self.assertEqual(pipeline_res["status"], "success")
        self.assertEqual(pipeline_res["symbol"], self.random_symbol)
        self.assertEqual(pipeline_res["price"], random_price)
        self.assertEqual(pipeline_res["chat_id"], self.random_chat_id)
        self.assertEqual(pipeline_res["url"], self.random_url)

    def test_export_audit_logs_valid(self):
        parser = MarketParser(self.random_storage_file)
        parser.fetch_and_store(self.random_symbol, 123.45)
        
        audit_res = export_audit_logs(storage_file=self.random_storage_file)
        self.assertTrue(audit_res)

    def test_export_audit_logs_empty(self):
        with open(self.random_storage_file, "w", encoding="utf-8") as f:
            f.write("   ")
        audit_res = export_audit_logs(storage_file=self.random_storage_file)
        self.assertFalse(audit_res)

    def test_run_pipeline_execution(self):
        res = run_pipeline(
            symbol=self.random_symbol,
            url=self.random_url,
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            storage_file=self.random_storage_file
        )
        self.assertTrue(res)

    def test_start_new_and_ened_aliases(self):
        res_new = start_new(
            symbol=self.random_symbol,
            url=self.random_url,
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            storage_file=self.random_storage_file
        )
        self.assertTrue(res_new)

        res_ened = start_ened(
            symbol=self.random_symbol,
            url=self.random_url,
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            storage_file=self.random_storage_file
        )
        self.assertTrue(res_ened)

if __name__ == "__main__":
    unittest.main()