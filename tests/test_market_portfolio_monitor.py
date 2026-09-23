import unittest
import os
import json
import uuid
import random
import io
from unittest.mock import patch
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
        self.storage_file = f"storage_{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://{uuid.uuid4().hex}.com/api"
        self.telegram_token = f"{random.randint(100000, 999999)}:{uuid.uuid4().hex[:16]}"
        self.chat_id = str(random.randint(1000000, 99999999))
        self.price = round(random.uniform(1.0, 1000.0), 4)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_run_pipeline_success(self):
        result = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.storage_file))

    def test_start_new_initialization(self):
        result = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(result)
        parser = MarketParser(storage_file=self.storage_file)
        data = parser.load_data(self.storage_file)
        self.assertIsInstance(data, dict)
        self.assertIn(self.symbol, data)

    def test_market_parser_fetch_and_store(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)
        
        loaded = parser.load_data(self.storage_file)
        self.assertEqual(loaded[self.symbol], self.price)

    def test_market_parser_load_nonexistent_file(self):
        non_existent = f"missing_{uuid.uuid4().hex}.json"
        parser = MarketParser(storage_file=non_existent)
        data = parser.load_data(non_existent)
        self.assertIsNone(data)

    def test_market_parser_handles_corrupted_stream(self):
        corrupted_data = uuid.uuid4().hex
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(corrupted_data)

        parser = MarketParser(storage_file=self.storage_file)
        with self.assertRaises(json.JSONDecodeError):
            parser.load_data(self.storage_file)

    def test_market_report_generator_symbol_report(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)

        generator = MarketReportGenerator(storage_file=self.storage_file)
        report = generator.generate_symbol_report(symbol=self.symbol)
        
        self.assertIn(self.symbol, report)
        self.assertIn(str(self.price), report)

    def test_market_report_generator_no_data(self):
        generator = MarketReportGenerator(storage_file=self.storage_file)
        report = generator.generate_symbol_report(symbol=self.symbol)
        
        self.assertIn(self.symbol, report)
        self.assertIn("No data", report)

    def test_get_raw_stream_dump(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)

        generator = MarketReportGenerator(storage_file=self.storage_file)
        raw_dump = generator.get_raw_stream_dump()
        
        parsed_dump = json.loads(raw_dump)
        self.assertEqual(parsed_dump[self.symbol], self.price)

    def test_generate_market_report_function(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)

        report = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
        self.assertIn(self.symbol, report)
        self.assertIn(str(self.price), report)

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

        self.assertEqual(pipeline_result["status"], "success")
        self.assertEqual(pipeline_result["symbol"], self.symbol)
        self.assertEqual(pipeline_result["price"], self.price)
        self.assertEqual(pipeline_result["chat_id"], self.chat_id)
        self.assertEqual(pipeline_result["url"], self.url)

    def test_parser_with_io_stream_mock(self):
        garbage_bytes = uuid.uuid4().bytes
        mock_stream = io.BytesIO(garbage_bytes)

        with patch("builtins.open", return_value=io.TextIOWrapper(mock_stream, encoding="utf-8")):
            parser = MarketParser(storage_file=self.storage_file)
            with self.assertRaises((json.JSONDecodeError, AttributeError)):
                parser.load_data(self.storage_file)