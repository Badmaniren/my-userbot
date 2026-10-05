import unittest
from unittest.mock import patch, mock_open
import json
import os
import io
import uuid
import random
import string

from skills.market_portfolio_monitor import (
    MarketParser,
    MarketReportGenerator,
    run_pipeline,
    start_new,
    start_ened,
    generate_market_report,
    run_market_telegram_pipeline,
    export_audit_logs
)


class TestMarketPortfolioMonitor(unittest.TestCase):

    def setUp(self):
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.price = round(random.uniform(10.0, 1000.0), 2)
        self.storage_file = f"store_{uuid.uuid4().hex}.json"
        self.chat_id = str(random.randint(100000, 999999))
        self.url = f"https://api.{uuid.uuid4().hex[:8]}.com/v1/hook"
        self.telegram_token = f"{random.randint(1000,9999)}:BOT_{uuid.uuid4().hex[:8]}"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_market_parser_fetch_and_store_new_file(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)
        
        self.assertTrue(os.path.exists(self.storage_file))
        data = parser.load_data(storage_file=self.storage_file)
        self.assertIsInstance(data, dict)
        self.assertIn(self.symbol, data)
        self.assertEqual(data[self.symbol], self.price)

    def test_market_parser_load_data_invalid_json(self):
        corrupted_content = f"{{invalid_syntax_{uuid.uuid4().hex}"
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(corrupted_content)

        parser = MarketParser(storage_file=self.storage_file)
        data = parser.load_data(storage_file=self.storage_file)
        self.assertEqual(data, {})

    def test_market_parser_load_data_none_storage(self):
        parser = MarketParser(storage_file=None)
        data = parser.load_data(storage_file=None)
        self.assertIsNone(data)

    def test_market_report_generator_symbol_report(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)

        report_gen = MarketReportGenerator(storage_file=self.storage_file)
        report = report_gen.generate_symbol_report(symbol=self.symbol)
        
        self.assertIn(self.symbol, report)
        self.assertIn(str(self.price), report)

    def test_market_report_generator_no_data(self):
        report_gen = MarketReportGenerator(storage_file=self.storage_file)
        report = report_gen.generate_symbol_report(symbol=self.symbol)
        self.assertIn("No data", report)

    def test_get_raw_stream_dump(self):
        payload = {self.symbol: self.price}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(payload, f)

        report_gen = MarketReportGenerator(storage_file=self.storage_file)
        dump = report_gen.get_raw_stream_dump()
        self.assertIn(self.symbol, dump)
        self.assertIn(str(self.price), dump)

    def test_get_raw_stream_dump_none_path(self):
        report_gen = MarketReportGenerator(storage_file=None)
        dump = report_gen.get_raw_stream_dump()
        self.assertEqual(dump, "{}")

    def test_generate_market_report_wrapper(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)

        report = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
        self.assertIn(self.symbol, report)
        self.assertIn(str(self.price), report)

    def test_run_market_telegram_pipeline(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)

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

    def test_run_pipeline(self):
        res = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res)

    def test_start_new_and_ened(self):
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

    def test_export_audit_logs_valid(self):
        payload = {uuid.uuid4().hex: uuid.uuid4().hex}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(payload, f)

        res = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(res)

    def test_export_audit_logs_empty(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("")

        res = export_audit_logs(storage_file=self.storage_file)
        self.assertFalse(res)

    def test_stream_read_with_mock_bytes_io(self):
        raw_bytes = json.dumps({self.symbol: self.price}).encode("utf-8")
        mock_stream = io.BytesIO(raw_bytes)

        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=raw_bytes)):
            
            parser = MarketParser(storage_file=self.storage_file)
            data = parser.load_data(storage_file=self.storage_file)
            self.assertIsInstance(data, dict)
            self.assertEqual(data.get(self.symbol), self.price)