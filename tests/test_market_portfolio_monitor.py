import unittest
from unittest.mock import patch, mock_open
import json
import os
import io
import uuid
import random
from skills import db_storage
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
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://{uuid.uuid4().hex[:8]}.com/api"
        self.telegram_token = f"{random.randint(100000,999999)}:AAG{uuid.uuid4().hex[:10]}"
        self.chat_id = str(random.randint(10000000, 99999999))
        self.storage_file = f"storage_{uuid.uuid4().hex[:8]}.json"
        self.price = round(random.uniform(10.0, 1500.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_market_parser_fetch_and_store_success(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)
        
        self.assertTrue(os.path.exists(self.storage_file))
        loaded_data = parser.load_data(self.storage_file)
        self.assertIsInstance(loaded_data, dict)
        self.assertIn(self.symbol, loaded_data)
        self.assertEqual(loaded_data[self.symbol], self.price)

    def test_market_parser_load_data_missing_file(self):
        missing_file = f"missing_{uuid.uuid4().hex}.json"
        parser = MarketParser(storage_file=missing_file)
        data = parser.load_data(missing_file)
        self.assertIsNone(data)

    def test_market_report_generator_symbol_report_exists(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)
        
        gen = MarketReportGenerator(storage_file=self.storage_file)
        report = gen.generate_symbol_report(symbol=self.symbol)
        
        self.assertIn(self.symbol, report)
        self.assertIn(str(self.price), report)

    def test_market_report_generator_symbol_report_no_data(self):
        gen = MarketReportGenerator(storage_file=self.storage_file)
        report = gen.generate_symbol_report(symbol=self.symbol)
        
        self.assertIn(self.symbol, report)
        self.assertIn("No data", report)

    def test_market_report_generator_get_raw_stream_dump(self):
        random_bytes_content = json.dumps({self.symbol: self.price}).encode("utf-8")
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=random_bytes_content.decode("utf-8"))):
            gen = MarketReportGenerator(storage_file=self.storage_file)
            dump = gen.get_raw_stream_dump()
            self.assertIn(self.symbol, dump)
            self.assertIn(str(self.price), dump)

    def test_market_report_generator_get_raw_stream_dump_empty(self):
        with patch("os.path.exists", return_value=False):
            gen = MarketReportGenerator(storage_file=self.storage_file)
            dump = gen.get_raw_stream_dump()
            self.assertEqual(dump, "{}")

    def test_generate_market_report_function(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)
        
        report = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
        self.assertIn(self.symbol, report)
        self.assertIn(str(self.price), report)

    def test_run_market_telegram_pipeline_execution(self):
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
        with patch("skills.market_portfolio_monitor.run_market_telegram_pipeline") as mock_telegram:
            mock_telegram.return_value = {"status": "success"}

            res = run_pipeline(
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                storage_file=self.storage_file
            )

            self.assertTrue(res)
            mock_telegram.assert_called_once()

    def test_start_new_entry_point(self):
        with patch("skills.market_portfolio_monitor.run_pipeline") as mock_run_pipeline:
            mock_run_pipeline.return_value = True

            res = start_new(
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                storage_file=self.storage_file
            )

            self.assertTrue(res)
            mock_run_pipeline.assert_called_once_with(
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                storage_file=self.storage_file
            )

    def test_db_storage_integration_safeguard(self):
        self.assertIsNotNone(db_storage)

if __name__ == "__main__":
    unittest.main()