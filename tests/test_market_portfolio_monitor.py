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
    MarketParser,
    MarketReportGenerator,
    generate_market_report,
    run_market_telegram_pipeline
)

class TestMarketPortfolioMonitor(unittest.TestCase):

    def setUp(self):
        self.symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.url = f"https://api.{uuid.uuid4().hex[:8]}.com/v1"
        self.telegram_token = f"{random.randint(1000, 9999)}:AA{uuid.uuid4().hex[:20]}"
        self.chat_id = str(random.randint(100000, 999999))
        self.price = round(random.uniform(10.0, 1000.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_market_parser_fetch_and_load(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)
        
        self.assertTrue(os.path.exists(self.storage_file))
        loaded_data = parser.load_data(self.storage_file)
        self.assertIsInstance(loaded_data, dict)
        self.assertIn(self.symbol, loaded_data)
        self.assertEqual(loaded_data[self.symbol], self.price)

    def test_market_parser_load_non_existent(self):
        non_existent_file = f"{uuid.uuid4().hex}.json"
        parser = MarketParser(storage_file=non_existent_file)
        data = parser.load_data(non_existent_file)
        self.assertIsNone(data)

    def test_market_report_generator_symbol_report(self):
        initial_data = {self.symbol: self.price}
        mock_data_json = json.dumps(initial_data)

        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=mock_data_json)):

            gen = MarketReportGenerator(storage_file=self.storage_file)
            report = gen.generate_symbol_report(symbol=self.symbol)
            self.assertIn(self.symbol, report)
            self.assertIn(str(self.price), report)

    def test_market_report_generator_no_data(self):
        other_symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        initial_data = {other_symbol: self.price}
        mock_data_json = json.dumps(initial_data)

        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=mock_data_json)):

            gen = MarketReportGenerator(storage_file=self.storage_file)
            report = gen.generate_symbol_report(symbol=self.symbol)
            self.assertIn(self.symbol, report)
            self.assertIn("No data", report)

    def test_get_raw_stream_dump(self):
        raw_stream_content = f"{uuid.uuid4().hex}:{random.randint(1, 100)}"
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=raw_stream_content)):

            gen = MarketReportGenerator(storage_file=self.storage_file)
            dump = gen.get_raw_stream_dump()
            self.assertEqual(dump, raw_stream_content)

    def test_get_raw_stream_dump_io_fallback(self):
        stream_mock = io.BytesIO(uuid.uuid4().bytes)
        with patch("os.path.exists", return_value=False):
            gen = MarketReportGenerator(storage_file=self.storage_file)
            dump = gen.get_raw_stream_dump()
            self.assertEqual(dump, "{}")

    def test_generate_market_report_helper(self):
        initial_data = {self.symbol: self.price}
        mock_data_json = json.dumps(initial_data)

        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=mock_data_json)):

            report = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
            self.assertIn(self.symbol, report)
            self.assertIn(str(self.price), report)

    def test_run_market_telegram_pipeline(self):
        initial_data = {self.symbol: self.price}
        mock_data_json = json.dumps(initial_data)

        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=mock_data_json)):

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

    def test_run_pipeline(self):
        initial_data = {self.symbol: 0.0}
        mock_data_json = json.dumps(initial_data)

        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=mock_data_json)) as mocked_file:

            res = run_pipeline(
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                storage_file=self.storage_file
            )
            self.assertTrue(res)
            mocked_file.assert_called()

    def test_start_new(self):
        initial_data = {self.symbol: 0.0}
        mock_data_json = json.dumps(initial_data)

        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=mock_data_json)):

            res = start_new(
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                storage_file=self.storage_file
            )
            self.assertTrue(res)

if __name__ == "__main__":
    unittest.main()