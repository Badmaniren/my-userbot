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
        self.chat_id = str(random.randint(1000000, 99999999))
        self.storage_file = f"{uuid.uuid4().hex}.json"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_market_parser_read_content_bytes(self):
        random_bytes = uuid.uuid4().bytes
        stream = io.BytesIO(random_bytes)
        parser = MarketParser(self.storage_file)
        content = parser._read_content(stream)
        self.assertIsInstance(content, str)

    def test_market_parser_fetch_and_load_data(self):
        parser = MarketParser(self.storage_file)
        price_val = round(random.uniform(10.0, 1000.0), 2)
        parser.fetch_and_store(self.symbol, price_val)
        
        loaded_data = parser.load_data(self.storage_file)
        self.assertIn(self.symbol, loaded_data)
        self.assertEqual(loaded_data[self.symbol], price_val)

    def test_market_parser_load_data_empty_or_missing(self):
        parser = MarketParser(None)
        self.assertIsNone(parser.load_data(None))

        parser_missing = MarketParser(self.storage_file)
        self.assertEqual(parser_missing.load_data(self.storage_file), {})

    def test_market_report_generator_symbol_report(self):
        price_val = round(random.uniform(1.0, 500.0), 4)
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, price_val)

        gen = MarketReportGenerator(self.storage_file)
        report = gen.generate_symbol_report(self.symbol)
        self.assertIn(self.symbol, report)
        self.assertIn(str(price_val), report)

    def test_market_report_generator_no_data(self):
        gen = MarketReportGenerator(self.storage_file)
        report = gen.generate_symbol_report(self.symbol)
        self.assertIn("No data", report)

    def test_market_report_generator_raw_stream_dump(self):
        gen = MarketReportGenerator(None)
        self.assertEqual(gen.get_raw_stream_dump(), "{}")

        price_val = round(random.uniform(50.0, 150.0), 2)
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, price_val)

        gen_valid = MarketReportGenerator(self.storage_file)
        dump = gen_valid.get_raw_stream_dump()
        self.assertIn(self.symbol, dump)
        self.assertIn(str(price_val), dump)

    def test_generate_market_report(self):
        price_val = round(random.uniform(200.0, 300.0), 2)
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, price_val)

        res = generate_market_report(self.storage_file, self.symbol)
        self.assertIn(self.symbol, res)
        self.assertIn(str(price_val), res)

    def test_run_market_telegram_pipeline(self):
        price_val = round(random.uniform(5.0, 50.0), 2)
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, price_val)

        res = run_market_telegram_pipeline(
            storage_file=self.storage_file,
            symbol=self.symbol,
            chat_id=self.chat_id,
            url=self.url,
            telegram_token=self.telegram_token
        )
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["symbol"], self.symbol)
        self.assertEqual(res["price"], price_val)
        self.assertEqual(res["chat_id"], self.chat_id)
        self.assertEqual(res["url"], self.url)

    def test_export_audit_logs(self):
        self.assertFalse(export_audit_logs(None))
        self.assertFalse(export_audit_logs(self.storage_file))

        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, 123.45)
        self.assertTrue(export_audit_logs(self.storage_file))

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

    def test_market_parser_corrupted_json(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(uuid.uuid4().hex)

        parser = MarketParser(self.storage_file)
        data = parser.load_data(self.storage_file)
        self.assertEqual(data, {})

    def market_parser_partial_json(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("{'incomplete': ")

        parser = MarketParser(self.storage_file)
        data = parser.load_data(self.storage_file)
        self.assertEqual(data, {})

if __name__ == '__main__':
    unittest.main()