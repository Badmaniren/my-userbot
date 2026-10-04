import unittest
from unittest.mock import patch
import json
import os
import io
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
        self.rand_suffix = uuid.uuid4().hex[:8]
        self.storage_file = f"test_storage_{self.rand_suffix}.json"
        self.symbol = f"SYM_{random.choice(string.ascii_uppercase)}{random.randint(100, 999)}"
        self.url = f"https://{uuid.uuid4().hex[:6]}.com/api"
        self.telegram_token = f"{random.randint(1000,9999)}:AA{uuid.uuid4().hex[:8]}"
        self.chat_id = str(random.randint(100000, 999999))
        self.price = round(random.uniform(10.0, 1000.0), 2)

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
        loaded_data = parser.load_data(self.storage_file)
        self.assertIsInstance(loaded_data, dict)
        self.assertIn(self.symbol, loaded_data)
        self.assertEqual(loaded_data[self.symbol], self.price)

    def test_market_parser_fetch_and_store_existing_malformed(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(f'{{ "{uuid.uuid4().hex": ')

        parser = MarketParser(storage_file=self.storage_file)
        with self.assertRaises(json.JSONDecodeError):
            parser.fetch_and_store(symbol=self.symbol, price=self.price)

    def test_market_parser_load_data_nonexistent(self):
        non_existent = f"missing_{uuid.uuid4().hex}.json"
        parser = MarketParser(storage_file=non_existent)
        res = parser.load_data(non_existent)
        self.assertIsNone(res)

    def test_market_parser_load_data_empty(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("   \n ")
        parser = MarketParser(storage_file=self.storage_file)
        res = parser.load_data(self.storage_file)
        self.assertEqual(res, {})

    def test_market_report_generator_symbol_report(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)

        gen = MarketReportGenerator(storage_file=self.storage_file)
        report = gen.generate_symbol_report(symbol=self.symbol)
        self.assertIn(self.symbol, report)
        self.assertIn(str(self.price), report)

    def test_market_report_generator_symbol_report_missing(self):
        gen = MarketReportGenerator(storage_file=self.storage_file)
        other_symbol = f"MISS_{uuid.uuid4().hex[:4]}"
        report = gen.generate_symbol_report(symbol=other_symbol)
        self.assertIn(other_symbol, report)
        self.assertIn("No data", report)

    def test_market_report_generator_get_raw_stream_dump(self):
        payload = {uuid.uuid4().hex: random.randint(1, 100)}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(payload, f)

        gen = MarketReportGenerator(storage_file=self.storage_file)
        dump = gen.get_raw_stream_dump()
        self.assertIn(list(payload.keys())[0], dump)

    def test_market_report_generator_get_raw_stream_dump_io_fallback(self):
        bad_path = f"/invalid/path/dir_{uuid.uuid4().hex}/file.json"
        gen = MarketReportGenerator(storage_file=bad_path)
        with patch("builtins.open", side_effect=Exception("Mocked open failure")):
            dump = gen.get_raw_stream_dump()
            self.assertEqual(dump, "{}")

    def test_generate_market_report_wrapper(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)

        res = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
        self.assertIn(self.symbol, res)

    def test_run_market_telegram_pipeline(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)

        pipeline_res = run_market_telegram_pipeline(
            storage_file=self.storage_file,
            symbol=self.symbol,
            chat_id=self.chat_id,
            url=self.url,
            telegram_token=self.telegram_token
        )
        self.assertEqual(pipeline_res["status"], "success")
        self.assertEqual(pipeline_res["symbol"], self.symbol)
        self.assertEqual(pipeline_res["price"], self.price)
        self.assertEqual(pipeline_res["chat_id"], self.chat_id)
        self.assertEqual(pipeline_res["url"], self.url)

    def test_export_audit_logs_valid(self):
        data = {uuid.uuid4().hex: uuid.uuid4().hex}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(data, f)

        self.assertTrue(export_audit_logs(storage_file=self.storage_file))

    def test_export_audit_logs_invalid(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(f'{{ "{uuid.uuid4().hex": ')

        self.assertFalse(export_audit_logs(storage_file=self.storage_file))

    def test_export_audit_logs_empty(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("   ")

        self.assertFalse(export_audit_logs(storage_file=self.storage_file))

    def test_export_audit_logs_none(self):
        self.assertFalse(export_audit_logs(storage_file=None))

    def test_run_pipeline(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)

        res = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res)

    def test_start_new(self):
        res = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res)

    def test_start_ened(self):
        res = start_ened(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res)

if __name__ == "__main__":
    unittest.main()