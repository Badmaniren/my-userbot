import unittest
from unittest.mock import patch, mock_open
import uuid
import random
import io
import json
import os

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
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.price = round(random.uniform(10.0, 1500.0), 2)
        self.chat_id = str(random.randint(100000, 999999))
        self.url = f"https://{uuid.uuid4().hex[:8]}.com/api/v1"
        self.telegram_token = f"{random.randint(100,999)}:BOT-{uuid.uuid4().hex[:8]}"
        self.storage_file = f"store_{uuid.uuid4().hex[:8]}.json"

    def test_market_parser_fetch_and_store(self):
        parser = MarketParser(storage_file=self.storage_file)
        mock_file_data = io.StringIO(json.dumps({self.symbol: self.price}))

        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=json.dumps({self.symbol: self.price}))) as mock_file:

            parser.fetch_and_store(symbol=self.symbol, price=self.price)
            self.assertTrue(mock_file.called)

    def test_market_parser_load_data_success(self):
        parser = MarketParser(storage_file=self.storage_file)
        payload = {self.symbol: self.price}

        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=json.dumps(payload))):

            data = parser.load_data(self.storage_file)
            self.assertIsInstance(data, dict)
            self.assertIn(self.symbol, data)
            self.assertEqual(data[self.symbol], self.price)

    def test_market_parser_load_data_not_found(self):
        parser = MarketParser(storage_file=self.storage_file)
        with patch("os.path.exists", return_value=False):
            data = parser.load_data(self.storage_file)
            self.assertIsNone(data)

    def test_market_parser_load_data_corrupted(self):
        parser = MarketParser(storage_file=self.storage_file)
        corrupted_bytes = io.BytesIO(b"INVALID_JSON_STREAM_" + uuid.uuid4().bytes)
        
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data="INVALID_JSON")):

            data = parser.load_data(self.storage_file)
            self.assertIsNone(data)

    def test_market_report_generator_symbol_exists(self):
        generator = MarketReportGenerator(storage_file=self.storage_file)
        payload = {self.symbol: self.price}
        
        with patch.object(MarketParser, "load_data", return_value=payload):
            report = generator.generate_symbol_report(symbol=self.symbol)
            self.assertIn(self.symbol, report)
            self.assertIn(str(self.price), report)

    def test_market_report_generator_symbol_missing(self):
        generator = MarketReportGenerator(storage_file=self.storage_file)
        other_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        payload = {other_symbol: self.price}

        with patch.object(MarketParser, "load_data", return_value=payload):
            report = generator.generate_symbol_report(symbol=self.symbol)
            self.assertIn(self.symbol, report)
            self.assertIn("No data", report)

    def test_get_raw_stream_dump(self):
        generator = MarketReportGenerator(storage_file=self.storage_file)
        random_content = uuid.uuid4().hex

        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=random_content)):

            dump = generator.get_raw_stream_dump()
            self.assertEqual(dump, random_content)

    def test_get_raw_stream_dump_io_error(self):
        generator = MarketReportGenerator(storage_file=self.storage_file)

        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", side_effect=IOError):

            dump = generator.get_raw_stream_dump()
            self.assertEqual(dump, "{}")

    def test_generate_market_report_wrapper(self):
        payload = {self.symbol: self.price}
        with patch.object(MarketParser, "load_data", return_value=payload):
            res = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
            self.assertIn(self.symbol, res)

    def test_run_market_telegram_pipeline(self):
        payload = {self.symbol: self.price}
        with patch.object(MarketParser, "load_data", return_value=payload):
            res = run_market_telegram_pipeline(
                storage_file=self.storage_file,
                symbol=self.symbol,
                chat_id=self.chat_id,
                url=self.url,
                telegram_token=self.telegram_token
            )
            self.assertEqual(res["status"], "success")
            self.assertEqual(res["symbol"], self.symbol)
            self.assertEqual(res["price"], self.price)
            self.assertEqual(res["chat_id"], self.chat_id)
            self.assertEqual(res["url"], self.url)

    def test_export_audit_logs_success(self):
        log_content = f"LOG_DATA_{uuid.uuid4().hex}"
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=log_content)):

            result = export_audit_logs(storage_file=self.storage_file)
            self.assertTrue(result)

    def test_export_audit_logs_empty(self):
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data="")):

            result = export_audit_logs(storage_file=self.storage_file)
            self.assertFalse(result)

    def test_export_audit_logs_io_error(self):
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", side_effect=IOError):

            result = export_audit_logs(storage_file=self.storage_file)
            self.assertFalse(result)

    def test_run_pipeline(self):
        with patch.object(MarketParser, "fetch_and_store") as mock_fetch, \
             patch.object(MarketReportGenerator, "generate_symbol_report") as mock_gen, \
             patch("skills.market_portfolio_monitor.generate_market_report") as mock_gen_market, \
             patch("skills.market_portfolio_monitor.run_market_telegram_pipeline") as mock_telegram:

            res = run_pipeline(
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                storage_file=self.storage_file
            )
            self.assertTrue(res)
            mock_fetch.assert_called_once()
            mock_gen.assert_called_once()
            mock_gen_market.assert_called_once()
            mock_telegram.assert_called_once()

    def test_start_new_and_ened(self):
        with patch("skills.market_portfolio_monitor.run_pipeline", return_value=True) as mock_run:
            res_new = start_new(
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                storage_file=self.storage_file
            )
            res_ened = start_ened(
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                storage_file=self.storage_file
            )
            self.assertTrue(res_new)
            self.assertTrue(res_ened)
            self.assertEqual(mock_run.call_count, 2)

if __name__ == "__main__":
    unittest.main()