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
        self.url = f"https://{uuid.uuid4().hex[:8]}.com/api"
        self.telegram_token = f"{random.randint(100000, 999999)}:{uuid.uuid4().hex[:10]}"
        self.chat_id = str(random.randint(10000000, 99999999))
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"
        self.price = round(random.uniform(10.0, 1500.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_market_parser_fetch_and_load(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)
        
        loaded_data = parser.load_data(storage_file=self.storage_file)
        self.assertIsInstance(loaded_data, dict)
        self.assertIn(self.symbol, loaded_data)
        self.assertEqual(loaded_data[self.symbol], self.price)

    def test_market_parser_load_nonexistent_file(self):
        non_existent = f"missing_{uuid.uuid4().hex}.json"
        parser = MarketParser(storage_file=non_existent)
        data = parser.load_data(storage_file=non_existent)
        self.assertIsNone(data)

    def test_market_parser_load_corrupted_json(self):
        corrupted_data = f"invalid_json_{uuid.uuid4().hex}"
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(corrupted_data)
        
        parser = MarketParser(storage_file=self.storage_file)
        data = parser.load_data(storage_file=self.storage_file)
        self.assertIsNone(data)

    def test_market_report_generator_symbol_report(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)
        
        gen = MarketReportGenerator(storage_file=self.storage_file)
        report = gen.generate_symbol_report(symbol=self.symbol)
        self.assertIn(self.symbol, report)
        self.assertIn(str(self.price), report)

    def test_market_report_generator_no_data(self):
        gen = MarketReportGenerator(storage_file=self.storage_file)
        report = gen.generate_symbol_report(symbol=self.symbol)
        self.assertIn("No data", report)

    def test_market_report_generator_get_raw_stream_dump(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)
        
        gen = MarketReportGenerator(storage_file=self.storage_file)
        dump = gen.get_raw_stream_dump()
        self.assertIn(self.symbol, dump)
        self.assertIn(str(self.price), dump)

    def test_generate_market_report_function(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)
        
        report = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
        self.assertIn(self.symbol, report)

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
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["symbol"], self.symbol)
        self.assertEqual(result["price"], self.price)
        self.assertEqual(result["chat_id"], self.chat_id)
        self.assertEqual(result["url"], self.url)

    def test_export_audit_logs_valid(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)
        
        res = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(res)

    def test_export_audit_logs_invalid(self):
        res = export_audit_logs(storage_file=None)
        self.assertFalse(res)

        non_existent = f"fake_{uuid.uuid4().hex}.json"
        res2 = export_audit_logs(storage_file=non_existent)
        self.assertFalse(res2)

    def test_run_pipeline_execution(self):
        res = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res)

    def test_start_new_execution(self):
        res = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res)

    def test_start_ened_alias(self):
        res = start_ened(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res)

    def test_market_parser_with_stream_mock(self):
        random_bytes = io.BytesIO(json.dumps({self.symbol: self.price}).encode('utf-8'))
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', return_value=random_bytes):
                parser = MarketParser(storage_file=self.storage_file)
                data = parser.load_data(storage_file=self.storage_file)
                self.assertEqual(data[self.symbol], self.price)

if __name__ == '__main__':
    unittest.main()