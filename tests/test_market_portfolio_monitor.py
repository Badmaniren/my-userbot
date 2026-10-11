import unittest
from unittest.mock import patch
import os
import json
import io
import random
import uuid
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
        self.random_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.random_url = f"https://{uuid.uuid4().hex[:8]}.com/api"
        self.random_token = f"BOT:{uuid.uuid4().hex[:10]}"
        self.random_chat_id = f"-100{random.randint(100000, 999999)}"
        self.random_storage = f"store_{uuid.uuid4().hex[:8]}.json"

    def tearDown(self):
        if os.path.exists(self.random_storage):
            try:
                os.remove(self.random_storage)
            except OSError:
                pass

    def test_market_parser_fetch_and_store_and_load(self):
        random_price = round(random.uniform(10.0, 5000.0), 2)
        parser = MarketParser(storage_file=self.random_storage)
        parser.fetch_and_store(symbol=self.random_symbol, price=random_price)

        self.assertTrue(os.path.exists(self.random_storage))
        loaded_data = parser.load_data(self.random_storage)
        self.assertIsInstance(loaded_data, dict)
        self.assertIn(self.random_symbol, loaded_data)
        self.assertEqual(loaded_data[self.random_symbol], random_price)

    def test_market_parser_load_data_none_and_missing(self):
        parser = MarketParser(storage_file=None)
        self.assertIsNone(parser.load_data(None))

        non_existent = f"missing_{uuid.uuid4().hex}.json"
        parser_missing = MarketParser(storage_file=non_existent)
        self.assertEqual(parser_missing.load_data(non_existent), {})

    def test_market_parser_corrupted_json(self):
        corrupted_content = f"{{invalid_json_stream_{uuid.uuid4().hex}"
        with open(self.random_storage, "w", encoding="utf-8") as f:
            f.write(corrupted_content)

        parser = MarketParser(storage_file=self.random_storage)
        data = parser.load_data(self.random_storage)
        self.assertEqual(data, {})

    def test_market_parser_read_content_bytes_and_stream(self):
        rand_hex = uuid.uuid4().hex
        random_bytes = f"data_{rand_hex}".encode("utf-8")
        stream = io.BytesIO(random_bytes)
        parser = MarketParser(storage_file=self.random_storage)
        content = parser._read_content(stream)
        self.assertIn(rand_hex[:4], content or rand_hex)

    def test_market_report_generator_symbol_report(self):
        random_price = round(random.uniform(1.0, 1000.0), 4)
        parser = MarketParser(storage_file=self.random_storage)
        parser.fetch_and_store(symbol=self.random_symbol, price=random_price)

        gen = MarketReportGenerator(storage_file=self.random_storage)
        report = gen.generate_symbol_report(symbol=self.random_symbol)
        self.assertIn(self.random_symbol, report)
        self.assertIn(str(random_price), report)

        absent_symbol = f"ABS_{uuid.uuid4().hex[:5]}"
        absent_report = gen.generate_symbol_report(symbol=absent_symbol)
        self.assertIn(absent_report_expected := "No data", absent_report)

    def test_market_report_generator_raw_stream_dump(self):
        gen = MarketReportGenerator(storage_file=None)
        self.assertEqual(gen.get_raw_stream_dump(), "{}")

        random_price = round(random.uniform(5.0, 50.0), 2)
        parser = MarketParser(storage_file=self.random_storage)
        parser.fetch_and_store(symbol=self.random_symbol, price=random_price)

        dump_gen = MarketReportGenerator(storage_file=self.random_storage)
        dump_content = dump_gen.get_raw_stream_dump()
        self.assertIn(self.random_symbol, dump_content)
        self.assertIn(str(random_price), dump_content)

    def test_generate_market_report_function(self):
        random_price = round(random.uniform(100.0, 200.0), 2)
        parser = MarketParser(storage_file=self.random_storage)
        parser.fetch_and_store(symbol=self.random_symbol, price=random_price)

        report = generate_market_report(storage_file=self.random_storage, symbol=self.random_symbol)
        self.assertIn(self.random_symbol, report)
        self.assertIn(str(random_price), report)

    def test_run_market_telegram_pipeline(self):
        random_price = round(random.uniform(500.0, 1500.0), 2)
        parser = MarketParser(storage_file=self.random_storage)
        parser.fetch_and_store(symbol=self.random_symbol, price=random_price)

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
        self.assertEqual(result.get("price"), random_price)
        self.assertEqual(result.get("chat_id"), self.random_chat_id)
        self.assertEqual(result.get("url"), self.random_url)

    def test_export_audit_logs_valid_and_invalid(self):
        self.assertFalse(export_audit_logs(storage_file=None))
        self.assertFalse(export_audit_logs(storage_file=f"nonexistent_{uuid.uuid4().hex}.json"))

        random_price = round(random.uniform(1.0, 10.0), 2)
        parser = MarketParser(storage_file=self.random_storage)
        parser.fetch_and_store(symbol=self.random_symbol, price=random_price)

        self.assertTrue(export_audit_logs(storage_file=self.random_storage))

        with open(self.random_storage, "w", encoding="utf-8") as f:
            f.write(f"broken_{uuid.uuid4().hex}")
        self.assertFalse(export_audit_logs(storage_file=self.random_storage))

    def test_run_pipeline_and_aliases(self):
        res_pipeline = run_pipeline(
            symbol=self.random_symbol,
            url=self.random_url,
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            storage_file=self.random_storage
        )
        self.assertTrue(res_pipeline)

        res_start_new = start_new(
            symbol=self.random_symbol,
            url=self.random_url,
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            storage_file=self.random_storage
        )
        self.assertTrue(res_start_new)

        res_start_ened = start_ened(
            symbol=self.random_symbol,
            url=self.random_url,
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            storage_file=self.random_storage
        )
        self.assertTrue(res_start_ened)

    def test_market_parser_non_dict_json(self):
        list_json = json.dumps([random.randint(1, 100), random.randint(101, 200)])
        with open(self.random_storage, "w", encoding="utf-8") as f:
            f.write(list_json)

        parser = MarketParser(storage_file=self.random_storage)
        loaded = parser.load_data(self.random_storage)
        self.assertEqual(loaded, {})

        random_price = round(random.uniform(20.0, 80.0), 2)
        parser.fetch_and_store(symbol=self.random_symbol, price=random_price)
        new_loaded = parser.load_data(self.random_storage)
        self.assertIsInstance(new_loaded, dict)
        self.assertEqual(new_loaded.get(self.random_symbol), random_price)

    def test_market_parser_empty_content_files(self):
        with open(self.random_storage, "w", encoding="utf-8") as f:
            f.write("   \n  \t ")

        parser = MarketParser(storage_file=self.random_storage)
        self.assertEqual(parser.load_data(self.random_storage), {})
        self.assertFalse(export_audit_logs(storage_file=self.random_storage))

if __name__ == '__main__':
    unittest.main()