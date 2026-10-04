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
    export_audit_logs,
)


class TestMarketPortfolioMonitor(unittest.TestCase):

    def setUp(self):
        self.symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        self.url = f"https://{uuid.uuid4().hex[:8]}.com/api"
        self.telegram_token = uuid.uuid4().hex
        self.chat_id = str(random.randint(100000, 999999))
        self.storage_file = f"test_store_{uuid.uuid4().hex[:8]}.json"
        self.price = round(random.uniform(1.0, 1000.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_market_parser_load_data_non_existent(self):
        parser = MarketParser(storage_file=self.storage_file)
        res = parser.load_data(self.storage_file)
        self.assertIsNone(res)

    def test_market_parser_load_data_empty(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("   \n")
        parser = MarketParser(storage_file=self.storage_file)
        res = parser.load_data(self.storage_file)
        self.assertEqual(res, {})

    def test_market_parser_load_data_unterminated(self):
        bad_json = f'{{ "{uuid.uuid4().hex[:4]}": '
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(bad_json)
        parser = MarketParser(storage_file=self.storage_file)
        res = parser.load_data(self.storage_file)
        self.assertEqual(res, {})

    def test_market_parser_load_data_valid(self):
        payload = {self.symbol: self.price}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(payload, f)
        parser = MarketParser(storage_file=self.storage_file)
        res = parser.load_data(self.storage_file)
        self.assertEqual(res, payload)

    def test_market_parser_load_data_not_dict(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump([1, 2, 3], f)
        parser = MarketParser(storage_file=self.storage_file)
        res = parser.load_data(self.storage_file)
        self.assertEqual(res, {})

    def test_market_parser_fetch_and_store(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)
        data = parser.load_data(self.storage_file)
        self.assertIsInstance(data, dict)
        self.assertEqual(data.get(self.symbol), self.price)

    def test_market_parser_fetch_and_store_corrupted_resilience(self):
        bad_json = f'{{ "{uuid.uuid4().hex[:4]}": '
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(bad_json)
        parser = MarketParser(storage_file=self.storage_file)
        new_price = round(random.uniform(10.0, 50.0), 2)
        parser.fetch_and_store(symbol=self.symbol, price=new_price)
        data = parser.load_data(self.storage_file)
        self.assertEqual(data.get(self.symbol), new_price)

    def test_market_report_generator_symbol_report(self):
        payload = {self.symbol: self.price}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(payload, f)
        gen = MarketReportGenerator(storage_file=self.storage_file)
        report = gen.generate_symbol_report(symbol=self.symbol)
        self.assertIn(self.symbol, report)
        self.assertIn(str(self.price), report)

    def test_market_report_generator_symbol_report_no_data(self):
        gen = MarketReportGenerator(storage_file=self.storage_file)
        report = gen.generate_symbol_report(symbol=self.symbol)
        self.assertIn("No data", report)

    def test_market_report_generator_get_raw_stream_dump(self):
        content_str = uuid.uuid4().hex
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(content_str)
        gen = MarketReportGenerator(storage_file=self.storage_file)
        dump = gen.get_raw_stream_dump()
        self.assertEqual(dump, content_str)

    def test_market_report_generator_get_raw_stream_dump_none(self):
        gen = MarketReportGenerator(storage_file=None)
        dump = gen.get_raw_stream_dump()
        self.assertEqual(dump, "{}")

    def test_generate_market_report_func(self):
        payload = {self.symbol: self.price}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(payload, f)
        res = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
        self.assertIn(self.symbol, res)

    def test_run_market_telegram_pipeline(self):
        payload = {self.symbol: self.price}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(payload, f)
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

    def test_export_audit_logs_none(self):
        self.assertFalse(export_audit_logs(storage_file=None))

    def test_export_audit_logs_empty(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("   ")
        self.assertFalse(export_audit_logs(storage_file=self.storage_file))

    def test_export_audit_logs_unterminated(self):
        bad_json = f'{{ "{uuid.uuid4().hex[:4]}": '
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(bad_json)
        self.assertTrue(export_audit_logs(storage_file=self.storage_file))

    def test_export_audit_logs_valid_dict(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump({uuid.uuid4().hex: uuid.uuid4().hex}, f)
        self.assertTrue(export_audit_logs(storage_file=self.storage_file))

    def test_export_audit_logs_valid_list(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump([1, 2, 3], f)
        self.assertFalse(export_audit_logs(storage_file=self.storage_file))

    def test_run_pipeline(self):
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