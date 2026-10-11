import unittest
from unittest.mock import patch
import os
import json
import io
import random
import uuid
import string

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
        self.random_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.random_url = f"https://{uuid.uuid4().hex}.com/api"
        self.random_token = uuid.uuid4().hex
        self.random_chat_id = str(random.randint(100000, 999999))
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"
        self.random_price = round(random.uniform(10.0, 1000.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_market_parser_fetch_and_load(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.random_symbol, price=self.random_price)
        
        data = parser.load_data(storage_file=self.storage_file)
        self.assertIsInstance(data, dict)
        self.assertIn(self.random_symbol, data)
        self.assertEqual(data[self.random_symbol], self.random_price)

    def test_market_parser_load_nonexistent(self):
        missing_file = f"missing_{uuid.uuid4().hex}.json"
        parser = MarketParser(storage_file=missing_file)
        data = parser.load_data(storage_file=missing_file)
        self.assertEqual(data, {})

    def test_market_parser_load_corrupted_json(self):
        bad_content = uuid.uuid4().hex
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(bad_content)
            
        parser = MarketParser(storage_file=self.storage_file)
        data = parser.load_data(storage_file=self.storage_file)
        self.assertEqual(data, {})

    def test_market_parser_read_content_bytes(self):
        parser = MarketParser(storage_file=self.storage_file)
        random_bytes = uuid.uuid4().bytes
        stream = io.BytesIO(random_bytes)
        content = parser._read_content(stream)
        self.assertIsInstance(content, str)

    def test_market_report_generator_symbol(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.random_symbol, price=self.random_price)
        
        gen = MarketReportGenerator(storage_file=self.storage_file)
        report = gen.generate_symbol_report(symbol=self.random_symbol)
        self.assertIn(self.random_symbol, report)
        self.assertIn(str(self.random_price), report)

    def test_market_report_generator_no_data(self):
        gen = MarketReportGenerator(storage_file=self.storage_file)
        missing_symbol = uuid.uuid4().hex[:4].upper()
        report = gen.generate_symbol_report(symbol=missing_symbol)
        self.assertIn("No data", report)

    def test_market_report_get_raw_stream_dump(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.random_symbol, price=self.random_price)
        
        gen = MarketReportGenerator(storage_file=self.storage_file)
        dump = gen.get_raw_stream_dump()
        self.assertIsInstance(dump, str)
        self.assertIn(self.random_symbol, dump)

    def test_generate_market_report_wrapper(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.random_symbol, price=self.random_price)
        
        report = generate_market_report(storage_file=self.storage_file, symbol=self.random_symbol)
        self.assertIn(self.random_symbol, report)

    def test_run_market_telegram_pipeline(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.random_symbol, price=self.random_price)
        
        result = run_market_telegram_pipeline(
            storage_file=self.storage_file,
            symbol=self.random_symbol,
            chat_id=self.random_chat_id,
            url=self.random_url,
            telegram_token=self.random_token
        )
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("symbol"), self.random_symbol)
        self.assertEqual(result.get("price"), self.random_price)
        self.assertEqual(result.get("chat_id"), self.random_chat_id)
        self.assertEqual(result.get("url"), self.random_url)

    def test_export_audit_logs_valid(self):
        data = {self.random_symbol: self.random_price}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(data, f)
            
        res = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(res)

    def test_export_audit_logs_invalid(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("{invalid_json")
            
        res = export_audit_logs(storage_file=self.storage_file)
        self.assertFalse(res)

    def test_export_audit_logs_empty(self):
        res = export_audit_logs(storage_file=None)
        self.assertFalse(res)

    def test_run_pipeline(self):
        success = run_pipeline(
            symbol=self.random_symbol,
            url=self.random_url,
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(success)

    def test_start_new(self):
        success = start_new(
            symbol=self.random_symbol,
            url=self.random_url,
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(success)

    def test_start_ened(self):
        success = start_ened(
            symbol=self.random_symbol,
            url=self.random_url,
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(success)

if __name__ == "__main__":
    unittest.main()