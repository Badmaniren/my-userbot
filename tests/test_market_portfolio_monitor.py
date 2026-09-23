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
    generate_market_report,
    run_market_telegram_pipeline,
    run_pipeline,
    start_new
)

class TestMarketPortfolioMonitor(unittest.TestCase):

    def setUp(self):
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.price = round(random.uniform(10.0, 1000.0), 2)
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.chat_id = str(random.randint(100000, 999999))
        self.url = f"https://{uuid.uuid4().hex[:8]}.com/api"
        self.telegram_token = f"{random.randint(1000,9999)}:ABC-{uuid.uuid4().hex[:6]}"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_market_parser_fetch_and_store(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)
        
        self.assertTrue(os.path.exists(self.storage_file))
        with open(self.storage_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        self.assertIn(self.symbol, data)
        self.assertEqual(data[self.symbol], self.price)

    def test_market_parser_load_data_nonexistent(self):
        non_existent_file = f"{uuid.uuid4().hex}.json"
        parser = MarketParser(storage_file=non_existent_file)
        result = parser.load_data(non_existent_file)
        self.assertIsNone(result)

    def test_market_parser_load_data_existing(self):
        initial_data = {self.symbol: self.price}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        parser = MarketParser(storage_file=self.storage_file)
        loaded = parser.load_data(self.storage_file)
        self.assertEqual(loaded, initial_data)

    def test_market_report_generator_symbol_report(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)

        generator = MarketReportGenerator(storage_file=self.storage_file)
        report = generator.generate_symbol_report(symbol=self.symbol)
        
        self.assertIn(self.symbol, report)
        self.assertIn(str(self.price), report)

    def test_market_report_generator_symbol_report_no_data(self):
        generator = MarketReportGenerator(storage_file=self.storage_file)
        report = generator.generate_symbol_report(symbol=self.symbol)
        
        self.assertIn(self.symbol, report)
        self.assertIn("No data", report)

    def test_market_report_generator_raw_stream_dump(self):
        random_garbage = uuid.uuid4().hex.encode('utf-8')
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=random_garbage.decode('utf-8'))):
                generator = MarketReportGenerator(storage_file=self.storage_file)
                dump = generator.get_raw_stream_dump()
                self.assertEqual(dump, random_garbage.decode('utf-8'))

    def test_market_report_generator_raw_stream_dump_io_bytes(self):
        random_bytes = os.urandom(32)
        mock_file = io.BytesIO(random_bytes)
        
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", return_value=mock_file):
                generator = MarketReportGenerator(storage_file=self.storage_file)
                dump = generator.get_raw_stream_dump()
                self.assertIsInstance(dump, str)

    def test_generate_market_report(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)

        report = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
        self.assertIn(self.symbol, report)
        self.assertIn(str(self.price), report)

    def test_run_market_telegram_pipeline(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)

        result = run_market_telegram_pipeline(
            storage_file=self.storage_file,
            symbol=self.symbol,
            chat_id=self.chat_id,
            url=self.url,
            telegram_token=self.telegram_token
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["symbol"], self.symbol)
        self.assertEqual(result["price"], self.price)
        self.assertEqual(result["chat_id"], self.chat_id)
        self.assertEqual(result["url"], self.url)

    def test_run_pipeline(self):
        res = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res)
        self.assertTrue(os.path.exists(self.storage_file))

    def test_start_new(self):
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