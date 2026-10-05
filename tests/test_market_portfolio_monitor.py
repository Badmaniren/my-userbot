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
        self.random_prefix = uuid.uuid4().hex[:8]
        self.storage_file = f"test_storage_{self.random_prefix}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://{uuid.uuid4().hex[:8]}.com/api"
        self.telegram_token = uuid.uuid4().hex
        self.chat_id = str(random.randint(100000, 999999))
        self.price = round(random.uniform(10.0, 1000.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_market_parser_fetch_and_store_and_load(self):
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, self.price)
        
        data = parser.load_data(self.storage_file)
        self.assertIsInstance(data, dict)
        self.assertIn(self.symbol, data)
        self.assertEqual(data[self.symbol], self.price)

    def test_market_parser_load_data_nonexistent(self):
        fake_path = f"nonexistent_{uuid.uuid4().hex}.json"
        parser = MarketParser(fake_path)
        data = parser.load_data(fake_path)
        self.assertEqual(data, {})

    def test_market_parser_load_data_corrupted_json(self):
        corrupted_data = f"{{invalid_json_{uuid.uuid4().hex}"
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(corrupted_data)
        
        parser = MarketParser(self.storage_file)
        data = parser.load_data(self.storage_file)
        self.assertEqual(data, {})

    def test_market_parser_load_data_none(self):
        parser = MarketParser(None)
        data = parser.load_data(None)
        self.assertIsNone(data)

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
        self.assertIn(self.symbol, dump)
        self.assertIn(str(self.price), dump)

    def test_market_report_generator_raw_stream_dump_none(self):
        gen = MarketReportGenerator(None)
        dump = gen.get_raw_stream_dump()
        self.assertEqual(dump, "{}")

    def test_generate_market_report_helper(self):
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, self.price)
        
        res = generate_market_report(self.storage_file, self.symbol)
        self.assertIn(self.symbol, res)
        self.assertIn(str(self.price), res)

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
        self.assertIsInstance(res, dict)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["symbol"], self.symbol)
        self.assertEqual(res["price"], self.price)
        self.assertEqual(res["chat_id"], self.chat_id)
        self.assertEqual(res["url"], self.url)

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

    def test_export_audit_logs_valid(self):
        data = {self.symbol: self.price}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(data, f)
        
        res = export_audit_logs(self.storage_file)
        self.assertTrue(res)

    def test_export_audit_logs_empty(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("   ")
        
        res = export_audit_logs(self.storage_file)
        self.assertFalse(res)

    def test_export_audit_logs_malformed(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(f"{{unclosed_json_{uuid.uuid4().hex}")
        
        res = export_audit_logs(self.storage_file)
        self.assertTrue(res)

    def test_export_audit_logs_nonexistent(self):
        fake_path = f"absent_{uuid.uuid4().hex}.json"
        res = export_audit_logs(fake_path)
        self.assertFalse(res)

    def test_stream_read_with_mock_bytes_io(self):
        random_bytes = json.dumps({self.symbol: self.price}).encode("utf-8")
        mock_file = io.BytesIO(random_bytes)
        
        with patch("builtins.open", return_value=mock_file):
            parser = MarketParser(self.storage_file)
            data = parser.load_data(self.storage_file)
            self.assertEqual(data.get(self.symbol), self.price)

if __name__ == "__main__":
    unittest.main()