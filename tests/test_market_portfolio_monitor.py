import unittest
import json
import os
import tempfile
import uuid
import random
from unittest.mock import patch, MagicMock
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
        self.rand_suffix = uuid.uuid4().hex[:8]
        self.symbol = f"SYM_{self.rand_suffix}"
        self.url = f"https://api.{self.rand_suffix}.market/v1"
        self.telegram_token = f"token_{self.rand_suffix}"
        self.chat_id = str(random.randint(100000, 999999))
        
        self.fd, self.storage_file = tempfile.mkstemp(suffix=".json")
        os.close(self.fd)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_market_parser_fetch_and_store_and_load(self):
        parser = MarketParser(self.storage_file)
        price = round(random.uniform(10.0, 1000.0), 4)
        
        parser.fetch_and_store(self.symbol, price)
        
        data = parser.load_data(self.storage_file)
        self.assertIsInstance(data, dict)
        self.assertIn(self.symbol, data)
        self.assertEqual(data[self.symbol], price)

    def test_market_parser_load_data_empty_file(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("   ")
        
        parser = MarketParser(self.storage_file)
        data = parser.load_data(self.storage_file)
        self.assertEqual(data, {})

    def test_market_parser_load_data_nonexistent(self):
        non_existent = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4().hex}.json")
        parser = MarketParser(non_existent)
        data = parser.load_data(non_existent)
        self.assertIsNone(data)

    def test_market_parser_load_data_invalid_json(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(f"{{invalid_content_{uuid.uuid4().hex}")
        
        parser = MarketParser(self.storage_file)
        with self.assertRaises(json.JSONDecodeError):
            parser.load_data(self.storage_file)

    def test_market_report_generator_symbol_report(self):
        price = round(random.uniform(1.0, 500.0), 2)
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, price)

        gen = MarketReportGenerator(self.storage_file)
        report = gen.generate_symbol_report(self.symbol)
        self.assertIn(self.symbol, report)
        self.assertIn(str(price), report)

    def test_market_report_generator_symbol_report_no_data(self):
        gen = MarketReportGenerator(self.storage_file)
        report = gen.generate_symbol_report(self.symbol)
        self.assertIn(self.symbol, report)
        self.assertIn("No data", report)

    def test_market_report_generator_get_raw_stream_dump(self):
        price = round(random.uniform(50.0, 150.0), 2)
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, price)

        gen = MarketReportGenerator(self.storage_file)
        dump = gen.get_raw_stream_dump()
        self.assertIn(self.symbol, dump)
        self.assertIn(str(price), dump)

    def test_generate_market_report_function(self):
        price = round(random.uniform(200.0, 300.0), 2)
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, price)

        res = generate_market_report(self.storage_file, self.symbol)
        self.assertIn(self.symbol, res)
        self.assertIn(str(price), res)

    def test_run_market_telegram_pipeline(self):
        price = round(random.uniform(1.0, 10.0), 4)
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, price)

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

    def test_export_audit_logs_valid(self):
        price = round(random.uniform(100.0, 200.0), 2)
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, price)

        valid_export = export_audit_logs(self.storage_file)
        self.assertTrue(valid_export)

    def test_export_audit_logs_invalid(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(f"{{broken_json_{uuid.uuid4().hex}")

        invalid_export = export_audit_logs(self.storage_file)
        self.assertFalse(invalid_export)

    def test_export_audit_logs_empty(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("   ")

        empty_export = export_audit_logs(self.storage_file)
        self.assertFalse(empty_export)

    def test_export_audit_logs_none(self):
        self.assertFalse(export_audit_logs(None))

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