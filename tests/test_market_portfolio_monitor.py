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
        self.telegram_token = f"{random.randint(100000, 999999)}:AAF{uuid.uuid4().hex[:10]}"
        self.chat_id = f"@{uuid.uuid4().hex[:6]}"
        self.storage_file = f"store_{uuid.uuid4().hex[:8]}.json"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_market_parser_fetch_and_store_new_file(self):
        price = round(random.uniform(10.0, 1500.0), 4)
        parser = MarketParser(storage_file=self.storage_file)
        
        parser.fetch_and_store(symbol=self.symbol, price=price)
        
        self.assertTrue(os.path.exists(self.storage_file))
        with open(self.storage_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn(self.symbol, data)
        self.assertEqual(data[self.symbol], price)

    def test_market_parser_load_data_invalid_json(self):
        corrupted_data = f"CORRUPTED_{uuid.uuid4().hex}"
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(corrupted_data)

        parser = MarketParser(storage_file=self.storage_file)
        data = parser.load_data(self.storage_file)
        self.assertIsNone(data)

    def test_market_parser_load_data_empty_file(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("   \n ")

        parser = MarketParser(storage_file=self.storage_file)
        data = parser.load_data(self.storage_file)
        self.assertEqual(data, {})

    def test_market_report_generator_symbol_report_exists(self):
        price = round(random.uniform(1.0, 500.0), 2)
        initial_data = {self.symbol: price}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        generator = MarketReportGenerator(storage_file=self.storage_file)
        report = generator.generate_symbol_report(symbol=self.symbol)
        
        expected_substring = f"Report for {self.symbol}: {price}"
        self.assertEqual(report, expected_substring)

    def test_market_report_generator_symbol_report_missing(self):
        other_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        generator = MarketReportGenerator(storage_file=self.storage_file)
        report = generator.generate_symbol_report(symbol=other_symbol)
        
        expected_substring = f"Report for {other_symbol}: No data"
        self.assertEqual(report, expected_substring)

    def test_market_report_generator_raw_stream_dump(self):
        dump_content = f"{uuid.uuid4().hex}:{random.randint(1, 100)}"
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(dump_content)

        generator = MarketReportGenerator(storage_file=self.storage_file)
        content = generator.get_raw_stream_dump()
        self.assertEqual(content, dump_content)

    def test_generate_market_report_function(self):
        price = round(random.uniform(50.0, 300.0), 2)
        initial_data = {self.symbol: price}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        report = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
        self.assertIn(str(price), report)
        self.assertIn(self.symbol, report)

    def test_run_market_telegram_pipeline(self):
        price = round(random.uniform(100.0, 1000.0), 2)
        initial_data = {self.symbol: price}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        result = run_market_telegram_pipeline(
            storage_file=self.storage_file,
            symbol=self.symbol,
            chat_id=self.chat_id,
            url=self.url,
            telegram_token=self.telegram_token
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["symbol"], self.symbol)
        self.assertEqual(result["price"], price)
        self.assertEqual(result["chat_id"], self.chat_id)
        self.assertEqual(result["url"], self.url)

    def test_export_audit_logs_valid(self):
        audit_payload = {uuid.uuid4().hex: random.randint(1, 500)}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(audit_payload, f)

        result = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(result)

    def test_export_audit_logs_invalid(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(f"INVALID_JSON_{uuid.uuid4().hex}")

        result = export_audit_logs(storage_file=self.storage_file)
        self.assertFalse(result)

    def test_export_audit_logs_missing_file(self):
        missing_path = f"missing_{uuid.uuid4().hex}.json"
        result = export_audit_logs(storage_file=missing_path)
        self.assertFalse(result)

    def test_run_pipeline_execution(self):
        initial_price = round(random.uniform(10.0, 99.9), 2)
        initial_data = {self.symbol: initial_price}
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

    def test_start_new_and_ened_aliases(self):
        initial_price = round(random.uniform(200.0, 500.0), 2)
        initial_data = {self.symbol: initial_price}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

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

    def test_io_bytes_stream_mocking_parser(self):
        random_garbage = f"GARBAGE_{uuid.uuid4().hex}".encode("utf-8")
        mock_file = io.BytesIO(random_garbage)
        
        with patch("builtins.open", mock_open(read_data=random_garbage.decode("utf-8"))):
            parser = MarketParser(storage_file=self.storage_file)
            data = parser.load_data(self.storage_file)
            self.assertIsNone(data)


if __name__ == "__main__":
    unittest.main()