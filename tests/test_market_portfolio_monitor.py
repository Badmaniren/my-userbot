import unittest
from unittest.mock import patch
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
    export_audit_logs,
)


class TestMarketPortfolioMonitor(unittest.TestCase):

    def setUp(self):
        self.symbol = "".join(random.choices(string.ascii_uppercase, k=5))
        self.url = f"https://{uuid.uuid4().hex}.com/api"
        self.telegram_token = f"{random.randint(100000, 999999)}:{uuid.uuid4().hex}"
        self.chat_id = str(random.randint(10000, 99999))
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.price = round(random.uniform(10.0, 1000.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_market_parser_read_content_bytes_and_streams(self):
        parser = MarketParser(storage_file=None)
        
        random_bytes = uuid.uuid4().bytes
        stream = io.BytesIO(random_bytes)
        content = parser._read_content(stream)
        self.assertIsInstance(content, str)

        corrupted_bytes = b"\xff\xfe\xfd"
        stream_corrupted = io.BytesIO(corrupted_bytes)
        content_corr = parser._read_content(stream_corrupted)
        self.assertIsInstance(content_corr, str)

    def test_market_parser_fetch_and_store_and_load_data(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)

        self.assertTrue(os.path.exists(self.storage_file))
        loaded_data = parser.load_data(storage_file=self.storage_file)
        self.assertIsInstance(loaded_data, dict)
        self.assertIn(self.symbol, loaded_data)
        self.assertEqual(loaded_data[self.symbol], self.price)

    def test_market_parser_load_data_edge_cases(self):
        parser = MarketParser(storage_file=self.storage_file)
        
        res_none = parser.load_data(storage_file=None)
        self.assertIsNone(res_none)

        non_existent_file = f"{uuid.uuid4().hex}.json"
        res_non_exist = parser.load_data(storage_file=non_existent_file)
        self.assertEqual(res_non_exist, {})

        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("   ")
        self.assertEqual(parser.load_data(self.storage_file), {})

        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("{invalid_json")
        self.assertEqual(parser.load_data(self.storage_file), {})

        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(json.dumps([random.randint(1, 100), random.randint(101, 200)]))
        self.assertEqual(parser.load_data(self.storage_file), {})

    def test_market_report_generator_symbol_report(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)

        report_gen = MarketReportGenerator(storage_file=self.storage_file)
        report = report_gen.generate_symbol_report(symbol=self.symbol)
        self.assertIn(self.symbol, report)
        self.assertIn(str(self.price), report)

        absent_symbol = "".join(random.choices(string.ascii_uppercase, k=6))
        absent_report = report_gen.generate_symbol_report(symbol=absent_symbol)
        self.assertIn(absent_symbol, absent_report)
        self.assertIn("No data", absent_report)

    def test_market_report_generator_raw_stream_dump(self):
        report_gen_none = MarketReportGenerator(storage_file=None)
        self.assertEqual(report_gen_none.get_raw_stream_dump(), "{}")

        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)

        report_gen = MarketReportGenerator(storage_file=self.storage_file)
        dump_content = report_gen.get_raw_stream_dump()
        self.assertIn(self.symbol, dump_content)
        self.assertIn(str(self.price), dump_content)

        non_existent_gen = MarketReportGenerator(storage_file=f"{uuid.uuid4().hex}.json")
        self.assertEqual(non_existent_gen.get_raw_stream_dump(), "{}")

    def test_generate_market_report_wrapper(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)

        rep = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
        self.assertIn(self.symbol, rep)

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
        self.assertIsInstance(res, dict)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["symbol"], self.symbol)
        self.assertEqual(res["price"], self.price)
        self.assertEqual(res["chat_id"], self.chat_id)
        self.assertEqual(res["url"], self.url)

    def test_run_pipeline_and_aliases(self):
        result = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(result)

        result_new = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(result_new)

        result_ened = start_ened(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(result_ened)

    def test_export_audit_logs(self):
        self.assertFalse(export_audit_logs(storage_file=None))
        self.assertFalse(export_audit_logs(storage_file=f"{uuid.uuid4().hex}.json"))

        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("   ")
        self.assertFalse(export_audit_logs(storage_file=self.storage_file))

        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("{partial_json")
        self.assertTrue(export_audit_logs(storage_file=self.storage_file))

        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)
        self.assertTrue(export_audit_logs(storage_file=self.storage_file))

        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("invalid_format_string_not_json")
        self.assertTrue(export_audit_logs(storage_file=self.storage_file))


if __name__ == "__main__":
    unittest.main()