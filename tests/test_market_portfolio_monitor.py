import unittest
from unittest.mock import patch, MagicMock
import os
import json
import uuid
import random
import io
import sys

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
        self.random_storage = f"test_storage_{uuid.uuid4().hex[:8]}.json"
        self.random_price = round(random.uniform(10.0, 5000.0), 2)

    def tearDown(self):
        if os.path.exists(self.random_storage):
            try:
                os.remove(self.random_storage)
            except OSError:
                pass

    def test_market_parser_fetch_and_load(self):
        parser = MarketParser(storage_file=self.random_storage)
        parser.fetch_and_store(symbol=self.random_symbol, price=self.random_price)
        
        loaded_data = parser.load_data(self.random_storage)
        self.assertIsInstance(loaded_data, dict)
        self.assertIn(self.random_symbol, loaded_data)
        self.assertEqual(loaded_data[self.random_symbol], self.random_price)

    def test_market_parser_load_nonexistent(self):
        non_existent_file = f"non_{uuid.uuid4().hex}.json"
        parser = MarketParser(storage_file=non_existent_file)
        result = parser.load_data(non_existent_file)
        self.assertIsNone(result)

    def test_market_parser_load_corrupted_json(self):
        corrupt_data = f"CORRUPT_DATA_{uuid.uuid4().hex}"
        with open(self.random_storage, "w", encoding="utf-8") as f:
            f.write(corrupt_data)

        parser = MarketParser(storage_file=self.random_storage)
        result = parser.load_data(self.random_storage)
        self.assertIsNone(result)

    def test_market_report_generator_symbol_report(self):
        parser = MarketParser(storage_file=self.random_storage)
        parser.fetch_and_store(symbol=self.random_symbol, price=self.random_price)

        generator = MarketReportGenerator(storage_file=self.random_storage)
        report = generator.generate_symbol_report(self.random_symbol)
        
        self.assertIn(self.random_symbol, report)
        self.assertIn(str(self.random_price), report)

    def test_market_report_generator_no_data(self):
        generator = MarketReportGenerator(storage_file=self.random_storage)
        report = generator.generate_symbol_report(self.random_symbol)
        
        self.assertIn(self.random_symbol, report)
        self.assertIn("No data", report)

    def test_market_report_generator_raw_stream_dump(self):
        parser = MarketParser(storage_file=self.random_storage)
        parser.fetch_and_store(symbol=self.random_symbol, price=self.random_price)

        generator = MarketReportGenerator(storage_file=self.random_storage)
        dump = generator.get_raw_stream_dump()

        self.assertIsInstance(dump, str)
        parsed_dump = json.loads(dump)
        self.assertEqual(parsed_dump.get(self.random_symbol), self.random_price)

    def test_generate_market_report_helper(self):
        parser = MarketParser(storage_file=self.random_storage)
        parser.fetch_and_store(symbol=self.random_symbol, price=self.random_price)

        report = generate_market_report(storage_file=self.random_storage, symbol=self.random_symbol)
        self.assertIn(self.random_symbol, report)
        self.assertIn(str(self.random_price), report)

    def test_run_market_telegram_pipeline(self):
        parser = MarketParser(storage_file=self.random_storage)
        parser.fetch_and_store(symbol=self.random_symbol, price=self.random_price)

        pipeline_result = run_market_telegram_pipeline(
            storage_file=self.random_storage,
            symbol=self.random_symbol,
            chat_id=self.random_chat_id,
            url=self.random_url,
            telegram_token=self.random_token
        )

        self.assertEqual(pipeline_result["status"], "success")
        self.assertEqual(pipeline_result["symbol"], self.random_symbol)
        self.assertEqual(pipeline_result["price"], self.random_price)
        self.assertEqual(pipeline_result["chat_id"], self.random_chat_id)
        self.assertEqual(pipeline_result["url"], self.random_url)

    def test_run_pipeline_execution(self):
        success = run_pipeline(
            symbol=self.random_symbol,
            url=self.random_url,
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            storage_file=self.random_storage
        )
        self.assertTrue(success)

        parser = MarketParser(storage_file=self.random_storage)
        data = parser.load_data(self.random_storage)
        self.assertIn(self.random_symbol, data)

    def test_start_new_entrypoint(self):
        success = start_new(
            symbol=self.random_symbol,
            url=self.random_url,
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            storage_file=self.random_storage
        )
        self.assertTrue(success)

    def test_start_ened_alias(self):
        success = start_ened(
            symbol=self.random_symbol,
            url=self.random_url,
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            storage_file=self.random_storage
        )
        self.assertTrue(success)

    def test_export_audit_logs_success(self):
        test_payload = {uuid.uuid4().hex: random.randint(1, 100)}
        with open(self.random_storage, "w", encoding="utf-8") as f:
            json.dump(test_payload, f)

        export_result = export_audit_logs(storage_file=self.random_storage)
        self.assertTrue(export_result)

    def test_export_audit_logs_failure_empty(self):
        with open(self.random_storage, "w", encoding="utf-8") as f:
            f.write("   \n  ")

        export_result = export_audit_logs(storage_file=self.random_storage)
        self.assertFalse(export_result)

    def test_export_audit_logs_failure_missing(self):
        missing_file = f"missing_{uuid.uuid4().hex}.json"
        export_result = export_audit_logs(storage_file=missing_file)
        self.assertFalse(export_result)

    def test_export_audit_logs_none(self):
        export_result = export_audit_logs(storage_file=None)
        self.assertFalse(export_result)

    def test_stream_mock_io_behavior(self):
        random_bytes = f'{{"{self.random_symbol}": {self.random_price}}}'.encode('utf-8')
        mock_file_stream = io.BytesIO(random_bytes)

        with patch("builtins.open", return_value=io.StringIO(mock_file_stream.read().decode('utf-8'))):
            generator = MarketReportGenerator(storage_file=self.random_storage)
            dump = generator.get_raw_stream_dump()
            self.assertIn(self.random_symbol, dump)