import unittest
from unittest.mock import patch, mock_open
import io
import json
import os
import random
import uuid
from skills.market_portfolio_monitor import (
    run_pipeline,
    start_new,
    start_ened,
    MarketParser,
    MarketReportGenerator,
    generate_market_report,
    run_market_telegram_pipeline,
    export_audit_logs,
)


class TestMarketPortfolioMonitor(unittest.TestCase):

    def setUp(self):
        self.symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        self.url = f"https://{uuid.uuid4().hex[:8]}.com/api"
        self.telegram_token = uuid.uuid4().hex
        self.chat_id = str(random.randint(100000, 999999))
        self.storage_file = f"storage_{uuid.uuid4().hex[:8]}.json"
        self.random_price = round(random.uniform(1.0, 1000.0), 2)

    def test_market_parser_with_bytesio_mock_stream(self):
        raw_data = json.dumps({self.symbol: self.random_price}).encode("utf-8")
        mock_stream = io.BytesIO(raw_data)

        parser = MarketParser(storage_file=self.storage_file)
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=raw_data.decode("utf-8"))):
                data = parser.load_data(self.storage_file)
                self.assertIsNotNone(data)
                self.assertIn(self.symbol, data)
                self.assertEqual(data[self.symbol], self.random_price)

    def test_market_parser_fetch_and_store(self):
        parser = MarketParser(storage_file=self.storage_file)
        written_data = {}

        def mock_file_write(file, mode="r", encoding="utf-8"):
            if "w" in mode:
                m = mock_open()
                return m.return_value
            else:
                return mock_open(read_data=json.dumps({self.symbol: self.random_price})).return_value

        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", side_effect=mock_file_write):
            parser.fetch_and_store(symbol=self.symbol, price=self.random_price)
            data = parser.load_data(self.storage_file)
            self.assertIsInstance(data, dict)

    def test_market_report_generator_symbol_report(self):
        generator = MarketReportGenerator(storage_file=self.storage_file)
        mock_data = {self.symbol: self.random_price}
        
        with patch.object(MarketParser, "load_data", return_value=mock_data):
            report = generator.generate_symbol_report(self.symbol)
            self.assertIn(self.symbol, report)
            self.assertIn(str(self.random_price), report)

    def test_market_report_generator_no_data(self):
        generator = MarketReportGenerator(storage_file=self.storage_file)
        
        with patch.object(MarketParser, "load_data", return_value={}):
            report = generator.generate_symbol_report(self.symbol)
            self.assertIn(self.symbol, report)
            self.assertIn("No data", report)

    def test_market_report_generator_raw_stream_dump(self):
        generator = MarketReportGenerator(storage_file=self.storage_file)
        raw_content = json.dumps({self.symbol: self.random_price})

        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=raw_content)):
            dump = generator.get_raw_stream_dump()
            self.assertEqual(dump, raw_content)

    def test_generate_market_report_function(self):
        with patch("skills.market_portfolio_monitor.MarketReportGenerator.generate_symbol_report", return_value=f"Report {self.symbol}") as mock_gen:
            res = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
            self.assertEqual(res, f"Report {self.symbol}")
            mock_gen.assert_called_once_with(self.symbol)

    def test_run_market_telegram_pipeline(self):
        mock_data = {self.symbol: self.random_price}
        with patch.object(MarketParser, "load_data", return_value=mock_data):
            result = run_market_telegram_pipeline(
                storage_file=self.storage_file,
                symbol=self.symbol,
                chat_id=self.chat_id,
                url=self.url,
                telegram_token=self.telegram_token
            )
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["symbol"], self.symbol)
            self.assertEqual(result["price"], self.random_price)
            self.assertEqual(result["chat_id"], self.chat_id)
            self.assertEqual(result["url"], self.url)

    def test_run_pipeline(self):
        with patch("skills.market_portfolio_monitor.MarketParser.load_data", return_value={self.symbol: self.random_price}), \
             patch("skills.market_portfolio_monitor.MarketParser.fetch_and_store") as mock_fetch, \
             patch("skills.market_portfolio_monitor.MarketReportGenerator.generate_symbol_report"), \
             patch("skills.market_portfolio_monitor.generate_market_report"), \
             patch("skills.market_portfolio_monitor.run_market_telegram_pipeline"):
            
            res = run_pipeline(
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                storage_file=self.storage_file
            )
            self.assertTrue(res)
            mock_fetch.assert_called_once()

    def test_start_new_and_ened_aliases(self):
        with patch("skills.market_portfolio_monitor.run_pipeline", return_value=True) as mock_run:
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
            self.assertEqual(mock_run.call_count, 2)

    def test_export_audit_logs(self):
        valid_json = json.dumps({uuid.uuid4().hex: random.randint(1, 100)})
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=valid_json)):
            self.assertTrue(export_audit_logs(self.storage_file))

        with patch("os.path.exists", return_value=False):
            self.assertFalse(export_audit_logs(self.storage_file))

    def test_market_parser_invalid_json_handling(self):
        corrupted_content = "invalid_json_payload_" + uuid.uuid4().hex
        parser = MarketParser(storage_file=self.storage_file)
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=corrupted_content)):
            data = parser.load_data(self.storage_file)
            self.assertEqual(data, {})

    def test_market_parser_malformed_bracket_handling(self):
        malformed_content = "{" + uuid.uuid4().hex
        parser = MarketParser(storage_file=self.storage_file)
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=malformed_content)):
            data = parser.load_data(self.storage_file)
            self.assertEqual(data, {})


if __name__ == "__main__":
    unittest.main()