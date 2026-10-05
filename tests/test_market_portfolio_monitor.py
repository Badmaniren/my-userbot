import unittest
import unittest.mock
import json
import os
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
        self.random_symbol = uuid.uuid4().hex[:8].upper()
        self.random_price = round(random.uniform(1.0, 1000.0), 2)
        self.random_chat_id = str(random.randint(100000, 999999))
        self.random_url = f"https://{uuid.uuid4().hex[:6]}.com/api"
        self.random_token = uuid.uuid4().hex
        self.random_storage = f"test_storage_{uuid.uuid4().hex}.json"

    def tearDown(self):
        if os.path.exists(self.random_storage):
            try:
                os.remove(self.random_storage)
            except OSError:
                pass

    def test_market_parser_fetch_and_store_new_file(self):
        parser = MarketParser(storage_file=self.random_storage)
        parser.fetch_and_store(symbol=self.random_symbol, price=self.random_price)

        self.assertTrue(os.path.exists(self.random_storage))
        with open(self.random_storage, "r", encoding="utf-8") as f:
            content = json.load(f)
        
        self.assertIn(self.random_symbol, content)
        self.assertEqual(content[self.random_symbol], self.random_price)

    def test_market_parser_load_data_valid(self):
        initial_data = {self.random_symbol: self.random_price}
        with open(self.random_storage, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        parser = MarketParser(storage_file=self.random_storage)
        loaded = parser.load_data(storage_file=self.random_storage)

        self.assertIsInstance(loaded, dict)
        self.assertEqual(loaded.get(self.random_symbol), self.random_price)

    def test_market_parser_load_data_corrupted_json(self):
        corrupted_content = "{" + uuid.uuid4().hex
        with open(self.random_storage, "w", encoding="utf-8") as f:
            f.write(corrupted_content)

        parser = MarketParser(storage_file=self.random_storage)
        loaded = parser.load_data(storage_file=self.random_storage)

        self.assertEqual(loaded, {})

    def test_market_parser_load_data_none_storage(self):
        parser = MarketParser(storage_file=None)
        loaded = parser.load_data(storage_file=None)
        self.assertIsNone(loaded)

    def test_market_report_generator_symbol_report(self):
        initial_data = {self.random_symbol: self.random_price}
        with open(self.random_storage, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        generator = MarketReportGenerator(storage_file=self.random_storage)
        report = generator.generate_symbol_report(symbol=self.random_symbol)

        self.assertIn(self.random_symbol, report)
        self.assertIn(str(self.random_price), report)

    def test_market_report_generator_symbol_report_no_data(self):
        generator = MarketReportGenerator(storage_file=self.random_storage)
        report = generator.generate_symbol_report(symbol=self.random_symbol)

        self.assertIn(self.random_symbol, report)
        self.assertIn("No data", report)

    def test_market_report_generator_get_raw_stream_dump(self):
        random_text = uuid.uuid4().hex
        with open(self.random_storage, "w", encoding="utf-8") as f:
            f.write(random_text)

        generator = MarketReportGenerator(storage_file=self.random_storage)
        dump = generator.get_raw_stream_dump()

        self.assertEqual(dump, random_text)

    def test_market_report_generator_get_raw_stream_dump_none(self):
        generator = MarketReportGenerator(storage_file=None)
        dump = generator.get_raw_stream_dump()
        self.assertEqual(dump, "{}")

    def test_generate_market_report_function(self):
        initial_data = {self.random_symbol: self.random_price}
        with open(self.random_storage, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        res = generate_market_report(storage_file=self.random_storage, symbol=self.random_symbol)
        self.assertIn(self.random_symbol, res)

    def test_run_market_telegram_pipeline(self):
        initial_data = {self.random_symbol: self.random_price}
        with open(self.random_storage, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        result = run_market_telegram_pipeline(
            storage_file=self.random_storage,
            symbol=self.random_symbol,
            chat_id=self.random_chat_id,
            url=self.random_url,
            telegram_token=self.random_token
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("symbol"), self.random_symbol)
        self.assertEqual(result.get("price"), self.random_price)
        self.assertEqual(result.get("chat_id"), self.random_chat_id)
        self.assertEqual(result.get("url"), self.random_url)

    def test_run_pipeline_execution(self):
        success = run_pipeline(
            symbol=self.random_symbol,
            url=self.random_url,
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            storage_file=self.random_storage
        )
        self.assertTrue(success)
        self.assertTrue(os.path.exists(self.random_storage))

    def test_start_new_and_ened_aliases(self):
        res_new = start_new(
            symbol=self.random_symbol,
            url=self.random_url,
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            storage_file=self.random_storage
        )
        self.assertTrue(res_new)

        res_ened = start_ened(
            symbol=self.random_symbol,
            url=self.random_url,
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            storage_file=self.random_storage
        )
        self.assertTrue(res_ened)

    def test_export_audit_logs_valid_json(self):
        initial_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        with open(self.random_storage, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        res = export_audit_logs(storage_file=self.random_storage)
        self.assertTrue(res)

    def test_export_audit_logs_empty(self):
        with open(self.random_storage, "w", encoding="utf-8") as f:
            f.write("   ")

        res = export_audit_logs(storage_file=self.random_storage)
        self.assertFalse(res)

    def test_market_parser_bytes_stream_mocking(self):
        random_bytes = json.dumps({self.random_symbol: self.random_price}).encode("utf-8")
        mock_file_obj = io.BytesIO(random_bytes)

        with unittest.mock.patch("builtins.open", return_value=mock_file_obj):
            parser = MarketParser(storage_file=self.random_storage)
            loaded = parser.load_data(storage_file=self.random_storage)
            self.assertIsInstance(loaded, dict)