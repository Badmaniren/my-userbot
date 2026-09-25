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
    export_audit_logs,
)


class TestMarketPortfolioMonitor(unittest.TestCase):

    def setUp(self):
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://example.com/api/{uuid.uuid4().hex[:8]}"
        self.telegram_token = f"{random.randint(100000, 999999)}:ABC-{uuid.uuid4().hex[:6]}"
        self.chat_id = str(random.randint(10000000, 99999999))
        self.storage_file = f"test_storage_{uuid.uuid4().hex[:8]}.json"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_market_parser_fetch_and_store(self):
        price = round(random.uniform(10.0, 1000.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=price)

        self.assertTrue(os.path.exists(self.storage_file))
        data = parser.load_data(self.storage_file)
        self.assertIsInstance(data, dict)
        self.assertIn(self.symbol, data)
        self.assertEqual(data[self.symbol], price)

    def test_market_parser_load_data_invalid(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(f"INVALID_JSON_{uuid.uuid4().hex}")

        parser = MarketParser(storage_file=self.storage_file)
        data = parser.load_data(self.storage_file)
        self.assertIsNone(data)

    def test_market_report_generator_symbol_report(self):
        price = round(random.uniform(1.0, 500.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=price)

        report_gen = MarketReportGenerator(storage_file=self.storage_file)
        report = report_gen.generate_symbol_report(symbol=self.symbol)
        self.assertIn(self.symbol, report)
        self.assertIn(str(price), report)

    def test_market_report_generator_no_data(self):
        report_gen = MarketReportGenerator(storage_file=self.storage_file)
        report = report_gen.generate_symbol_report(symbol=self.symbol)
        self.assertIn(self.symbol, report)
        self.assertIn("No data", report)

    def test_market_report_generator_get_raw_stream_dump(self):
        price = round(random.uniform(1.0, 100.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=price)

        report_gen = MarketReportGenerator(storage_file=self.storage_file)
        dump = report_gen.get_raw_stream_dump()
        self.assertIsInstance(dump, str)
        self.assertIn(self.symbol, dump)

    def test_generate_market_report(self):
        price = round(random.uniform(50.0, 500.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=price)

        report = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
        self.assertIn(self.symbol, report)
        self.assertIn(str(price), report)

    def test_run_market_telegram_pipeline(self):
        price = round(random.uniform(10.0, 200.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
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

    def test_run_pipeline(self):
        res = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res)
        self.assertTrue(os.path.exists(self.storage_file))

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

    def test_export_audit_logs_nonexistent(self):
        non_existent = f"missing_{uuid.uuid4().hex}.json"
        res = export_audit_logs(storage_file=non_existent)
        self.assertFalse(res)

    def test_export_audit_logs_empty_file(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("")
        res = export_audit_logs(storage_file=self.storage_file)
        self.assertFalse(res)

    def test_export_audit_logs_empty_dict(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump({}, f)
        res = export_audit_logs(storage_file=self.storage_file)
        self.assertFalse(res)

    def test_export_audit_logs_valid_data(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=123.45)
        res = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(res)

    def test_mock_io_stream_dump(self):
        random_bytes = f"STREAM_DATA_{uuid.uuid4().hex}".encode("utf-8")
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", return_value=io.BytesIO(random_bytes)):
                report_gen = MarketReportGenerator(storage_file=self.storage_file)
                dump = report_gen.get_raw_stream_dump()
                self.assertIsInstance(dump, str)