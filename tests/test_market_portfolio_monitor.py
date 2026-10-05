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
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://api.{uuid.uuid4().hex[:8]}.com/v1"
        self.telegram_token = f"{random.randint(100000, 999999)}:AA{uuid.uuid4().hex[:10]}"
        self.chat_id = str(random.randint(10000000, 99999999))
        self.storage_file = f"storage_{uuid.uuid4().hex}.json"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_market_parser_load_data_nonexistent(self):
        random_file = f"nonexistent_{uuid.uuid4().hex}.json"
        parser = MarketParser(storage_file=random_file)
        res = parser.load_data(random_file)
        self.assertEqual(res, {})

    def test_market_parser_load_data_none(self):
        parser = MarketParser(storage_file=None)
        res = parser.load_data(None)
        self.assertIsNone(res)

    def test_market_parser_fetch_and_store_and_load(self):
        parser = MarketParser(storage_file=self.storage_file)
        price = round(random.uniform(1.0, 1000.0), 4)
        parser.fetch_and_store(symbol=self.symbol, price=price)
        
        loaded = parser.load_data(self.storage_file)
        self.assertIsInstance(loaded, dict)
        self.assertIn(self.symbol, loaded)
        self.assertEqual(loaded[self.symbol], price)

    def test_market_parser_corrupted_json(self):
        bad_content = f"{{invalid_json_{uuid.uuid4().hex}"
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(bad_content)
        
        parser = MarketParser(storage_file=self.storage_file)
        loaded = parser.load_data(self.storage_file)
        self.assertEqual(loaded, {})

    def test_market_report_generator_symbol(self):
        parser = MarketParser(storage_file=self.storage_file)
        price = round(random.uniform(10.0, 500.0), 2)
        parser.fetch_and_store(symbol=self.symbol, price=price)
        
        gen = MarketReportGenerator(storage_file=self.storage_file)
        report = gen.generate_symbol_report(self.symbol)
        self.assertIn(self.symbol, report)
        self.assertIn(str(price), report)

    def test_market_report_generator_no_data(self):
        gen = MarketReportGenerator(storage_file=self.storage_file)
        report = gen.generate_symbol_report(self.symbol)
        self.assertIn(self.symbol, report)
        self.assertIn("No data", report)

    def test_get_raw_stream_dump_empty(self):
        gen = MarketReportGenerator(storage_file=None)
        dump = gen.get_raw_stream_dump()
        self.assertEqual(dump, "{}")

    def test_get_raw_stream_dump_with_file(self):
        expected_content = json.dumps({self.symbol: random.randint(1, 100)})
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(expected_content)
        
        gen = MarketReportGenerator(storage_file=self.storage_file)
        dump = gen.get_raw_stream_dump()
        self.assertEqual(dump, expected_content)

    def test_generate_market_report_helper(self):
        parser = MarketParser(storage_file=self.storage_file)
        price = round(random.uniform(5.0, 50.0), 2)
        parser.fetch_and_store(symbol=self.symbol, price=price)

        report = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
        self.assertIn(self.symbol, report)

    def test_run_market_telegram_pipeline(self):
        parser = MarketParser(storage_file=self.storage_file)
        price = round(random.uniform(100.0, 200.0), 2)
        parser.fetch_and_store(symbol=self.symbol, price=price)

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
        self.assertEqual(result.get("price"), price)
        self.assertEqual(result.get("chat_id"), self.chat_id)
        self.assertEqual(result.get("url"), self.url)

    def test_export_audit_logs_invalid(self):
        res = export_audit_logs(storage_file=None)
        self.assertFalse(res)

        empty_file = f"empty_{uuid.uuid4().hex}.json"
        with open(empty_file, "w", encoding="utf-8") as f:
            f.write("   ")
        try:
            res_empty = export_audit_logs(storage_file=empty_file)
            self.assertFalse(res_empty)
        finally:
            if os.path.exists(empty_file):
                os.remove(empty_file)

    def test_export_audit_logs_valid(self):
        data = {uuid.uuid4().hex: random.randint(1, 100)}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(data, f)

        res = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(res)

    def test_run_pipeline(self):
        res = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res)

    def test_start_new(self):
        res = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res)

    def test_start_ened(self):
        res = start_ened(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res)

    def test_io_bytes_stream_mocking(self):
        garbage_bytes = io.BytesIO(uuid.uuid4().bytes)
        with patch("builtins.open", return_value=io.StringIO(garbage_bytes.read().hex())):
            parser = MarketParser(storage_file=self.storage_file)
            data = parser.load_data(self.storage_file)
            self.assertEqual(data, {})

if __name__ == "__main__":
    unittest.main()