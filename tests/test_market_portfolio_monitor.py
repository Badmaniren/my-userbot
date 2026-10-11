import unittest
from unittest.mock import patch, mock_open
import os
import io
import json
import random
import uuid
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
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.url = f"https://{''.join(random.choices(string.ascii_lowercase, k=8))}.com/{uuid.uuid4().hex}"
        self.telegram_token = f"{random.randint(100000, 999999)}:{uuid.uuid4().hex[:16]}"
        self.chat_id = str(random.randint(10000000, 99999999))
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.price = round(random.uniform(10.0, 1000.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_market_parser_read_content_bytes_utf8(self):
        parser = MarketParser(self.storage_file)
        random_bytes = uuid.uuid4().bytes
        mock_file = io.BytesIO(random_bytes)
        content = parser._read_content(mock_file)
        self.assertIsInstance(content, str)

    def test_market_parser_read_content_string(self):
        parser = MarketParser(self.storage_file)
        random_str = uuid.uuid4().hex
        mock_file = io.StringIO(random_str)
        content = parser._read_content(mock_file)
        self.assertEqual(content, random_str)

    def test_market_parser_fetch_and_store(self):
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, self.price)
        self.assertTrue(os.path.exists(self.storage_file))
        data = parser.load_data(self.storage_file)
        self.assertIn(self.symbol, data)
        self.assertEqual(data[self.symbol], self.price)

    def test_market_parser_load_data_corrupted_json(self):
        corrupted_content = f"{{{uuid.uuid4().hex}"
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(corrupted_content)
        parser = MarketParser(self.storage_file)
        data = parser.load_data(self.storage_file)
        self.assertEqual(data, {})

    def test_market_report_generator_generate_symbol_report(self):
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, self.price)
        gen = MarketReportGenerator(storage_file=self.storage_file)
        report = gen.generate_symbol_report(self.symbol)
        self.assertIn(self.symbol, report)
        self.assertIn(str(self.price), report)

    def test_market_report_generator_get_raw_stream_dump(self):
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, self.price)
        gen = MarketReportGenerator(storage_file=self.storage_file)
        dump = gen.get_raw_stream_dump()
        self.assertIn(self.symbol, dump)
        self.assertIn(str(self.price), dump)

    def test_generate_market_report(self):
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, self.price)
        report = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
        self.assertIn(self.symbol, report)

    def test_run_market_telegram_pipeline(self):
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, self.price)
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
        result = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(result)

    def test_start_new(self):
        result = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(result)

    def test_start_ened(self):
        result = start_ened(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(result)

    def test_export_audit_logs_valid(self):
        data = {self.symbol: self.price}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(data, f)
        res = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(res)

    def test_export_audit_logs_invalid(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(uuid.uuid4().hex)
        res = export_audit_logs(storage_file=self.storage_file)
        self.assertFalse(res)

    def test_export_audit_logs_nonexistent(self):
        non_existent_file = f"{uuid.uuid4().hex}.json"
        res = export_audit_logs(storage_file=non_existent_file)
        self.assertFalse(res)

if __name__ == "__main__":
    unittest.main()