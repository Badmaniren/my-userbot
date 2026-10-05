import unittest
from unittest.mock import patch, MagicMock
import io
import json
import os
import random
import uuid
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
        self.url = f"https://{uuid.uuid4().hex[:8]}.org/api"
        self.telegram_token = f"{random.randint(1000, 9999)}:BOT_{uuid.uuid4().hex[:6]}"
        self.chat_id = f"@{uuid.uuid4().hex[:6]}"
        self.storage_file = f"store_{uuid.uuid4().hex[:8]}.json"
        self.price = round(random.uniform(10.0, 1000.0), 4)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except Exception:
                pass

    def test_market_parser_stream_reading_bytes_io_fix(self):
        stream_data = json.dumps({self.symbol: self.price}).encode("utf-8")
        stream_mock = io.BytesIO(stream_data)
        
        parser = MarketParser(storage_file=stream_mock)
        data = parser.load_data(stream_mock)

        self.assertIsInstance(data, dict)
        self.assertEqual(data.get(self.symbol), self.price)

    def test_market_parser_fetch_and_store_stream(self):
        stream_mock = io.BytesIO(b"")
        parser = MarketParser(storage_file=stream_mock)

        new_symbol = f"NEW_{uuid.uuid4().hex[:4]}"
        new_price = round(random.uniform(1.0, 500.0), 2)

        parser.fetch_and_store(symbol=new_symbol, price=new_price)

        stream_mock.seek(0)
        content = stream_mock.read().decode("utf-8")
        parsed = json.loads(content)

        self.assertEqual(parsed.get(new_symbol), new_price)

    def test_market_parser_load_data_invalid_json(self):
        invalid_content = f"{{invalid_json_{uuid.uuid4().hex}}}"
        stream_mock = io.BytesIO(invalid_content.encode("utf-8"))

        parser = MarketParser(storage_file=stream_mock)
        data = parser.load_data(stream_mock)
        
        self.assertEqual(data, {})

    def test_market_report_generator_symbol_report(self):
        initial_data = {self.symbol: self.price}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        gen = MarketReportGenerator(storage_file=self.storage_file)
        report = gen.generate_symbol_report(symbol=self.symbol)
        
        self.assertIn(self.symbol, report)
        self.assertIn(str(self.price), report)

    def test_market_report_generator_no_data(self):
        missing_symbol = f"MISS_{uuid.uuid4().hex[:4]}"
        gen = MarketReportGenerator(storage_file=self.storage_file)
        report = gen.generate_symbol_report(symbol=missing_symbol)
        
        self.assertIn(missing_symbol, report)
        self.assertIn("No data", report)

    def test_market_report_generator_raw_stream_dump(self):
        initial_data = {self.symbol: self.price}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        gen = MarketReportGenerator(storage_file=self.storage_file)
        dump = gen.get_raw_stream_dump()
        
        self.assertIn(self.symbol, dump)
        self.assertIn(str(self.price), dump)

    def test_generate_market_report_wrapper(self):
        initial_data = {self.symbol: self.price}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        report = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
        self.assertIn(self.symbol, report)

    def test_run_market_telegram_pipeline(self):
        initial_data = {self.symbol: self.price}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        res = run_market_telegram_pipeline(
            storage_file=self.storage_file,
            symbol=self.symbol,
            chat_id=self.chat_id,
            url=self.url,
            telegram_token=self.telegram_token
        )

        self.assertEqual(res["status"], "success")
        self.assertEqual(res["symbol"], self.symbol)
        self.assertEqual(res["price"], self.price)
        self.assertEqual(res["chat_id"], self.chat_id)
        self.assertEqual(res["url"], self.url)

    def test_run_pipeline_execution(self):
        initial_data = {self.symbol: self.price}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        result = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(result)

    def test_start_new_alias(self):
        result = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(result)

    def test_start_ened_alias(self):
        result = start_ened(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(result)

    def test_export_audit_logs_valid_file(self):
        initial_data = {self.symbol: self.price}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        exported = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(exported)

    def test_export_audit_logs_empty(self):
        exported = export_audit_logs(storage_file=None)
        self.assertFalse(exported)

    def test_market_parser_latin1_fallback(self):
        latin_bytes = "Test $ symbol".encode("latin-1")
        stream_mock = io.BytesIO(latin_bytes)
        parser = MarketParser(storage_file=stream_mock)
        content = parser._read_content(stream_mock)
        self.assertIn("Test", content)