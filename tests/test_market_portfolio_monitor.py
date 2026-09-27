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
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://{uuid.uuid4().hex[:8]}.com/api"
        self.telegram_token = f"{random.randint(100000, 999999)}:{uuid.uuid4().hex[:16]}"
        self.chat_id = f"@{uuid.uuid4().hex[:8]}"
        self.price = round(random.uniform(10.0, 5000.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_market_parser_fetch_and_load(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)
        
        data = parser.load_data(storage_file=self.storage_file)
        self.assertIsInstance(data, dict)
        self.assertIn(self.symbol, data)
        self.assertEqual(data[self.symbol], self.price)

    def test_market_parser_load_nonexistent(self):
        nonexistent = f"missing_{uuid.uuid4().hex}.json"
        parser = MarketParser(storage_file=nonexistent)
        data = parser.load_data(nonexistent)
        self.assertIsNone(data)

    def test_market_parser_load_corrupted_json(self):
        garbage_content = uuid.uuid4().hex
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(garbage_content)
        
        parser = MarketParser(storage_file=self.storage_file)
        data = parser.load_data(self.storage_file)
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
        
        self.assertIn(self.symbol, report)
        self.assertIn("No data", report)

    def test_market_report_generator_stream_dump(self):
        dump_content = json.dumps({self.symbol: self.price})
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(dump_content)
            
        gen = MarketReportGenerator(storage_file=self.storage_file)
        stream_data = gen.get_raw_stream_dump()
        
        self.assertIn(self.symbol, stream_data)
        self.assertIn(str(self.price), stream_data)

    def test_market_report_generator_stream_dump_io_error(self):
        gen = MarketReportGenerator(storage_file=f"invalid_{uuid.uuid4().hex}.json")
        with patch("builtins.open", side_effect=IOError):
            stream_data = gen.get_raw_stream_dump()
            self.assertEqual(stream_data, "{}")

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

    def test_export_audit_logs_valid(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(uuid.uuid4().hex)
            
        status = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(status)

    def test_export_audit_logs_empty(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("   ")
            
        status = export_audit_logs(storage_file=self.storage_file)
        self.assertFalse(status)

    def test_export_audit_logs_nonexistent(self):
        status = export_audit_logs(storage_file=f"missing_{uuid.uuid4().hex}.json")
        self.assertFalse(status)

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

    def test_market_parser_io_exception_handling(self):
        parser = MarketParser(storage_file=self.storage_file)
        with patch("builtins.open", side_effect=IOError):
            parser.fetch_and_store(symbol=self.symbol, price=self.price)
            data = parser.load_data(storage_file=self.storage_file)
            self.assertIsNone(data)


if __name__ == "__main__":
    unittest.main()