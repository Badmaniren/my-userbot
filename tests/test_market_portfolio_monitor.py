import unittest
from unittest.mock import patch, mock_open
import json
import os
import io
import uuid
import random
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
        self.rand_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.rand_url = f"https://api.{uuid.uuid4().hex[:8]}.org/v1"
        self.rand_token = f"tok_{uuid.uuid4().hex}"
        self.rand_chat = str(random.randint(100000, 999999))
        self.rand_file = f"{uuid.uuid4().hex}.json"

    def test_market_parser_load_data_bytes_stream(self):
        rand_key = uuid.uuid4().hex[:5]
        rand_val = random.uniform(10.0, 500.0)
        payload = json.dumps({rand_key: rand_val}).encode("utf-8")
        
        parser = MarketParser(storage_file=self.rand_file)
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=payload.decode("utf-8"))):
            data = parser.load_data(self.rand_file)
            self.assertIsInstance(data, dict)
            self.assertIn(rand_key, data)
            self.assertEqual(data[rand_key], rand_val)

    def test_market_parser_load_data_invalid_stream(self):
        rand_garbage = uuid.uuid4().hex
        parser = MarketParser(storage_file=self.rand_file)
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=rand_garbage)):
            data = parser.load_data(self.rand_file)
            self.assertIsInstance(data, dict)
            self.assertEqual(data, {})

    def test_market_parser_load_data_empty_file(self):
        parser = MarketParser(storage_file=self.rand_file)
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data="   ")):
            data = parser.load_data(self.rand_file)
            self.assertIsInstance(data, dict)
            self.assertEqual(data, {})

    def test_market_parser_load_data_none_path(self):
        parser = MarketParser(storage_file=None)
        data = parser.load_data(None)
        self.assertIsNone(data)

    def test_market_parser_fetch_and_store(self):
        rand_price = random.uniform(1.0, 1000.0)
        parser = MarketParser(storage_file=self.rand_file)
        
        mock_file_handle = mock_open()
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_file_handle):
            parser.fetch_and_store(symbol=self.rand_symbol, price=rand_price)
            mock_file_handle.assert_called()

    def test_market_report_generator_symbol_report(self):
        rand_price = random.uniform(50.0, 500.0)
        mock_data = {self.rand_symbol: rand_price}
        
        gen = MarketReportGenerator(storage_file=self.rand_file)
        with patch.object(MarketParser, "load_data", return_value=mock_data):
            report = gen.generate_symbol_report(self.rand_symbol)
            self.assertIn(self.rand_symbol, report)
            self.assertIn(str(rand_price), report)

    def test_market_report_generator_symbol_report_no_data(self):
        gen = MarketReportGenerator(storage_file=self.rand_file)
        with patch.object(MarketParser, "load_data", return_value={}):
            report = gen.generate_symbol_report(self.rand_symbol)
            self.assertIn("No data", report)

    def test_market_report_generator_raw_stream_dump(self):
        rand_content = json.dumps({uuid.uuid4().hex: random.randint(1, 100)})
        gen = MarketReportGenerator(storage_file=self.rand_file)
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=rand_content)):
            dump = gen.get_raw_stream_dump()
            self.assertEqual(dump, rand_content)

    def test_market_report_generator_raw_stream_dump_missing(self):
        gen = MarketReportGenerator(storage_file=None)
        self.assertEqual(gen.get_raw_stream_dump(), "{}")
        
        with patch("os.path.exists", return_value=False):
            gen2 = MarketReportGenerator(storage_file=self.rand_file)
            self.assertEqual(gen2.get_raw_stream_dump(), "{}")

    def test_generate_market_report_wrapper(self):
        with patch("skills.market_portfolio_monitor.MarketReportGenerator.generate_symbol_report", return_value=uuid.uuid4().hex) as mock_gen:
            res = generate_market_report(self.rand_file, self.rand_symbol)
            self.assertIsInstance(res, str)
            mock_gen.assert_called_once_with(self.rand_symbol)

    def test_run_market_telegram_pipeline(self):
        rand_price = random.uniform(10.0, 100.0)
        mock_data = {self.rand_symbol: rand_price}
        
        with patch.object(MarketParser, "load_data", return_value=mock_data):
            res = run_market_telegram_pipeline(
                storage_file=self.rand_file,
                symbol=self.rand_symbol,
                chat_id=self.rand_chat,
                url=self.rand_url,
                telegram_token=self.rand_token
            )
            self.assertIsInstance(res, dict)
            self.assertEqual(res["status"], "success")
            self.assertEqual(res["symbol"], self.rand_symbol)
            self.assertEqual(res["price"], rand_price)
            self.assertEqual(res["chat_id"], self.rand_chat)
            self.assertEqual(res["url"], self.rand_url)

    def test_export_audit_logs_valid(self):
        rand_content = json.dumps({uuid.uuid4().hex: uuid.uuid4().hex})
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=rand_content)):
            self.assertTrue(export_audit_logs(self.rand_file))

    def test_export_audit_logs_empty(self):
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data="   ")):
            self.assertFalse(export_audit_logs(self.rand_file))

    def test_export_audit_logs_nonexistent(self):
        with patch("os.path.exists", return_value=False):
            self.assertFalse(export_audit_logs(self.rand_file))

    def test_run_pipeline_execution(self):
        rand_price = random.uniform(5.0, 50.0)
        mock_data = {self.rand_symbol: rand_price}
        
        with patch.object(MarketParser, "load_data", return_value=mock_data), \
             patch.object(MarketParser, "fetch_and_store") as mock_fetch, \
             patch.object(MarketReportGenerator, "generate_symbol_report"), \
             patch("skills.market_portfolio_monitor.generate_market_report"), \
             patch("skills.market_portfolio_monitor.run_market_telegram_pipeline"):
            
            result = run_pipeline(
                symbol=self.rand_symbol,
                url=self.rand_url,
                telegram_token=self.rand_token,
                chat_id=self.rand_chat,
                storage_file=self.rand_file
            )
            self.assertTrue(result)
            mock_fetch.assert_called_once()

    def test_start_new_and_ened_aliases(self):
        with patch("skills.market_portfolio_monitor.run_pipeline", return_value=True) as mock_run:
            res_new = start_new(self.rand_symbol, self.rand_url, self.rand_token, self.rand_chat, self.rand_file)
            res_ened = start_ened(self.rand_symbol, self.rand_url, self.rand_token, self.rand_chat, self.rand_file)
            
            self.assertTrue(res_new)
            self.assertTrue(res_ened)
            self.assertEqual(mock_run.call_count, 2)
            
            mock_run.assert_called_with(
                symbol=self.rand_symbol,
                url=self.rand_url,
                telegram_token=self.rand_token,
                chat_id=self.rand_chat,
                storage_file=self.rand_file
            )

    def test_io_bytes_stream_mocking_compliance(self):
        rand_bytes = json.dumps({self.rand_symbol: random.randint(100, 999)}).encode("utf-8")
        stream = io.BytesIO(rand_bytes)
        
        parser = MarketParser(storage_file=self.rand_file)
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=stream.read().decode("utf-8"))):
            data = parser.load_data(self.rand_file)
            self.assertIsInstance(data, dict)
            self.assertIn(self.rand_symbol, data)