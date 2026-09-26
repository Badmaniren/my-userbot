import unittest
from unittest.mock import patch
import os
import json
import uuid
import random
import io

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
        self.random_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.random_url = f"https://{uuid.uuid4().hex[:8]}.com/api"
        self.random_token = uuid.uuid4().hex
        self.random_chat_id = str(random.randint(100000, 999999))
        self.storage_file = f"storage_{uuid.uuid4().hex[:8]}.json"

    def tearDown(self):
        for fpath in [self.storage_file, self.symbol, f"{self.symbol}.db", f"{self.symbol}.json"]:
            if os.path.exists(fpath):
                try:
                    os.remove(fpath)
                except OSError:
                    pass

    def test_market_parser_fetch_and_load(self):
        parser = MarketParser(storage_file=self.storage_file)
        test_price = round(random.uniform(10.0, 1000.0), 2)
        
        parser.fetch_and_store(symbol=self.random_symbol, price=test_price)
        
        loaded_data = parser.load_data(self.storage_file)
        self.assertIsInstance(loaded_data, dict)
        self.assertIn(self.random_symbol, loaded_data)
        self.assertEqual(loaded_data[self.random_symbol], test_price)

    def test_market_parser_load_nonexistent(self):
        nonexistent_file = f"missing_{uuid.uuid4().hex}.json"
        parser = MarketParser(storage_file=nonexistent_file)
        data = parser.load_data(nonexistent_file)
        self.assertIsNone(data)

    def test_market_parser_corrupted_json(self):
        corrupt_data = uuid.uuid4().hex
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(corrupt_data)
        
        parser = MarketParser(storage_file=self.storage_file)
        data = parser.load_data(self.storage_file)
        self.assertIsNone(data)

    def test_market_report_generator_symbol_report(self):
        test_price = round(random.uniform(1.0, 500.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.random_symbol, price=test_price)

        report_gen = MarketReportGenerator(storage_file=self.storage_file)
        report = report_gen.generate_symbol_report(self.random_symbol)
        
        self.assertIn(self.random_symbol, report)
        self.assertIn(str(test_price), report)

    def test_market_report_generator_no_data(self):
        report_gen = MarketReportGenerator(storage_file=self.storage_file)
        report = report_gen.generate_symbol_report(self.random_symbol)
        
        self.assertIn(self.random_symbol, report)
        self.assertIn("No data", report)

    def test_market_report_generator_raw_stream_dump(self):
        test_content = json.dumps({uuid.uuid4().hex: random.randint(1, 100)})
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(test_content)

        report_gen = MarketReportGenerator(storage_file=self.storage_file)
        dump = report_gen.get_raw_stream_dump()
        self.assertEqual(dump, test_content)

    def test_market_report_generator_raw_stream_dump_io_error(self):
        report_gen = MarketReportGenerator(storage_file=self.storage_file)
        with patch("builtins.open", side_effect=IOError("Disk failure")):
            dump = report_gen.get_raw_stream_dump()
            self.assertEqual(dump, "{}")

    def test_generate_market_report_function(self):
        test_price = round(random.uniform(50.0, 150.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.random_symbol, price=test_price)

        res = generate_market_report(storage_file=self.storage_file, symbol=self.random_symbol)
        self.assertIn(self.random_symbol, res)
        self.assertIn(str(test_price), res)

    def test_run_market_telegram_pipeline(self):
        test_price = round(random.uniform(200.0, 300.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.random_symbol, price=test_price)

        pipeline_result = run_market_telegram_pipeline(
            storage_file=self.storage_file,
            symbol=self.random_symbol,
            chat_id=self.random_chat_id,
            url=self.random_url,
            telegram_token=self.random_token
        )

        self.assertIsInstance(pipeline_result, dict)
        self.assertEqual(pipeline_result["status"], "success")
        self.assertEqual(pipeline_result["symbol"], self.random_symbol)
        self.assertEqual(pipeline_result["price"], test_price)
        self.assertEqual(pipeline_result["chat_id"], self.random_chat_id)
        self.assertEqual(pipeline_result["url"], self.random_url)

    def test_export_audit_logs_success(self):
        random_log_content = uuid.uuid4().hex
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(random_log_content)

        exported = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(exported)

    def test_export_audit_logs_empty(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("")

        exported = export_audit_logs(storage_file=self.storage_file)
        self.assertFalse(exported)

    def test_export_audit_logs_not_found(self):
        missing_file = f"audit_{uuid.uuid4().hex}.log"
        exported = export_audit_logs(storage_file=missing_file)
        self.assertFalse(exported)

    def test_export_audit_logs_io_error(self):
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", side_effect=IOError("Read error")):
            exported = export_audit_logs(storage_file=self.storage_file)
            self.assertFalse(exported)

    def test_run_pipeline(self):
        result = run_pipeline(
            symbol=self.random_symbol,
            url=self.random_url,
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(result)

    def test_start_new(self):
        result = start_new(
            symbol=self.random_symbol,
            url=self.random_url,
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(result)

    def test_start_ened_alias(self):
        result = start_ened(
            symbol=self.random_symbol,
            url=self.random_url,
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(result)

    def test_market_parser_stream_io_bytes(self):
        garbage_bytes = uuid.uuid4().bytes
        mock_stream = io.BytesIO(garbage_bytes)
        
        with patch("builtins.open", return_value=mock_stream):
            parser = MarketParser(storage_file=self.storage_file)
            data = parser.load_data(self.storage_file)
            self.assertIsNone(data)


if __name__ == "__main__":
    unittest.main()