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
    export_audit_logs
)

class TestMarketPortfolioMonitor(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"
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

    def test_market_parser_load_and_store_random_data(self):
        price = round(random.uniform(10.0, 1000.0), 2)
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, price)

        loaded_data = parser.load_data(self.storage_file)
        self.assertIsInstance(loaded_data, dict)
        self.assertIn(self.symbol, loaded_data)
        self.assertEqual(loaded_data[self.symbol], price)

    def test_market_parser_load_none_storage(self):
        parser = MarketParser(None)
        res = parser.load_data(None)
        self.assertIsNone(res)

    def test_market_parser_corrupted_json(self):
        corrupt_data = f"{{invalid_json_{uuid.uuid4().hex}"
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(corrupt_data)

        parser = MarketParser(self.storage_file)
        data = parser.load_data(self.storage_file)
        self.assertEqual(data, {})

    def test_market_parser_binary_content_mock(self):
        random_bytes = io.BytesIO(json.dumps({self.symbol: random.randint(1, 500)}).encode("utf-8"))
        
        with patch("builtins.open", return_value=random_bytes):
            parser = MarketParser(self.storage_file)
            data = parser.load_data(self.storage_file)
            self.assertIsInstance(data, dict)

    def test_market_report_generator_symbol_report(self):
        price = round(random.uniform(1.0, 50.0), 2)
        initial_data = {self.symbol: price}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        gen = MarketReportGenerator(self.storage_file)
        report = gen.generate_symbol_report(self.symbol)
        self.assertIn(self.symbol, report)
        self.assertIn(str(price), report)

    def test_market_report_generator_no_data(self):
        gen = MarketReportGenerator(self.storage_file)
        report = gen.generate_symbol_report(self.symbol)
        self.assertIn("No data", report)

    def test_market_report_generator_get_raw_stream_dump(self):
        dump_content = f"{uuid.uuid4().hex}:{random.randint(100, 999)}"
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(dump_content)

        gen = MarketReportGenerator(self.storage_file)
        raw = gen.get_raw_stream_dump()
        self.assertEqual(raw, dump_content)

    def test_market_report_generator_get_raw_stream_dump_none(self):
        gen = MarketReportGenerator(None)
        self.assertEqual(gen.get_raw_stream_dump(), "{}")

    def test_generate_market_report_function(self):
        price = round(random.uniform(100.0, 200.0), 2)
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump({self.symbol: price}, f)

        res = generate_market_report(self.storage_file, self.symbol)
        self.assertIn(self.symbol, res)
        self.assertIn(str(price), res)

    def test_run_market_telegram_pipeline(self):
        price = round(random.uniform(500.0, 1000.0), 2)
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump({self.symbol: price}, f)

        result = run_market_telegram_pipeline(
            storage_file=self.storage_file,
            symbol=self.symbol,
            chat_id=self.chat_id,
            url=self.url,
            telegram_token=self.telegram_token
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["symbol"], self.symbol)
        self.assertEqual(result["price"], price)
        self.assertEqual(result["chat_id"], self.chat_id)
        self.assertEqual(result["url"], self.url)

    def test_run_pipeline_execution(self):
        success = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(success)

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

    def test_export_audit_logs_valid_dict(self):
        audit_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(audit_data, f)

        self.assertTrue(export_audit_logs(self.storage_file))

    def test_export_audit_logs_empty(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("   ")

        self.assertFalse(export_audit_logs(self.storage_file))

    def test_export_audit_logs_nonexistent(self):
        non_existent = f"missing_{uuid.uuid4().hex}.json"
        self.assertFalse(export_audit_logs(non_existent))

if __name__ == "__main__":
    unittest.main()