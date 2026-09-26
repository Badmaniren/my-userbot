import unittest
from unittest.mock import patch, mock_open
import os
import json
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
        self.random_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.random_url = f"https://{uuid.uuid4().hex}.com/{uuid.uuid4().hex}"
        self.random_token = uuid.uuid4().hex
        self.random_chat_id = str(random.randint(100000, 99999999))
        self.random_storage_file = f"{uuid.uuid4().hex}.json"

    def test_market_parser_fetch_and_store(self):
        random_price = round(random.uniform(10.0, 1000.0), 2)
        parser = MarketParser(storage_file=self.random_storage_file)
        
        mock_file_data = io.StringIO()
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=json.dumps({self.random_symbol: 1.0}))) as mocked_file:
            
            parser.fetch_and_store(self.random_symbol, random_price)
            mocked_file.assert_called()

    def test_market_parser_load_data_valid(self):
        parser = MarketParser(storage_file=self.random_storage_file)
        random_val = random.randint(50, 500)
        payload = json.dumps({self.random_symbol: random_val})

        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=payload)):
            data = parser.load_data(self.random_storage_file)
            self.assertIsInstance(data, dict)
            self.assertEqual(data.get(self.random_symbol), random_val)

    def test_market_parser_load_data_corrupted(self):
        parser = MarketParser(storage_file=self.random_storage_file)
        corrupted_data = "{" + uuid.uuid4().hex

        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=corrupted_data)):
            data = parser.load_data(self.random_storage_file)
            self.assertIsNone(data)

    def test_market_parser_load_data_missing(self):
        parser = MarketParser(storage_file=self.random_storage_file)
        with patch("os.path.exists", return_value=False):
            data = parser.load_data(self.random_storage_file)
            self.assertIsNone(data)

    def test_market_report_generator_with_data(self):
        generator = MarketReportGenerator(storage_file=self.random_storage_file)
        random_price = round(random.uniform(1.0, 500.0), 2)
        mock_data = {self.random_symbol: random_price}

        with patch.object(MarketParser, 'load_data', return_value=mock_data):
            report = generator.generate_symbol_report(self.random_symbol)
            self.assertIn(self.random_symbol, report)
            self.assertIn(str(random_price), report)

    def test_market_report_generator_no_data(self):
        generator = MarketReportGenerator(storage_file=self.random_storage_file)

        with patch.object(MarketParser, 'load_data', return_value={}):
            report = generator.generate_symbol_report(self.random_symbol)
            self.assertIn(self.random_symbol, report)
            self.assertIn("No data", report)

    def test_market_report_generator_raw_stream_dump(self):
        generator = MarketReportGenerator(storage_file=self.random_storage_file)
        random_dump = json.dumps({uuid.uuid4().hex: uuid.uuid4().hex})

        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=random_dump)):
            stream = generator.get_raw_stream_dump()
            self.assertEqual(stream, random_dump)

    def test_market_report_generator_raw_stream_dump_io_error(self):
        generator = MarketReportGenerator(storage_file=self.random_storage_file)

        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", side_effect=IOError):
            stream = generator.get_raw_stream_dump()
            self.assertEqual(stream, "{}")

    def test_generate_market_report(self):
        random_price = round(random.uniform(5.0, 50.0), 2)
        with patch.object(MarketReportGenerator, 'generate_symbol_report', return_value=f"Report for {self.random_symbol}: {random_price}"):
            res = generate_market_report(self.random_storage_file, self.random_symbol)
            self.assertIn(self.random_symbol, res)

    def test_run_market_telegram_pipeline(self):
        random_price = round(random.uniform(100.0, 999.0), 2)
        mock_data = {self.random_symbol: random_price}

        with patch.object(MarketParser, 'load_data', return_value=mock_data):
            response = run_market_telegram_pipeline(
                storage_file=self.random_storage_file,
                symbol=self.random_symbol,
                chat_id=self.random_chat_id,
                url=self.random_url,
                telegram_token=self.random_token
            )
            self.assertEqual(response["status"], "success")
            self.assertEqual(response["symbol"], self.random_symbol)
            self.assertEqual(response["price"], random_price)
            self.assertEqual(response["chat_id"], self.random_chat_id)
            self.assertEqual(response["url"], self.random_url)

    def test_export_audit_logs_success(self):
        random_content = uuid.uuid4().hex
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=random_content)):
            result = export_audit_logs(storage_file=self.random_storage_file)
            self.assertTrue(result)

    def test_export_audit_logs_empty(self):
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data="")):
            result = export_audit_logs(storage_file=self.random_storage_file)
            self.assertFalse(result)

    def test_export_audit_logs_missing(self):
        with patch("os.path.exists", return_value=False):
            result = export_audit_logs(storage_file=self.random_storage_file)
            self.assertFalse(result)

    def test_run_pipeline(self):
        with patch.object(MarketParser, 'fetch_and_store'), \
             patch.object(MarketReportGenerator, 'generate_symbol_report'), \
             patch("skills.market_portfolio_monitor.generate_market_report"), \
             patch("skills.market_portfolio_monitor.run_market_telegram_pipeline"):
            
            res = run_pipeline(
                symbol=self.random_symbol,
                url=self.random_url,
                telegram_token=self.random_token,
                chat_id=self.random_chat_id,
                storage_file=self.random_storage_file
            )
            self.assertTrue(res)

    def test_start_new(self):
        with patch("skills.market_portfolio_monitor.run_pipeline", return_value=True) as mocked_run:
            res = start_new(
                symbol=self.random_symbol,
                url=self.random_url,
                telegram_token=self.random_token,
                chat_id=self.random_chat_id,
                storage_file=self.random_storage_file
            )
            mocked_run.assert_called_once()
            self.assertTrue(res)

    def test_start_ened(self):
        with patch("skills.market_portfolio_monitor.start_new", return_value=True) as mocked_start:
            res = start_ened(
                symbol=self.random_symbol,
                url=self.random_url,
                telegram_token=self.random_token,
                chat_id=self.random_chat_id,
                storage_file=self.random_storage_file
            )
            mocked_start.assert_called_once()
            self.assertTrue(res)


if __name__ == '__main__':
    unittest.main()