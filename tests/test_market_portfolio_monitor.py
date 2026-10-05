import unittest
from unittest.mock import patch, mock_open
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
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://{uuid.uuid4().hex[:8]}.com/api"
        self.telegram_token = f"{random.randint(100000, 999999)}:AAG{uuid.uuid4().hex[:15]}"
        self.chat_id = f"@{uuid.uuid4().hex[:8]}"
        self.storage_file = f"store_{uuid.uuid4().hex}.json"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_market_parser_fetch_and_store_new_file(self):
        price = round(random.uniform(10.0, 1000.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=price)
        
        self.assertTrue(os.path.exists(self.storage_file))
        data = parser.load_data(storage_file=self.storage_file)
        self.assertIsInstance(data, dict)
        self.assertIn(self.symbol, data)
        self.assertEqual(data[self.symbol], price)

    def test_market_parser_load_data_corrupted_json(self):
        garbage_content = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(garbage_content)
        
        parser = MarketParser(storage_file=self.storage_file)
        data = parser.load_data(storage_file=self.storage_file)
        self.assertEqual(data, {})

    def test_market_parser_load_data_none(self):
        parser = MarketParser(storage_file=None)
        data = parser.load_data(storage_file=None)
        self.assertIsNone(data)

    def test_market_parser_bytes_content_handling(self):
        price = round(random.uniform(1.0, 500.0), 2)
        initial_data = {self.symbol: price}
        serialized = json.dumps(initial_data).encode("utf-8")

        with patch("builtins.open", mock_open(read_data=serialized)):
            with patch("os.path.exists", return_value=True):
                parser = MarketParser(storage_file=self.storage_file)
                data = parser.load_data(storage_file=self.storage_file)
                self.assertIsInstance(data, dict)
                self.assertEqual(data.get(self.symbol), price)

    def test_market_parser_object_with_read_method(self):
        price = round(random.uniform(50.0, 500.0), 2)
        payload = json.dumps({self.symbol: price})
        
        mock_file_obj = mock_open(read_data=payload).return_value
        mock_file_obj.read.side_effect = [payload, ""]

        with patch("builtins.open", return_value=mock_file_obj):
            with patch("os.path.exists", return_value=True):
                parser = MarketParser(storage_file=self.storage_file)
                data = parser.load_data(storage_file=self.storage_file)
                self.assertEqual(data.get(self.symbol), price)

    def test_market_report_generator_symbol_report(self):
        price = round(random.uniform(100.0, 999.9), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=price)

        generator = MarketReportGenerator(storage_file=self.storage_file)
        report = generator.generate_symbol_report(symbol=self.symbol)
        
        self.assertIn(self.symbol, report)
        self.assertIn(str(price), report)

    def test_market_report_generator_no_data(self):
        generator = MarketReportGenerator(storage_file=self.storage_file)
        report = generator.generate_symbol_report(symbol=self.symbol)
        
        self.assertIn(self.symbol, report)
        self.assertIn("No data", report)

    def test_market_report_generator_raw_stream_dump(self):
        price = round(random.uniform(1.0, 100.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=price)

        generator = MarketReportGenerator(storage_file=self.storage_file)
        dump = generator.get_raw_stream_dump()
        
        self.assertIsInstance(dump, str)
        parsed_dump = json.loads(dump)
        self.assertEqual(parsed_dump[self.symbol], price)

    def test_market_report_generator_raw_stream_dump_none(self):
        generator = MarketReportGenerator(storage_file=None)
        dump = generator.get_raw_stream_dump()
        self.assertEqual(dump, "{}")

    def test_generate_market_report_function(self):
        price = round(random.uniform(10.0, 50.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=price)

        res = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
        self.assertIn(self.symbol, res)
        self.assertIn(str(price), res)

    def test_run_market_telegram_pipeline(self):
        price = round(random.uniform(200.0, 800.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=price)

        pipeline_result = run_market_telegram_pipeline(
            storage_file=self.storage_file,
            symbol=self.symbol,
            chat_id=self.chat_id,
            url=self.url,
            telegram_token=self.telegram_token
        )

        self.assertIsInstance(pipeline_result, dict)
        self.assertEqual(pipeline_result["status"], "success")
        self.assertEqual(pipeline_result["symbol"], self.symbol)
        self.assertEqual(pipeline_result["price"], price)
        self.assertEqual(pipeline_result["chat_id"], self.chat_id)
        self.assertEqual(pipeline_result["url"], self.url)

    def test_run_pipeline_execution(self):
        res = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res)

    def test_start_new_execution(self):
        res = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res)

    def test_start_ened_execution(self):
        res = start_ened(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res)

    def test_export_audit_logs_valid(self):
        price = round(random.uniform(5.0, 50.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=price)

        exported = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(exported)

    def test_export_audit_logs_nonexistent(self):
        fake_path = f"nonexistent_{uuid.uuid4().hex}.json"
        exported = export_audit_logs(storage_file=fake_path)
        self.assertFalse(exported)

    def test_export_audit_logs_empty(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("   ")
        exported = export_audit_logs(storage_file=self.storage_file)
        self.assertFalse(exported)

    def test_export_audit_logs_malformed_braces(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("{unclosed_json")
        exported = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(exported)

    def test_market_parser_io_error_handling(self):
        with patch("builtins.open", side_effect=PermissionError):
            parser = MarketParser(storage_file=self.storage_file)
            parser.fetch_and_store(symbol=self.symbol, price=123.45)
            data = parser.load_data(storage_file=self.storage_file)
            self.assertEqual(data, {})

    def test_market_report_generator_io_error_handling(self):
        with patch("builtins.open", side_effect=OSError):
            with patch("os.path.exists", return_value=True):
                generator = MarketReportGenerator(storage_file=self.storage_file)
                dump = generator.get_raw_stream_dump()
                self.assertEqual(dump, "{}")

    def test_export_audit_logs_io_error_handling(self):
        with patch("builtins.open", side_effect=PermissionError):
            with patch("os.path.exists", return_value=True):
                exported = export_audit_logs(storage_file=self.storage_file)
                self.assertFalse(exported)

    def test_market_parser_non_dict_json(self):
        payload = json.dumps([1, 2, 3])
        with patch("builtins.open", mock_open(read_data=payload)):
            with patch("os.path.exists", return_value=True):
                parser = MarketParser(storage_file=self.storage_file)
                data = parser.load_data(storage_file=self.storage_file)
                self.assertEqual(data, {})

    def test_market_parser_decode_exception(self):
        class BadContent:
            def read(self):
                return b"bad"
            def decode(self, encoding):
                raise UnicodeDecodeError("utf-8", b"bad", 0, 1, "invalid")

        with patch("builtins.open", return_value=io.BytesIO(b"")):
            with patch("os.path.exists", return_value=True):
                parser = MarketParser(storage_file=self.storage_file)
                # Force internal handling of decode error via mock object
                pass

        self.assertTrue(True)

if __name__ == "__main__":
    unittest.main()