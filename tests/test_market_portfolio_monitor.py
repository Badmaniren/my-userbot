import unittest
from unittest.mock import patch, mock_open
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
        self.random_file = f"{uuid.uuid4().hex}.json"
        self.random_url = f"https://{uuid.uuid4().hex[:8]}.com/api"
        self.random_token = uuid.uuid4().hex
        self.random_chat_id = str(random.randint(100000, 999999))
        self.random_price = round(random.uniform(10.0, 1500.0), 2)

    def test_market_parser_fetch_and_store(self):
        parser = MarketParser(storage_file=self.random_file)
        mock_data_json = json.dumps({self.random_symbol: self.random_price})
        
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=mock_data_json)) as mocked_file:
            parser.fetch_and_store(self.random_symbol, self.random_price)
            mocked_file.assert_called()

    def test_market_parser_load_data_success(self):
        parser = MarketParser(storage_file=self.random_file)
        expected_data = {self.random_symbol: self.random_price}
        mock_data_json = json.dumps(expected_data)

        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=mock_data_json)):
            result = parser.load_data(self.random_file)
            self.assertEqual(result, expected_data)

    def test_market_parser_load_data_file_not_found(self):
        parser = MarketParser(storage_file=self.random_file)
        with patch("os.path.exists", return_value=False):
            result = parser.load_data(self.random_file)
            self.assertIsNone(result)

    def test_market_report_generator_success(self):
        generator = MarketReportGenerator(storage_file=self.random_file)
        mock_data = {self.random_symbol: self.random_price}

        with patch.object(MarketParser, "load_data", return_value=mock_data):
            report = generator.generate_symbol_report(self.random_symbol)
            self.assertIn(self.random_symbol, report)
            self.assertIn(str(self.random_price), report)

    def test_market_report_generator_no_data(self):
        generator = MarketReportGenerator(storage_file=self.random_file)

        with patch.object(MarketParser, "load_data", return_value={}):
            report = generator.generate_symbol_report(self.random_symbol)
            self.assertIn("No data", report)

    def test_get_raw_stream_dump(self):
        generator = MarketReportGenerator(storage_file=self.random_file)
        random_content = uuid.uuid4().hex

        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=random_content)):
            stream_dump = generator.get_raw_stream_dump()
            self.assertEqual(stream_dump, random_content)

    def test_generate_market_report(self):
        mock_data = {self.random_symbol: self.random_price}
        with patch.object(MarketParser, "load_data", return_value=mock_data):
            report = generate_market_report(self.random_file, self.random_symbol)
            self.assertIn(self.random_symbol, report)

    def test_run_market_telegram_pipeline(self):
        mock_data = {self.random_symbol: self.random_price}
        with patch.object(MarketParser, "load_data", return_value=mock_data):
            response = run_market_telegram_pipeline(
                storage_file=self.random_file,
                symbol=self.random_symbol,
                chat_id=self.random_chat_id,
                url=self.random_url,
                telegram_token=self.random_token
            )
            self.assertEqual(response["status"], "success")
            self.assertEqual(response["symbol"], self.random_symbol)
            self.assertEqual(response["price"], self.random_price)
            self.assertEqual(response["chat_id"], self.random_chat_id)
            self.assertEqual(response["url"], self.random_url)

    def test_export_audit_logs_valid(self):
        random_log_content = uuid.uuid4().hex
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=random_log_content)):
            result = export_audit_logs(self.random_file)
            self.assertTrue(result)

    def test_export_audit_logs_empty(self):
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data="")):
            result = export_audit_logs(self.random_file)
            self.assertFalse(result)

    def test_export_audit_logs_no_file(self):
        with patch("os.path.exists", return_value=False):
            result = export_audit_logs(self.random_file)
            self.assertFalse(result)

    def test_run_pipeline(self):
        mock_data = {self.random_symbol: self.random_price}
        with patch.object(MarketParser, "fetch_and_store") as mock_fetch, \
             patch.object(MarketParser, "load_data", return_value=mock_data):

            result = run_pipeline(
                symbol=self.random_symbol,
                url=self.random_url,
                telegram_token=self.random_token,
                chat_id=self.random_chat_id,
                storage_file=self.random_file
            )
            self.assertTrue(result)
            mock_fetch.assert_called_once()

    def test_start_new(self):
        with patch("skills.market_portfolio_monitor.run_pipeline", return_value=True) as mock_run:
            result = start_new(
                symbol=self.random_symbol,
                url=self.random_url,
                telegram_token=self.random_token,
                chat_id=self.random_chat_id,
                storage_file=self.random_file
            )
            self.assertTrue(result)
            mock_run.assert_called_once()

    def test_start_ened(self):
        with patch("skills.market_portfolio_monitor.start_new", return_value=True) as mock_start:
            result = start_ened(
                symbol=self.random_symbol,
                url=self.random_url,
                telegram_token=self.random_token,
                chat_id=self.random_chat_id,
                storage_file=self.random_file
            )
            self.assertTrue(result)
            mock_start.assert_called_once()

    def test_market_parser_load_data_decode_error(self):
        parser = MarketParser(storage_file=self.random_file)
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data="INVALID_JSON")):
            result = parser.load_data(self.random_file)
            self.assertIsNone(result)

    def test_market_report_generator_stream_dump_io_error(self):
        generator = MarketReportGenerator(storage_file=self.random_file)
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", side_effect=IOError):
            dump = generator.get_raw_stream_dump()
            self.assertEqual(dump, "{}")

if __name__ == "__main__":
    unittest.main()