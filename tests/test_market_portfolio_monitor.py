import unittest
from unittest.mock import patch
import os
import tempfile
import json
import uuid
import random
import io

from skills.market_portfolio_monitor import (
    MarketParser,
    MarketReportGenerator,
    run_pipeline,
    start_new,
    generate_market_report,
    run_market_telegram_pipeline,
    export_audit_logs
)


class TestMarketPortfolioMonitor(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.temp_dir.name, f"{uuid.uuid4().hex}.json")
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.price = round(random.uniform(10.0, 1500.0), 2)
        self.url = f"https://{uuid.uuid4().hex}.com/webhook"
        self.telegram_token = f"{random.randint(1000,9999)}:ABC-{uuid.uuid4().hex[:8]}"
        self.chat_id = str(random.randint(100000, 999999))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_market_parser_fetch_and_store_and_load(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)

        self.assertTrue(os.path.exists(self.storage_file))

        loaded_data = parser.load_data(storage_file=self.storage_file)
        self.assertIsInstance(loaded_data, dict)
        self.assertIn(self.symbol, loaded_data)
        self.assertEqual(loaded_data[self.symbol], self.price)

    def test_market_parser_load_data_nonexistent(self):
        nonexistent_file = os.path.join(self.temp_dir.name, f"{uuid.uuid4().hex}.json")
        parser = MarketParser(storage_file=nonexistent_file)
        data = parser.load_data(nonexistent_file)
        self.assertIsNone(data)

    def test_market_parser_load_data_corrupted(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(uuid.uuid4().hex)

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

    def test_market_report_generator_raw_stream_dump(self):
        dummy_content = uuid.uuid4().hex
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(dummy_content)

        gen = MarketReportGenerator(storage_file=self.storage_file)
        dump = gen.get_raw_stream_dump()
        self.assertEqual(dump, dummy_content)

    def test_market_report_generator_raw_stream_dump_io_error(self):
        gen = MarketReportGenerator(storage_file=self.storage_file)
        with patch("builtins.open", side_effect=IOError):
            dump = gen.get_raw_stream_dump()
            self.assertEqual(dump, "{}")

    def test_generate_market_report_helper(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)

        res = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
        self.assertIn(self.symbol, res)
        self.assertIn(str(self.price), res)

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

    def test_run_pipeline(self):
        success = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(success)

        parser = MarketParser(storage_file=self.storage_file)
        data = parser.load_data(self.storage_file)
        self.assertIn(self.symbol, data)

    def test_start_new(self):
        success = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(success)

    def test_export_audit_logs_success(self):
        dummy_content = uuid.uuid4().hex
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(dummy_content)

        res = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(res)

    def test_export_audit_logs_empty(self):
        res = export_audit_logs(storage_file=None)
        self.assertFalse(res)

        nonexistent = os.path.join(self.temp_dir.name, f"{uuid.uuid4().hex}.json")
        res2 = export_audit_logs(storage_file=nonexistent)
        self.assertFalse(res2)

    def test_export_audit_logs_io_error(self):
        with patch("builtins.open", side_effect=IOError):
            res = export_audit_logs(storage_file=self.storage_file)
            self.assertFalse(res)


if __name__ == "__main__":
    unittest.main()