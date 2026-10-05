import unittest
from unittest.mock import patch
import json
import os
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
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://{uuid.uuid4().hex}.com/api"
        self.telegram_token = f"{random.randint(1000,9999)}:{uuid.uuid4().hex[:16]}"
        self.chat_id = str(random.randint(100000, 999999))
        self.price = round(random.uniform(1.0, 1000.0), 4)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_market_parser_fetch_and_load(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)
        
        data = parser.load_data(storage_file=self.storage_file)
        self.assertIsInstance(data, dict)
        self.assertIn(self.symbol, data)
        self.assertEqual(data[self.symbol], self.price)

    def test_market_parser_load_data_none_and_missing(self):
        parser = MarketParser(storage_file=None)
        self.assertIsNone(parser.load_data(None))
        
        non_existent = f"{uuid.uuid4().hex}.json"
        parser_missing = MarketParser(storage_file=non_existent)
        self.assertEqual(parser_missing.load_data(non_existent), {})

    def test_market_parser_corrupted_json(self):
        corrupted_prefix = "{"
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(corrupted_prefix)
        
        parser = MarketParser(storage_file=self.storage_file)
        data = parser.load_data(self.storage_file)
        self.assertEqual(data, {})

    def test_market_parser_invalid_json_content(self):
        invalid_content = uuid.uuid4().hex
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(invalid_content)
        
        parser = MarketParser(storage_file=self.storage_file)
        data = parser.load_data(self.storage_file)
        self.assertEqual(data, {})

    def test_market_parser_binary_content_mock(self):
        binary_data = uuid.uuid4().bytes
        mock_file = io.BytesIO(binary_data)
        
        with patch("builtins.open", return_value=mock_file):
            parser = MarketParser(storage_file=self.storage_file)
            data = parser.load_data(self.storage_file)
            self.assertEqual(data, {})

    def test_market_report_generator_symbol_report(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)
        
        gen = MarketReportGenerator(storage_file=self.storage_file)
        report = gen.generate_symbol_report(symbol=self.symbol)
        self.assertIn(self.symbol, report)
        self.assertIn(str(self.price), report)

    def test_market_report_generator_no_data(self):
        gen = MarketReportGenerator(storage_file=self.storage_file)
        report = gen.generate_symbol_report(symbol=self.symbol)
        self.assertIn("No data", report)

    def test_market_report_generator_raw_stream_dump(self):
        gen = MarketReportGenerator(storage_file=None)
        self.assertEqual(gen.get_raw_stream_dump(), "{}")
        
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)
        
        gen_valid = MarketReportGenerator(storage_file=self.storage_file)
        dump = gen_valid.get_raw_stream_dump()
        self.assertIn(self.symbol, dump)

    def test_generate_market_report_wrapper(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)
        
        report = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
        self.assertIn(self.symbol, report)

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

    def test_run_pipeline_execution(self):
        res = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res)

    def test_start_new_and_ened_aliases(self):
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

    def test_export_audit_logs_non_existent(self):
        self.assertFalse(export_audit_logs(storage_file=None))
        self.assertFalse(export_audit_logs(storage_file=f"{uuid.uuid4().hex}.json"))

    def test_export_audit_logs_valid_dict(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)
        
        self.assertTrue(export_audit_logs(storage_file=self.storage_file))

    def test_export_audit_logs_empty_file(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("   ")
        
        self.assertFalse(export_audit_logs(storage_file=self.storage_file))

    def test_export_audit_logs_corrupted_start(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("{invalid_json_" + uuid.uuid4().hex)
        
        self.assertTrue(export_audit_logs(storage_file=self.storage_file))

    def test_export_audit_logs_invalid_json_type(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(f'"{uuid.uuid4().hex}"')
        
        self.assertFalse(export_audit_logs(storage_file=self.storage_file))

if __name__ == "__main__":
    unittest.main()