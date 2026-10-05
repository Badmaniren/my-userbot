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
        self.random_symbol = ''.join(random.choices(string.ascii_uppercase, k=5)) + uuid.uuid4().hex[:4]
        self.random_url = f"https://{uuid.uuid4().hex[:8]}.com/{uuid.uuid4().hex[:6]}"
        self.random_token = uuid.uuid4().hex
        self.random_chat_id = str(random.randint(100000, 99999999))
        self.random_storage = f"{uuid.uuid4().hex}.json"

    def tearDown(self):
        if os.path.exists(self.random_storage):
            try:
                os.remove(self.random_storage)
            except OSError:
                pass

    def test_market_parser_load_and_store_random_data(self):
        random_price = round(random.uniform(10.0, 5000.0), 2)
        parser = MarketParser(storage_file=self.random_storage)
        parser.fetch_and_store(symbol=self.random_symbol, price=random_price)
        
        loaded_data = parser.load_data(self.random_storage)
        self.assertIsInstance(loaded_data, dict)
        self.assertIn(self.random_symbol, loaded_data)
        self.assertEqual(loaded_data[self.random_symbol], random_price)

    def test_market_parser_load_nonexistent_file(self):
        non_existent = f"{uuid.uuid4().hex}.json"
        parser = MarketParser(storage_file=non_existent)
        res = parser.load_data(non_existent)
        self.assertEqual(res, {})

    def test_market_parser_read_content_edge_cases(self):
        parser = MarketParser(storage_file=self.random_storage)
        garbage_bytes = io.BytesIO(uuid.uuid4().bytes)
        read_res = parser._read_content(garbage_bytes)
        self.assertIsInstance(read_res, str)

        broken_json_content = "{invalid_json_stream"
        with open(self.random_storage, "w", encoding="utf-8") as f:
            f.write(broken_json_content)
        
        loaded = parser.load_data(self.random_storage)
        self.assertEqual(loaded, {})

    def test_market_report_generator_symbol_report(self):
        random_price = round(random.uniform(1.0, 999.0), 2)
        parser = MarketParser(storage_file=self.random_storage)
        parser.fetch_and_store(symbol=self.random_symbol, price=random_price)

        generator = MarketReportGenerator(storage_file=self.random_storage)
        report = generator.generate_symbol_report(symbol=self.random_symbol)
        self.assertIn(self.random_symbol, report)
        self.assertIn(str(random_price), report)

        missing_symbol = uuid.uuid4().hex[:6]
        missing_report = generator.generate_symbol_report(symbol=missing_symbol)
        self.assertIn("No data", missing_report)

    def test_market_report_generator_raw_stream_dump(self):
        generator = MarketReportGenerator(storage_file=None)
        self.assertEqual(generator.get_raw_stream_dump(), "{}")

        random_price = round(random.uniform(100.0, 200.0), 2)
        parser = MarketParser(storage_file=self.random_storage)
        parser.fetch_and_store(symbol=self.random_symbol, price=random_price)

        generator_active = MarketReportGenerator(storage_file=self.random_storage)
        dump_content = generator_active.get_raw_stream_dump()
        self.assertIn(self.random_symbol, dump_content)
        self.assertIn(str(random_price), dump_content)

    def test_generate_market_report_function(self):
        random_price = round(random.uniform(5.0, 50.0), 2)
        parser = MarketParser(storage_file=self.random_storage)
        parser.fetch_and_store(symbol=self.random_symbol, price=random_price)

        rep = generate_market_report(storage_file=self.random_storage, symbol=self.random_symbol)
        self.assertIn(self.random_symbol, rep)

    def test_run_market_telegram_pipeline(self):
        random_price = round(random.uniform(1000.0, 2000.0), 2)
        parser = MarketParser(storage_file=self.random_storage)
        parser.fetch_and_store(symbol=self.random_symbol, price=random_price)

        pipeline_result = run_market_telegram_pipeline(
            storage_file=self.random_storage,
            symbol=self.random_symbol,
            chat_id=self.random_chat_id,
            url=self.random_url,
            telegram_token=self.random_token
        )

        self.assertEqual(pipeline_result["status"], "success")
        self.assertEqual(pipeline_result["symbol"], self.random_symbol)
        self.assertEqual(pipeline_result["price"], random_price)
        self.assertEqual(pipeline_result["chat_id"], self.random_chat_id)
        self.assertEqual(pipeline_result["url"], self.random_url)

    def test_export_audit_logs(self):
        self.assertFalse(export_audit_logs(storage_file=None))
        non_existent = f"{uuid.uuid4().hex}.json"
        self.assertFalse(export_audit_logs(storage_file=non_existent))

        with open(self.random_storage, "w", encoding="utf-8") as f:
            f.write("   ")
        self.assertFalse(export_audit_logs(storage_file=self.random_storage))

        with open(self.random_storage, "w", encoding="utf-8") as f:
            f.write("{partial_json")
        self.assertTrue(export_audit_logs(storage_file=self.random_storage))

        valid_data = {self.random_symbol: random.randint(1, 100)}
        with open(self.random_storage, "w", encoding="utf-8") as f:
            json.dump(valid_data, f)
        self.assertTrue(export_audit_logs(storage_file=self.random_storage))

    def test_run_pipeline_execution(self):
        random_price = round(random.uniform(10.0, 99.0), 2)
        parser = MarketParser(storage_file=self.random_storage)
        parser.fetch_and_store(symbol=self.random_symbol, price=random_price)

        pipeline_res = run_pipeline(
            symbol=self.random_symbol,
            url=self.random_url,
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            storage_file=self.random_storage
        )
        self.assertTrue(pipeline_res)

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

    def test_market_parser_non_dict_json_recovery(self):
        with open(self.random_storage, "w", encoding="utf-8") as f:
            json.dump([1, 2, 3], f)

        parser = MarketParser(storage_file=self.random_storage)
        loaded = parser.load_data(self.random_storage)
        self.assertEqual(loaded, {})

        random_price = round(random.uniform(50.0, 100.0), 2)
        parser.fetch_and_symbol_price = parser.fetch_and_store(symbol=self.random_symbol, price=random_price)
        final_loaded = parser.load_data(self.random_storage)
        self.assertIn(self.random_symbol, final_loaded)
        self.assertEqual(final_loaded[self.random_symbol], random_price)