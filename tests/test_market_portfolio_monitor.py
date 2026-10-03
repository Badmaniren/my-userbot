import unittest
import json
import os
import tempfile
import uuid
import random
from unittest.mock import patch
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
        self.random_symbol = f"SYM_{uuid.uuid4().hex[:8].upper()}"
        self.random_url = f"https://{uuid.uuid4().hex[:6]}.org/api"
        self.random_token = uuid.uuid4().hex
        self.random_chat_id = str(random.randint(100000, 9999999))
        
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.temp_dir.name, f"{uuid.uuid4().hex}.json")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_market_parser_fetch_and_load(self):
        random_price = round(random.uniform(10.0, 1000.0), 4)
        parser = MarketParser(storage_file=self.storage_file)
        
        parser.fetch_and_store(symbol=self.random_symbol, price=random_price)
        self.assertTrue(os.path.exists(self.storage_file))

        loaded_data = parser.load_data(storage_file=self.storage_file)
        self.assertIsInstance(loaded_data, dict)
        self.assertIn(self.random_symbol, loaded_data)
        self.assertEqual(loaded_data[self.random_symbol], random_price)

    def test_market_parser_load_data_corrupted_file(self):
        garbage_content = uuid.uuid4().hex
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(garbage_content)

        parser = MarketParser(storage_file=self.storage_file)
        loaded_data = parser.load_data(storage_file=self.storage_file)
        self.assertIsNone(loaded_data)

    def test_market_parser_load_data_unterminated_object(self):
        malformed_json = '{"' + uuid.uuid4().hex + '": 123'
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(malformed_json)

        parser = MarketParser(storage_file=self.storage_file)
        with self.assertRaises(json.JSONDecodeError):
            parser.load_data(storage_file=self.storage_file)

    def test_market_report_generator_symbol_report(self):
        random_price = round(random.uniform(1.0, 500.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.random_symbol, price=random_price)

        report_gen = MarketReportGenerator(storage_file=self.storage_file)
        report = report_gen.generate_symbol_report(symbol=self.random_symbol)
        
        self.assertIn(self.random_symbol, report)
        self.assertIn(str(random_price), report)

    def test_market_report_generator_no_data(self):
        report_gen = MarketReportGenerator(storage_file=self.storage_file)
        report = report_gen.generate_symbol_report(symbol=self.random_symbol)
        
        self.assertIn(self.random_symbol, report)
        self.assertIn("No data", report)

    def test_market_report_generator_get_raw_stream_dump(self):
        random_price = round(random.uniform(50.0, 500.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.random_symbol, price=random_price)

        report_gen = MarketReportGenerator(storage_file=self.storage_file)
        dump = report_gen.get_raw_stream_dump()
        
        self.assertIsInstance(dump, str)
        parsed_dump = json.loads(dump)
        self.assertEqual(parsed_dump[self.random_symbol], random_price)

    def test_generate_market_report_function(self):
        random_price = round(random.uniform(0.1, 99.9), 3)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.random_symbol, price=random_price)

        report = generate_market_report(storage_file=self.storage_file, symbol=self.random_symbol)
        self.assertIn(self.random_symbol, report)
        self.assertIn(str(random_price), report)

    def test_run_market_telegram_pipeline(self):
        random_price = round(random.uniform(100.0, 200.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.random_symbol, price=random_price)

        result = run_market_telegram_pipeline(
            storage_file=self.storage_file,
            symbol=self.random_symbol,
            chat_id=self.random_chat_id,
            url=self.random_url,
            telegram_token=self.random_token
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("symbol"), self.random_symbol)
        self.assertEqual(result.get("price"), random_price)
        self.assertEqual(result.get("chat_id"), self.random_chat_id)
        self.assertEqual(result.get("url"), self.random_url)

    def test_run_pipeline_execution(self):
        res = run_pipeline(
            symbol=self.random_symbol,
            url=self.random_url,
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res)

    def test_start_new_and_start_ened_aliases(self):
        res_new = start_new(
            symbol=self.random_symbol,
            url=self.random_url,
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res_new)

        res_ened = start_ened(
            symbol=self.random_symbol,
            url=self.random_url,
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res_ened)

    def test_export_audit_logs_valid(self):
        random_data = {uuid.uuid4().hex: random.randint(1, 100)}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(random_data, f)

        export_result = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(export_result)

    def test_export_audit_logs_invalid(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(uuid.uuid4().hex)

        export_result = export_audit_logs(storage_file=self.storage_file)
        self.assertFalse(export_result)

    def test_export_audit_logs_nonexistent(self):
        nonexistent_path = os.path.join(self.temp_dir.name, f"{uuid.uuid4().hex}.json")
        export_result = export_audit_logs(storage_file=nonexistent_path)
        self.assertFalse(export_result)

    def test_bytes_io_mock_stream_behavior(self):
        random_bytes = uuid.uuid4().bytes
        stream = io.BytesIO(random_bytes)
        
        with patch("builtins.open") as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = stream.read().decode('latin1', errors='ignore')
            parser = MarketParser(storage_file=self.storage_file)
            data = parser.load_data(storage_file=self.storage_file)
            self.assertIsNone(data)


if __name__ == "__main__":
    unittest.main()