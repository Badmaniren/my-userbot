import unittest
from unittest.mock import patch, mock_open
import json
import os
import io
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
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://{uuid.uuid4().hex[:8]}.com/api"
        self.telegram_token = f"{random.randint(100000, 999999)}:{uuid.uuid4().hex[:16]}"
        self.chat_id = f"@{uuid.uuid4().hex[:8]}"
        self.storage_file = f"storage_{uuid.uuid4().hex[:8]}.json"

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

    def test_market_parser_fetch_and_store_and_load(self):
        price = round(random.uniform(10.0, 1000.0), 4)
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, price)
        
        loaded = parser.load_data(self.storage_file)
        self.assertIsInstance(loaded, dict)
        self.assertIn(self.symbol, loaded)
        self.assertEqual(loaded[self.symbol], price)

    def test_market_parser_load_data_invalid_json(self):
        garbage_content = uuid.uuid4().hex
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(garbage_content)
        
        parser = MarketParser(self.storage_file)
        loaded = parser.load_data(self.storage_file)
        self.assertEqual(loaded, {})

    def test_market_parser_load_data_none_storage(self):
        parser = MarketParser(None)
        self.assertIsNone(parser.load_data(None))

    def test_market_report_generator_symbol_report(self):
        price = round(random.uniform(1.0, 500.0), 2)
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, price)

        gen = MarketReportGenerator(self.storage_file)
        report = gen.generate_symbol_report(self.symbol)
        self.assertIn(self.symbol, report)
        self.assertIn(str(price), report)

    def test_market_report_generator_no_data(self):
        gen = MarketReportGenerator(self.storage_file)
        report = gen.generate_symbol_report(self.symbol)
        self.assertIn(self.symbol, report)
        self.assertIn("No data", report)

    def test_market_report_generator_get_raw_stream_dump(self):
        random_text = f"dump_{uuid.uuid4().hex}"
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(random_text)

        gen = MarketReportGenerator(self.storage_file)
        dump = gen.get_raw_stream_dump()
        self.assertEqual(dump, random_text)

    def test_generate_market_report_function(self):
        price = round(random.uniform(5.0, 50.0), 2)
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, price)

        report = generate_market_report(self.storage_file, self.symbol)
        self.assertIn(self.symbol, report)
        self.assertIn(str(price), report)

    def test_run_market_telegram_pipeline(self):
        price = round(random.uniform(100.0, 999.0), 2)
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
        payload = {self.symbol: random.randint(1, 100)}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(payload, f)

        res = export_audit_logs(self.storage_file)
        self.assertTrue(res)

    def test_export_audit_logs_empty(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("   ")

        res = export_audit_logs(self.storage_file)
        self.assertFalse(res)

    def test_run_pipeline_execution(self):
        result = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(result)

    def test_start_new_execution(self):
        result = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(result)

    def test_start_ened_execution(self):
        result = start_ened(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()