import unittest
from unittest.mock import patch
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
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.storage_file = f"test_store_{uuid.uuid4().hex}.json"
        self.url = f"https://api.{uuid.uuid4().hex[:8]}.com/v1"
        self.telegram_token = f"{random.randint(100000,999999)}:{uuid.uuid4().hex[:16]}"
        self.chat_id = f"@{uuid.uuid4().hex[:8]}"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_market_parser_fetch_and_store(self):
        parser = MarketParser(storage_file=self.storage_file)
        random_price = round(random.uniform(10.0, 5000.0), 2)
        parser.fetch_and_store(symbol=self.symbol, price=random_price)

        self.assertTrue(os.path.exists(self.storage_file))
        data = parser.load_data(self.storage_file)
        self.assertIsInstance(data, dict)
        self.assertIn(self.symbol, data)
        self.assertEqual(data[self.symbol], random_price)

    def test_market_parser_load_empty_or_missing(self):
        parser = MarketParser(storage_file=self.storage_file)
        self.assertIsNone(parser.load_data(self.storage_file))

        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("   ")
        
        data = parser.load_data(self.storage_file)
        self.assertEqual(data, {})

    def test_market_parser_invalid_json(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(f"INVALID_JSON_{uuid.uuid4().hex}")
        
        parser = MarketParser(storage_file=self.storage_file)
        random_price = round(random.uniform(1.0, 100.0), 2)
        parser.fetch_and_store(symbol=self.symbol, price=random_price)

        data = parser.load_data(self.storage_file)
        self.assertEqual(data.get(self.symbol), random_price)

    def test_market_report_generator_symbol_report(self):
        random_price = round(random.uniform(50.0, 1500.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=random_price)

        gen = MarketReportGenerator(storage_file=self.storage_file)
        report = gen.generate_symbol_report(self.symbol)
        self.assertIn(self.symbol, report)
        self.assertIn(str(random_price), report)

        missing_symbol = f"MISS_{uuid.uuid4().hex[:4]}"
        missing_report = gen.generate_symbol_report(missing_symbol)
        self.assertIn("No data", missing_report)

    def test_market_report_generator_raw_stream_dump(self):
        gen = MarketReportGenerator(storage_file=self.storage_file)
        dump_empty = gen.get_raw_stream_dump()
        self.assertEqual(dump_empty, "{}")

        random_price = round(random.uniform(1.0, 500.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=random_price)

        dump_filled = gen.get_raw_stream_dump()
        self.assertIn(self.symbol, dump_filled)
        self.assertIn(str(random_price), dump_filled)

    def test_generate_market_report_helper(self):
        random_price = round(random.uniform(200.0, 800.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=random_price)

        report = generate_market_report(self.storage_file, self.symbol)
        self.assertIn(self.symbol, report)
        self.assertIn(str(random_price), report)

    def test_run_market_telegram_pipeline(self):
        random_price = round(random.uniform(1000.0, 9999.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=random_price)

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
        self.assertEqual(result.get("price"), random_price)
        self.assertEqual(result.get("chat_id"), self.chat_id)
        self.assertEqual(result.get("url"), self.url)

    def test_run_pipeline_execution(self):
        random_price = round(random.uniform(10.0, 500.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=random_price)

        success = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(success)

    def test_start_new_entrypoint(self):
        random_price = round(random.uniform(100.0, 4000.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=random_price)

        success = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(success)

    def test_stream_dump_with_bytes_io_mock(self):
        dummy_bytes = json.dumps({self.symbol: 123.45}).encode("utf-8")
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", return_value=io.BytesIO(dummy_bytes) if hasattr(io, 'BytesIO') else io.StringIO(dummy_bytes.decode("utf-8"))):
            gen = MarketReportGenerator(storage_file=self.storage_file)
            stream_content = gen.get_raw_stream_dump()
            self.assertIn(self.symbol, stream_content)