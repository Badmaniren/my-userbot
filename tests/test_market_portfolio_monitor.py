import unittest
from unittest.mock import patch
import os
import json
import uuid
import random
import io
import sys

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
        self.telegram_token = f"{random.randint(1000, 9999)}:{uuid.uuid4().hex[:10]}"
        self.chat_id = str(random.randint(100000, 999999))
        self.storage_file = f"storage_{uuid.uuid4().hex[:8]}.json"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_market_parser_fetch_and_store_and_load(self):
        price = round(random.uniform(10.0, 1000.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=price)

        self.assertTrue(os.path.exists(self.storage_file))
        loaded_data = parser.load_data(self.storage_file)
        self.assertIsInstance(loaded_data, dict)
        self.assertIn(self.symbol, loaded_data)
        self.assertEqual(loaded_data[self.symbol], price)

    def test_market_parser_load_data_empty_or_nonexistent(self):
        parser = MarketParser(storage_file=self.storage_file)
        res_nonexistent = parser.load_data(self.storage_file)
        self.assertIsNone(res_nonexistent)

        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("   ")
        res_empty = parser.load_data(self.storage_file)
        self.assertEqual(res_empty, {})

    def test_market_parser_load_data_corrupted_json(self):
        parser = MarketParser(storage_file=self.storage_file)
        garbage = uuid.uuid4().hex
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(garbage)
        res_corrupt = parser.load_data(self.storage_file)
        self.assertIsNone(res_corrupt)

    def test_market_report_generator_symbol_report(self):
        price = round(random.uniform(1.0, 500.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=price)

        gen = MarketReportGenerator(storage_file=self.storage_file)
        report = gen.generate_symbol_report(symbol=self.symbol)
        self.assertIn(self.symbol, report)
        self.assertIn(str(price), report)

    def test_market_report_generator_no_data(self):
        gen = MarketReportGenerator(storage_file=self.storage_file)
        report = gen.generate_symbol_report(symbol=self.symbol)
        self.assertIn(self.symbol, report)
        self.assertIn("No data", report)

    def test_market_report_generator_get_raw_stream_dump(self):
        gen = MarketReportGenerator(storage_file=self.storage_file)
        dump_empty = gen.get_raw_stream_dump()
        self.assertEqual(dump_empty, "{}")

        price = round(random.uniform(50.0, 150.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=price)

        dump_filled = gen.get_raw_stream_dump()
        self.assertIn(self.symbol, dump_filled)
        self.assertIn(str(price), dump_filled)

    def test_generate_market_report_function(self):
        price = round(random.uniform(0.1, 99.9), 4)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=price)

        result = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
        self.assertIn(self.symbol, result)
        self.assertIn(str(price), result)

    def test_run_market_telegram_pipeline(self):
        price = round(random.uniform(100.0, 200.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=price)

        res = run_market_telegram_pipeline(
            storage_file=self.storage_file,
            symbol=self.symbol,
            chat_id=self.chat_id,
            url=self.url,
            telegram_token=self.telegram_token
        )
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("status"), "success")
        self.assertEqual(res.get("symbol"), self.symbol)
        self.assertEqual(res.get("price"), price)
        self.assertEqual(res.get("chat_id"), self.chat_id)
        self.assertEqual(res.get("url"), self.url)

    def test_export_audit_logs_valid_and_invalid(self):
        self.assertFalse(export_audit_logs(storage_file=self.storage_file))

        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("   ")
        self.assertFalse(export_audit_logs(storage_file=self.storage_file))

        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(uuid.uuid4().hex)
        self.assertFalse(export_audit_logs(storage_file=self.storage_file))

        valid_data = {uuid.uuid4().hex: random.randint(1, 100)}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(valid_data, f)
        self.assertTrue(export_audit_logs(storage_file=self.storage_file))

    def test_run_pipeline(self):
        price = round(random.uniform(1000.0, 5000.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=price)

        status = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(status)

    def test_start_new_and_start_ened(self):
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

    def test_market_parser_with_bytes_io_mock(self):
        random_bytes = json.dumps({self.symbol: random.randint(10, 500)}).encode("utf-8")
        with patch("builtins.open", return_value=io.BytesIO(random_bytes) if sys.version_info[0] < 3 else io.StringIO(random_bytes.decode("utf-8"))):
            with patch("os.path.exists", return_value=True):
                parser = MarketParser(storage_file=self.storage_file)
                data = parser.load_data(self.storage_file)
                self.assertIsInstance(data, dict)