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
        self.rand_suffix = uuid.uuid4().hex
        self.storage_file = f"test_storage_{self.rand_suffix}.json"
        self.symbol = f"SYM_{random.randint(1000, 9999)}_{uuid.uuid4().hex[:4]}"
        self.url = f"https://api.{uuid.uuid4().hex[:8]}.test/v1"
        self.telegram_token = f"token_{uuid.uuid4().hex}"
        self.chat_id = str(random.randint(100000, 999999))
        self.price = round(random.uniform(1.0, 10000.0), 4)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_market_parser_fetch_and_load(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)
        
        self.assertTrue(os.path.exists(self.storage_file))

        loaded_data = parser.load_data(self.storage_file)
        self.assertIsInstance(loaded_data, dict)
        self.assertIn(self.symbol, loaded_data)
        self.assertEqual(loaded_data[self.symbol], self.price)

    def test_market_parser_load_nonexistent(self):
        parser = MarketParser(storage_file=self.storage_file)
        non_existent_path = f"missing_{uuid.uuid4().hex}.json"
        res = parser.load_data(non_existent_path)
        self.assertIsNone(res)

    def test_market_parser_invalid_json_handling(self):
        garbage_content = f"invalid_json_data_{uuid.uuid4().hex}"
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(garbage_content)

        parser = MarketParser(storage_file=self.storage_file)
        loaded = parser.load_data(self.storage_file)
        self.assertIsNone(loaded)

    def test_market_report_generator_symbol_report(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)

        reporter = MarketReportGenerator(storage_file=self.storage_file)
        report = reporter.generate_symbol_report(symbol=self.symbol)

        self.assertIn(self.symbol, report)
        self.assertIn(str(self.price), report)

    def test_market_report_generator_no_data(self):
        reporter = MarketReportGenerator(storage_file=self.storage_file)
        report = reporter.generate_symbol_report(symbol=self.symbol)

        self.assertIn(self.symbol, report)
        self.assertIn("No data", report)

    def test_market_report_generator_get_raw_stream_dump(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)

        reporter = MarketReportGenerator(storage_file=self.storage_file)
        raw_dump = reporter.get_raw_stream_dump()

        self.assertIsInstance(raw_dump, str)
        parsed_dump = json.loads(raw_dump)
        self.assertEqual(parsed_dump.get(self.symbol), self.price)

    def test_generate_market_report_helper(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)

        report = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
        self.assertIn(self.symbol, report)
        self.assertIn(str(self.price), report)

    def test_run_market_telegram_pipeline(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)

        result = run_market_telegram_pipeline(
            storage_file=self.storage_file,
            symbol=self.symbol,
            chat_id=self.chat_id,
            url=self.url,
            telegram_token=self.telegram_token
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("symbol"), self.symbol)
        self.assertEqual(result.get("price"), self.price)
        self.assertEqual(result.get("chat_id"), self.chat_id)
        self.assertEqual(result.get("url"), self.url)

    def test_export_audit_logs_valid(self):
        data = {uuid.uuid4().hex: random.randint(1, 100)}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(data, f)

        export_res = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(export_res)

    def test_export_audit_logs_invalid(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(f"corrupted_log_{uuid.uuid4().hex}")

        export_res = export_audit_logs(storage_file=self.storage_file)
        self.assertFalse(export_res)

    def test_export_audit_logs_nonexistent(self):
        missing_file = f"missing_{uuid.uuid4().hex}.json"
        export_res = export_audit_logs(storage_file=missing_file)
        self.assertFalse(export_res)

    def test_run_pipeline_flow(self):
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

    def test_start_new_and_ened_aliasing(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)

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

    def test_stream_bytes_io_mocking_load(self):
        random_bytes = json.dumps({self.symbol: self.price}).encode("utf-8")
        stream_mock = io.BytesIO(random_bytes)

        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", return_value=io.StringIO(stream_mock.getvalue().decode("utf-8"))):

            parser = MarketParser(storage_file=self.storage_file)
            data = parser.load_data(self.storage_file)
            self.assertIsInstance(data, dict)
            self.assertEqual(data.get(self.symbol), self.price)


if __name__ == "__main__":
    unittest.main()