import unittest
from unittest.mock import patch, mock_open
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
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://{uuid.uuid4().hex[:8]}.com/api"
        self.telegram_token = f"{random.randint(100000, 999999)}:{uuid.uuid4().hex[:16]}"
        self.chat_id = f"@{uuid.uuid4().hex[:8]}"
        self.storage_file = f"storage_{uuid.uuid4().hex}.json"
        self.price = round(random.uniform(10.0, 1000.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_market_parser_fetch_and_store(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)

        self.assertTrue(os.path.exists(self.storage_file))
        with open(self.storage_file, "r", encoding="utf-8") as f:
            content = f.read()
            data = json.loads(content)
            self.assertIn(self.symbol, data)
            self.assertEqual(data[self.symbol], self.price)

    def test_market_parser_load_data_nonexistent(self):
        non_existent = f"missing_{uuid.uuid4().hex}.json"
        parser = MarketParser(storage_file=non_existent)
        result = parser.load_data(non_existent)
        self.assertIsNone(result)

    def test_market_parser_load_data_empty_file(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("   \n  ")
        parser = MarketParser(storage_file=self.storage_file)
        result = parser.load_data(self.storage_file)
        self.assertEqual(result, {})

    def test_market_parser_load_data_corrupted_json(self):
        corrupted_data = f"{{invalid_json_{uuid.uuid4().hex}"
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(corrupted_data)
        parser = MarketParser(storage_file=self.storage_file)
        result = parser.load_data(self.storage_file)
        self.assertIsNone(result)

    def test_market_report_generator_with_data(self):
        initial_data = {self.symbol: self.price}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        gen = MarketReportGenerator(storage_file=self.storage_file)
        report = gen.generate_symbol_report(symbol=self.symbol)
        
        expected_substring = f"Report for {self.symbol}: {self.price}"
        self.assertIn(expected_substring, report)

    def test_market_report_generator_no_data(self):
        gen = MarketReportGenerator(storage_file=self.storage_file)
        missing_symbol = f"MISS_{uuid.uuid4().hex[:4]}"
        report = gen.generate_symbol_report(symbol=missing_symbol)
        
        expected_substring = f"Report for {missing_symbol}: No data"
        self.assertIn(expected_substring, report)

    def test_get_raw_stream_dump(self):
        stream_content = f'{{"random_dump_key_{uuid.uuid4().hex}": {random.randint(1, 100)}}}'
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(stream_content)

        gen = MarketReportGenerator(storage_file=self.storage_file)
        dump = gen.get_raw_stream_dump()
        self.assertEqual(dump, stream_content)

    def test_get_raw_stream_dump_io_error(self):
        gen = MarketReportGenerator(storage_file=self.storage_file)
        with patch("builtins.open", side_effect=IOError("Simulated IO Error")):
            dump = gen.get_raw_stream_dump()
            self.assertEqual(dump, "{}")

    def test_generate_market_report_wrapper(self):
        initial_data = {self.symbol: self.price}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        report = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
        self.assertIn(str(self.price), report)
        self.assertIn(self.symbol, report)

    def test_run_market_telegram_pipeline(self):
        initial_data = {self.symbol: self.price}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

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
        self.assertEqual(res.get("price"), self.price)
        self.assertEqual(res.get("chat_id"), self.chat_id)
        self.assertEqual(res.get("url"), self.url)

    def test_export_audit_logs_success(self):
        log_content = f"audit_entry_{uuid.uuid4().hex}"
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(log_content)

        result = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(result)

    def test_export_audit_logs_empty_file(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("   \n")

        result = export_audit_logs(storage_file=self.storage_file)
        self.assertFalse(result)

    def test_export_audit_logs_nonexistent(self):
        non_existent = f"missing_audit_{uuid.uuid4().hex}.log"
        result = export_audit_logs(storage_file=non_existent)
        self.assertFalse(result)

    def test_export_audit_logs_io_exception(self):
        with patch("builtins.open", side_effect=OSError("Disk failure")):
            result = export_audit_logs(storage_file=self.storage_file)
            self.assertFalse(result)

    def test_run_pipeline_execution(self):
        initial_data = {self.symbol: self.price}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        success = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(success)

    def test_start_new_execution(self):
        success = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(success)

    def test_start_ened_alias(self):
        success = start_ened(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(success)

    def test_market_parser_io_exceptions_handling(self):
        parser = MarketParser(storage_file=self.storage_file)
        with patch("builtins.open", side_effect=IOError("Write error")):
            try:
                parser.fetch_and_store(symbol=self.symbol, price=self.price)
            except Exception as e:
                self.fail(f"fetch_and_store raised unexpected exception on IOError: {e}")

        with patch("builtins.open", side_effect=OSError("Read error")):
            res = parser.load_data(storage_file=self.storage_file)
            self.assertIsNone(res)


if __name__ == "__main__":
    unittest.main()