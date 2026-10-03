import unittest
import unittest.mock
from unittest.mock import patch
import io
import json
import os
import random
import uuid
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
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://{uuid.uuid4().hex}.com/api"
        self.telegram_token = uuid.uuid4().hex
        self.chat_id = str(random.randint(100000, 999999))

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_market_parser_fetch_and_store(self):
        parser = MarketParser(storage_file=self.storage_file)
        price = round(random.uniform(1.0, 1000.0), 4)
        parser.fetch_and_store(symbol=self.symbol, price=price)
        
        self.assertTrue(os.path.exists(self.storage_file))
        data = parser.load_data(self.storage_file)
        self.assertIsInstance(data, dict)
        self.assertIn(self.symbol, data)
        self.assertEqual(data[self.symbol], price)

    def test_market_parser_load_data_not_exists(self):
        non_existent = f"{uuid.uuid4().hex}.json"
        parser = MarketParser(storage_file=non_existent)
        result = parser.load_data(non_existent)
        self.assertIsNone(result)

    def test_market_parser_load_data_empty(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("   ")
        parser = MarketParser(storage_file=self.storage_file)
        result = parser.load_data(self.storage_file)
        self.assertEqual(result, {})

    def test_market_parser_load_data_unterminated(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write('{"unclosed": 123')
        parser = MarketParser(storage_file=self.storage_file)
        with self.assertRaises(json.JSONDecodeError):
            parser.load_data(self.storage_file)

    def test_market_parser_load_data_invalid_type(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write('[1, 2, 3]')
        parser = MarketParser(storage_file=self.storage_file)
        result = parser.load_data(self.storage_file)
        self.assertIsNone(result)

    def test_market_report_generator_symbol_report(self):
        price = round(random.uniform(10.0, 500.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=price)
        
        gen = MarketReportGenerator(storage_file=self.storage_file)
        report = gen.generate_symbol_report(symbol=self.symbol)
        self.assertIn(self.symbol, report)
        self.assertIn(str(price), report)

    def test_market_report_generator_symbol_report_no_data(self):
        gen = MarketReportGenerator(storage_file=self.storage_file)
        report = gen.generate_symbol_report(symbol=self.symbol)
        self.assertIn("No data", report)

    def test_market_report_generator_get_raw_stream_dump(self):
        gen = MarketReportGenerator(storage_file=self.storage_file)
        dump = gen.get_raw_stream_dump()
        self.assertEqual(dump, "{}")

        price = round(random.uniform(1.0, 100.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=price)
        dump_data = gen.get_raw_stream_dump()
        self.assertIn(self.symbol, dump_data)

    def test_generate_market_report_function(self):
        price = round(random.uniform(5.0, 50.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=price)
        
        rep = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
        self.assertIn(self.symbol, rep)

    def test_run_market_telegram_pipeline(self):
        price = round(random.uniform(100.0, 1000.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=price)

        res = run_market_telegram_pipeline(
            storage_file=self.storage_file,
            symbol=self.symbol,
            chat_id=self.chat_id,
            url=self.url,
            telegram_token=self.telegram_token
        )
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["symbol"], self.symbol)
        self.assertEqual(res["price"], price)
        self.assertEqual(res["chat_id"], self.chat_id)
        self.assertEqual(res["url"], self.url)

    def test_export_audit_logs_valid(self):
        price = round(random.uniform(1.0, 10.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=price)

        self.assertTrue(export_audit_logs(storage_file=self.storage_file))

    def test_export_audit_logs_invalid(self):
        self.assertFalse(export_audit_logs(storage_file=None))
        self.assertFalse(export_audit_logs(storage_file=f"{uuid.uuid4().hex}.json"))

        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("   ")
        self.assertFalse(export_audit_logs(storage_file=self.storage_file))

        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write('{"unclosed": true')
        self.assertFalse(export_audit_logs(storage_file=self.storage_file))

        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write('[1, 2, 3]')
        self.assertFalse(export_audit_logs(storage_file=self.storage_file))

    def test_run_pipeline_execution(self):
        res = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res)
        self.assertTrue(os.path.exists(self.storage_file))

    def test_start_new_execution(self):
        res = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res)

    def test_start_ened_execution(self):
        res = start_ened(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res)

    def test_stream_bytes_io_mocking_integration(self):
        random_bytes = uuid.uuid4().bytes + ''.join(random.choices(string.ascii_letters, k=20)).encode('utf-8')
        mock_stream = io.BytesIO(random_bytes)
        
        with patch('os.path.exists', return_value=True), patch('builtins.open', return_value=mock_stream):
            parser = MarketParser(storage_file=self.storage_file)
            with self.assertRaises((json.JSONDecodeError, TypeError, Exception)):
                parser.load_data(self.storage_file)