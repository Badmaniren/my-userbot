import unittest
from unittest.mock import patch
import os
import io
import json
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
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.url = f"https://{uuid.uuid4().hex}.com/{uuid.uuid4().hex}"
        self.telegram_token = f"{random.randint(100000, 999999)}:{uuid.uuid4().hex}"
        self.chat_id = f"@{uuid.uuid4().hex[:8]}"
        self.storage_file = f"test_store_{uuid.uuid4().hex}.json"
        self.price = round(random.uniform(10.0, 1000.0), 2)

    def tearDown(files_self):
        if os.path.exists(files_self.storage_file):
            try:
                os.remove(files_self.storage_file)
            except OSError:
                pass

    def test_market_parser_fetch_and_store_and_load(self):
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, self.price)
        
        data = parser.load_data(self.storage_file)
        self.assertIsInstance(data, dict)
        self.assertIn(self.symbol, data)
        self.assertEqual(data[self.symbol], self.price)

    def test_market_parser_load_data_nonexistent(self):
        non_existent = f"nonexistent_{uuid.uuid4().hex}.json"
        parser = MarketParser(non_existent)
        data = parser.load_data(non_existent)
        self.assertEqual(data, {})

    def test_market_parser_load_data_corrupted_json(self):
        corrupted_content = f"{{invalid_json_{uuid.uuid4().hex}"
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(corrupted_content)
        
        parser = MarketParser(self.storage_file)
        data = parser.load_data(self.storage_file)
        self.assertEqual(data, {})

    def test_market_parser_read_content_bytesio_latin1(self):
        parser = MarketParser(None)
        random_bytes = uuid.uuid4().bytes + b'\xff\xfe'
        stream = io.BytesIO(random_bytes)
        content = parser._read_content(stream)
        self.assertIsInstance(content, str)

    def test_market_report_generator_symbol_report(self):
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, self.price)

        report_gen = MarketReportGenerator(self.storage_file)
        report = report_gen.generate_symbol_report(self.symbol)
        self.assertIn(self.symbol, report)
        self.assertIn(str(self.price), report)

    def test_market_report_generator_no_data(self):
        report_gen = MarketReportGenerator(self.storage_file)
        missing_symbol = uuid.uuid4().hex[:6].upper()
        report = report_gen.generate_symbol_report(missing_symbol)
        self.assertIn("No data", report)

    def test_market_report_generator_get_raw_stream_dump(self):
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, self.price)

        report_gen = MarketReportGenerator(self.storage_file)
        dump = report_gen.get_raw_stream_dump()
        self.assertIsInstance(dump, str)
        self.assertIn(self.symbol, dump)
        self.assertIn(str(self.price), dump)

    def test_generate_market_report_function(self):
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, self.price)

        res = generate_market_report(self.storage_file, self.symbol)
        self.assertIn(self.symbol, res)

    def test_run_market_telegram_pipeline(self):
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, self.price)

        result = run_market_telegram_pipeline(
            storage_file=self.storage_file,
            symbol=self.symbol,
            chat_id=self.chat_id,
            url=self.url,
            telegram_token=self.telegram_token
        )
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["symbol"], self.symbol)
        self.assertEqual(result["price"], self.price)
        self.assertEqual(result["chat_id"], self.chat_id)
        self.assertEqual(result["url"], self.url)

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

    def test_export_audit_logs_valid_dict(self):
        data = {uuid.uuid4().hex: uuid.uuid4().hex}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(data, f)
        
        self.assertTrue(export_audit_logs(self.storage_file))

    def test_export_audit_logs_empty(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("   ")
        
        self.assertFalse(export_audit_logs(self.storage_file))

    def test_export_audit_logs_nonexistent(self):
        non_existent = f"missing_{uuid.uuid4().hex}.json"
        self.assertFalse(export_audit_logs(non_existent))