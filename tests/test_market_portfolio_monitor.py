import unittest
from unittest.mock import patch
import os
import json
import uuid
import random
import io
from skills.market_portfolio_monitor import (
    MarketParser,
    MarketReportGenerator,
    generate_market_report,
    run_market_telegram_pipeline,
    run_pipeline,
    start_new
)

class TestMarketPortfolioMonitor(unittest.TestCase):

    def setUp(self):
        self.symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        self.price = round(random.uniform(10.0, 1500.0), 2)
        self.url = f"https://api.{uuid.uuid4().hex[:8]}.org/v1/send"
        self.telegram_token = f"{random.randint(100000, 999999)}:AA{uuid.uuid4().hex[:20]}"
        self.chat_id = str(random.randint(-999999999, -100000))
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"

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

    def test_market_parser_load_nonexistent(self):
        non_existent_file = f"missing_{uuid.uuid4().hex}.json"
        parser = MarketParser(storage_file=non_existent_file)
        data = parser.load_data(non_existent_file)
        self.assertIsNone(data)

    def test_market_report_generator_symbol_report(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)
        
        reporter = MarketReportGenerator(storage_file=self.storage_file)
        report = reporter.generate_symbol_report(self.symbol)
        
        self.assertIn(self.symbol, report)
        self.assertIn(str(self.price), report)

    def test_market_report_generator_no_data(self):
        reporter = MarketReportGenerator(storage_file=self.storage_file)
        report = reporter.generate_symbol_report(self.symbol)
        
        self.assertIn(self.symbol, report)
        self.assertIn("No data", report)

    def test_market_report_generator_raw_stream_dump(self):
        random_garbage = uuid.uuid4().hex
        mock_file_data = json.dumps({uuid.uuid4().hex: random_garbage})
        
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", return_value=io.StringIO(mock_file_data)):
            reporter = MarketReportGenerator(storage_file=self.storage_file)
            raw_dump = reporter.get_raw_stream_dump()
            self.assertEqual(raw_dump, mock_file_data)

    def test_market_report_generator_raw_stream_dump_missing(self):
        with patch("os.path.exists", return_value=False):
            reporter = MarketReportGenerator(storage_file=self.storage_file)
            raw_dump = reporter.get_raw_stream_dump()
            self.assertEqual(raw_dump, "{}")

    def test_generate_market_report_wrapper(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)
        
        result = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
        self.assertIn(self.symbol, result)
        self.assertIn(str(self.price), result)

    def test_run_market_telegram_pipeline(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)
        
        pipeline_result = run_market_telegram_pipeline(
            storage_file=self.storage_file,
            symbol=self.symbol,
            chat_id=self.chat_id,
            url=self.url,
            telegram_token=self.telegram_token
        )
        
        self.assertIsInstance(pipeline_result, dict)
        self.assertEqual(pipeline_result.get("status"), "success")
        self.assertEqual(pipeline_result.get("symbol"), self.symbol)
        self.assertEqual(pipeline_result.get("price"), self.price)
        self.assertEqual(pipeline_result.get("chat_id"), self.chat_id)
        self.assertEqual(pipeline_result.get("url"), self.url)

    def test_run_pipeline_execution(self):
        result = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(result)

        parser = MarketParser(storage_file=self.storage_file)
        data = parser.load_data(self.storage_file)
        self.assertIn(self.symbol, data)

    def test_start_new_entrypoint(self):
        result = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(result)

        reporter = MarketReportGenerator(storage_file=self.storage_file)
        report = reporter.generate_symbol_report(self.symbol)
        self.assertIn(self.symbol, report)

if __name__ == "__main__":
    unittest.main()