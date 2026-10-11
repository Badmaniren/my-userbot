import unittest
from unittest.mock import patch
import os
import io
import json
import uuid
import random
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

class TestMarketPortfolioMonitorInquisitor(unittest.TestCase):

    def setUp(self):
        self.rand_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.rand_url = f"https://{uuid.uuid4().hex}.com/api"
        self.rand_token = uuid.uuid4().hex
        self.rand_chat_id = str(random.randint(100000, 999999))
        self.rand_storage = f"{uuid.uuid4().hex}.json"
        self.rand_price = round(random.uniform(10.0, 1500.0), 2)

    def tearDown(self):
        if os.path.exists(self.rand_storage):
            try:
                os.remove(self.rand_storage)
            except OSError:
                pass

    def test_market_parser_fetch_and_load_roundtrip(self):
        parser = MarketParser(storage_file=self.rand_storage)
        parser.fetch_and_store(symbol=self.rand_symbol, price=self.rand_price)
        
        data = parser.load_data(storage_file=self.rand_storage)
        self.assertIsInstance(data, dict)
        self.assertIn(self.rand_symbol, data)
        self.assertEqual(data[self.rand_symbol], self.rand_price)

    def test_market_parser_load_data_none_storage(self):
        parser = MarketParser(storage_file=None)
        res = parser.load_data(None)
        self.assertIsNone(res)

    def test_market_parser_corrupted_json_handling(self):
        corrupted_content = f"{{invalid_json_stream_{uuid.uuid4().hex}}"
        with open(self.rand_storage, "w", encoding="utf-8") as f:
            f.write(corrupted_content)
        
        parser = MarketParser(storage_file=self.rand_storage)
        data = parser.load_data(storage_file=self.rand_storage)
        self.assertEqual(data, {})

    def test_market_parser_binary_stream_decoding(self):
        trash_bytes = uuid.uuid4().bytes
        with patch("builtins.open", unittest.mock.mock_open(read_data=trash_bytes)):
            parser = MarketParser(storage_file=self.rand_storage)
            with open(self.rand_storage, "rb") as f:
                content = parser._read_content(f)
                self.assertIsInstance(content, str)

    def test_market_report_generator_symbol_report(self):
        parser = MarketParser(storage_file=self.rand_storage)
        parser.fetch_and_store(symbol=self.rand_symbol, price=self.rand_price)
        
        gen = MarketReportGenerator(storage_file=self.rand_storage)
        report = gen.generate_symbol_report(symbol=self.rand_symbol)
        self.assertIn(self.rand_symbol, report)
        self.assertIn(str(self.rand_price), report)

    def test_market_report_generator_no_data(self):
        gen = MarketReportGenerator(storage_file=self.rand_storage)
        report = gen.generate_symbol_report(symbol=self.rand_symbol)
        self.assertIn("No data", report)

    def test_market_report_generator_raw_stream_dump(self):
        parser = MarketParser(storage_file=self.rand_storage)
        parser.fetch_and_store(symbol=self.rand_symbol, price=self.rand_price)
        
        gen = MarketReportGenerator(storage_file=self.rand_storage)
        dump = gen.get_raw_stream_dump()
        self.assertIn(self.rand_symbol, dump)
        self.assertIn(str(self.rand_price), dump)

    def test_generate_market_report_helper(self):
        parser = MarketParser(storage_file=self.rand_storage)
        parser.fetch_and_store(symbol=self.rand_symbol, price=self.rand_price)
        
        report = generate_market_report(storage_file=self.rand_storage, symbol=self.rand_symbol)
        self.assertIn(self.rand_symbol, report)

    def test_run_market_telegram_pipeline(self):
        parser = MarketParser(storage_file=self.rand_storage)
        parser.fetch_and_store(symbol=self.rand_symbol, price=self.rand_price)
        
        result = run_market_telegram_pipeline(
            storage_file=self.rand_storage,
            symbol=self.rand_symbol,
            chat_id=self.rand_chat_id,
            url=self.rand_url,
            telegram_token=self.rand_token
        )
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["symbol"], self.rand_symbol)
        self.assertEqual(result["price"], self.rand_price)
        self.assertEqual(result["chat_id"], self.rand_chat_id)
        self.assertEqual(result["url"], self.rand_url)

    def test_export_audit_logs_valid(self):
        parser = MarketParser(storage_file=self.rand_storage)
        parser.fetch_and_store(symbol=self.rand_symbol, price=self.rand_price)
        
        res = export_audit_logs(storage_file=self.rand_storage)
        self.assertTrue(res)

    def test_export_audit_logs_invalid(self):
        with open(self.rand_storage, "w", encoding="utf-8") as f:
            f.write(uuid.uuid4().hex)
            
        res = export_audit_logs(storage_file=self.rand_storage)
        self.assertFalse(res)

    def test_run_pipeline_integration(self):
        parser = MarketParser(storage_file=self.rand_storage)
        parser.fetch_and_store(symbol=self.rand_symbol, price=self.rand_price)
        
        pipeline_res = run_pipeline(
            symbol=self.rand_symbol,
            url=self.rand_url,
            telegram_token=self.rand_token,
            chat_id=self.rand_chat_id,
            storage_file=self.rand_storage
        )
        self.assertTrue(pipeline_res)

    def test_start_new_and_ened_aliases(self):
        parser = MarketParser(storage_file=self.rand_storage)
        parser.fetch_and_store(symbol=self.rand_symbol, price=self.rand_price)
        
        res_new = start_new(
            symbol=self.rand_symbol,
            url=self.rand_url,
            telegram_token=self.rand_token,
            chat_id=self.rand_chat_id,
            storage_file=self.rand_storage
        )
        self.assertTrue(res_new)
        
        res_ened = start_ened(
            symbol=self.rand_symbol,
            url=self.rand_url,
            telegram_token=self.rand_token,
            chat_id=self.rand_chat_id,
            storage_file=self.rand_storage
        )
        self.assertTrue(res_ened)

if __name__ == "__main__":
    unittest.main()