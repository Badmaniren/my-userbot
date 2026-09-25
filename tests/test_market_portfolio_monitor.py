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
        self.url = f"https://{uuid.uuid4().hex[:8]}.org/api"
        self.telegram_token = f"{random.randint(100000, 999999)}:{uuid.uuid4().hex[:10]}"
        self.chat_id = f"@{uuid.uuid4().hex[:6]}"
        self.storage_file = f"test_storage_{uuid.uuid4().hex[:8]}.json"

    def tearDown(slef):
        if os.path.exists(slef.storage_file):
            try:
                os.remove(slef.storage_file)
            except OSError:
                pass

    def test_run_pipeline_success(self):
        result = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.storage_file))

    def test_start_new_and_ened_aliases(self):
        res_new = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        res_ened = start_ened(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res_new)
        self.assertTrue(res_ened)

    def test_market_parser_fetch_and_load(self):
        parser = MarketParser(storage_file=self.storage_file)
        random_price = round(random.uniform(10.0, 5000.0), 2)
        parser.fetch_and_store(symbol=self.symbol, price=random_price)

        loaded_data = parser.load_data(self.storage_file)
        self.assertIsInstance(loaded_data, dict)
        self.assertIn(self.symbol, loaded_data)
        self.assertEqual(loaded_data[self.symbol], random_price)

    def test_market_parser_load_nonexistent(self):
        nonexistent_file = f"ghost_{uuid.uuid4().hex}.json"
        parser = MarketParser(storage_file=nonexistent_file)
        self.assertIsNone(parser.load_data(nonexistent_file))

    def test_market_parser_corrupted_json(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("{broken_json_content_" + uuid.uuid4().hex)

        parser = MarketParser(storage_file=self.storage_file)
        self.assertIsNone(parser.load_data(self.storage_file))

    def test_market_report_generator_symbol_report(self):
        random_price = round(random.uniform(1.0, 100.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=random_price)

        gen = MarketReportGenerator(storage_file=self.storage_file)
        report = gen.generate_symbol_report(symbol=self.symbol)
        self.assertIn(self.symbol, report)
        self.assertIn(str(random_price), report)

    def test_market_report_generator_no_data(self):
        gen = MarketReportGenerator(storage_file=self.storage_file)
        report = gen.generate_symbol_report(symbol=self.symbol)
        self.assertIn("No data", report)

    def test_market_report_generator_raw_stream_dump(self):
        random_price = round(random.uniform(50.0, 150.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=random_price)

        gen = MarketReportGenerator(storage_file=self.storage_file)
        dump = gen.get_raw_stream_dump()
        self.assertIsInstance(dump, str)
        self.assertIn(self.symbol, dump)

    def test_market_report_generator_raw_stream_dump_io_error(self):
        gen = MarketReportGenerator(storage_file=self.storage_file)
        with patch("builtins.open", side_effect=IOError("Simulated IO Error")):
            dump = gen.get_raw_stream_dump()
            self.assertEqual(dump, "{}")

    def test_generate_market_report_helper(self):
        random_price = round(random.uniform(200.0, 300.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=random_price)

        res = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
        self.assertIn(self.symbol, res)

    def test_run_market_telegram_pipeline(self):
        random_price = round(random.uniform(1000.0, 2000.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=random_price)

        pipeline_result = run_market_telegram_pipeline(
            storage_file=self.storage_file,
            symbol=self.symbol,
            chat_id=self.chat_id,
            url=self.url,
            telegram_token=self.telegram_token
        )

        self.assertEqual(pipeline_result["status"], "success")
        self.assertEqual(pipeline_result["symbol"], self.symbol)
        self.assertEqual(pipeline_result["price"], random_price)
        self.assertEqual(pipeline_result["chat_id"], self.chat_id)
        self.assertEqual(pipeline_result["url"], self.url)

    def test_export_audit_logs_valid(self):
        random_price = round(random.uniform(1.0, 10.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=random_price)

        export_result = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(export_result)

    def test_export_audit_logs_empty_or_missing(self):
        self.assertFalse(export_audit_logs(storage_file=None))
        self.assertFalse(export_audit_logs(storage_file=f"missing_{uuid.uuid4().hex}.json"))

        empty_file = f"empty_{uuid.uuid4().hex}.json"
        with open(empty_file, "w", encoding="utf-8") as f:
            f.write("")
        try:
            self.assertFalse(export_audit_logs(storage_file=empty_file))
        finally:
            if os.path.exists(empty_file):
                os.remove(empty_file)

    def test_export_audit_logs_empty_json_dict(self):
        empty_json_file = f"empty_json_{uuid.uuid4().hex}.json"
        with open(empty_json_file, "w", encoding="utf-8") as f:
            f.write("{}")
        try:
            self.assertFalse(export_audit_logs(storage_file=empty_json_file))
        finally:
            if os.path.exists(empty_json_file):
                os.remove(empty_json_file)

    def test_export_audit_logs_io_error(self):
        with patch("builtins.open", side_effect=IOError("Read failure")):
            self.assertFalse(export_audit_logs(storage_file=self.storage_file))

    def test_market_parser_stream_bytes_mock(self):
        trash_bytes = io.BytesIO(uuid.uuid4().bytes)
        with patch("builtins.open", return_value=trash_bytes):
            parser = MarketParser(storage_file=self.storage_file)
            result = parser.load_data(self.storage_file)
            self.assertIsNone(result)