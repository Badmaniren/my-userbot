import unittest
from unittest.mock import patch
import json
import os
import io
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


class TestMarketPortfolioMonitor(unittest.TestCase):

    def setUp(self):
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://{uuid.uuid4().hex[:8]}.com/api"
        self.telegram_token = f"{random.randint(10000, 99999)}:ABC{uuid.uuid4().hex[:6]}"
        self.chat_id = f"@{uuid.uuid4().hex[:6]}"
        self.storage_file = f"storage_{uuid.uuid4().hex[:8]}.json"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_market_parser_load_data_none_or_missing(self):
        parser = MarketParser(storage_file=self.storage_file)
        res = parser.load_data(None)
        self.assertIsNone(res)

        non_existent = f"missing_{uuid.uuid4().hex}.json"
        res2 = parser.load_data(non_existent)
        self.assertIsNone(res2)

    def test_market_parser_fetch_and_store_valid(self):
        price = round(random.uniform(10.0, 1000.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=price)

        self.assertTrue(os.path.exists(self.storage_file))
        data = parser.load_data(self.storage_file)
        self.assertIsInstance(data, dict)
        self.assertIn(self.symbol, data)
        self.assertEqual(data[self.symbol], price)

    def test_market_parser_unterminated_json(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write('{"unterminated": 123')

        parser = MarketParser(storage_file=self.storage_file)
        with self.assertRaises(json.JSONDecodeError):
            parser.load_data(self.storage_file)

        with self.assertRaises(json.JSONDecodeError):
            parser.fetch_and_store(self.symbol, 50.0)

    def test_market_report_generator_symbol_report(self):
        price = round(random.uniform(1.0, 500.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=price)

        gen = MarketReportGenerator(storage_file=self.storage_file)
        report = gen.generate_symbol_report(self.symbol)
        self.assertIn(self.symbol, report)
        self.assertIn(str(price), report)

        other_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        no_data_report = gen.generate_symbol_report(other_symbol)
        self.assertIn("No data", no_data_report)

    def test_market_report_generator_raw_stream_dump(self):
        gen = MarketReportGenerator(storage_file=self.storage_file)
        dump_empty = gen.get_raw_stream_dump()
        self.assertEqual(dump_empty, "{}")

        price = round(random.uniform(5.0, 50.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=price)

        dump = gen.get_raw_stream_dump()
        self.assertIn(self.symbol, dump)
        self.assertIn(str(price), dump)

    def test_generate_market_report_wrapper(self):
        price = round(random.uniform(100.0, 200.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=price)

        rep = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
        self.assertIn(self.symbol, rep)
        self.assertIn(str(price), rep)

    def test_run_market_telegram_pipeline(self):
        price = round(random.uniform(0.1, 99.9), 2)
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

    def test_run_pipeline_and_aliases(self):
        res_pipeline = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res_pipeline)

        res_start_new = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res_start_new)

        res_start_ened = start_ened(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res_start_ened)

    def test_export_audit_logs(self):
        self.assertFalse(export_audit_logs(None))
        self.assertFalse(export_audit_logs(f"fake_{uuid.uuid4().hex}.json"))

        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("   \n  ")
        self.assertFalse(export_audit_logs(self.storage_file))

        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write('{"bad_json":')
        self.assertFalse(export_audit_logs(self.storage_file))

        payload = {self.symbol: random.randint(1, 100)}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(payload, f)
        self.assertTrue(export_audit_logs(self.storage_file))

    def test_stream_bytes_io_mocking(self):
        random_bytes = json.dumps({self.symbol: round(random.uniform(1.0, 10.0), 2)}).encode("utf-8")
        stream = io.BytesIO(random_bytes)

        with patch("builtins.open", return_value=stream):
            parser = MarketParser(storage_file=self.storage_file)
            data = parser.load_data(self.storage_file)
            self.assertIsNotNone(data)
            self.assertIsInstance(data, dict)
            self.assertIn(self.symbol, data)