import unittest
from unittest.mock import patch
import os
import io
import json
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
        self.random_symbol = ''.join(random.choices(string.ascii_uppercase, k=5)) + "_" + uuid.uuid4().hex[:6]
        self.random_url = f"https://{uuid.uuid4().hex[:8]}.com/{uuid.uuid4().hex[:6]}"
        self.random_token = uuid.uuid4().hex
        self.random_chat_id = str(random.randint(100000, 9999999))
        self.random_storage_file = f"test_store_{uuid.uuid4().hex[:8]}.json"

    def tearDown(self):
        if os.path.exists(self.random_storage_file):
            try:
                os.remove(self.random_storage_file)
            except OSError:
                pass

    def test_market_parser_fetch_and_load(self):
        parser = MarketParser(self.random_storage_file)
        test_price = round(random.uniform(10.0, 5000.0), 4)

        parser.fetch_and_store(self.random_symbol, test_price)
        self.assertTrue(os.path.exists(self.random_storage_file))

        loaded_data = parser.load_data(self.random_storage_file)
        self.assertIsInstance(loaded_data, dict)
        self.assertIn(self.random_symbol, loaded_data)
        self.assertEqual(loaded_data[self.random_symbol], test_price)

    def test_market_parser_invalid_json_handling(self):
        invalid_content = "{" + uuid.uuid4().hex
        with open(self.random_storage_file, "w", encoding="utf-8") as f:
            f.write(invalid_content)

        parser = MarketParser(self.random_storage_file)
        loaded_data = parser.load_data(self.random_storage_file)
        self.assertEqual(loaded_data, {})

    def test_market_parser_read_content_stream(self):
        parser = MarketParser(self.random_storage_file)
        random_bytes = uuid.uuid4().bytes
        stream = io.BytesIO(random_bytes)
        
        read_result = parser._read_content(stream)
        self.assertIsInstance(read_result, str)

    def test_market_report_generator_symbol(self):
        parser = MarketParser(self.random_storage_file)
        test_price = round(random.uniform(1.0, 100.0), 2)
        parser.fetch_and_store(self.random_symbol, test_price)

        report_gen = MarketReportGenerator(self.random_storage_file)
        report = report_gen.generate_symbol_report(self.random_symbol)
        
        self.assertIn(self.random_symbol, report)
        self.assertIn(str(test_price), report)

    def test_market_report_generator_raw_stream(self):
        parser = MarketParser(self.random_storage_file)
        test_price = round(random.uniform(100.0, 200.0), 2)
        parser.fetch_and_store(self.random_symbol, test_price)

        report_gen = MarketReportGenerator(self.random_storage_file)
        raw_dump = report_gen.get_raw_stream_dump()
        
        self.assertIn(self.random_symbol, raw_dump)
        self.assertIn(str(test_price), raw_dump)

    def test_generate_market_report_function(self):
        parser = MarketParser(self.random_storage_file)
        test_price = round(random.uniform(5.0, 50.0), 2)
        parser.fetch_and_store(self.random_symbol, test_price)

        res = generate_market_report(self.random_storage_file, self.random_symbol)
        self.assertIn(self.random_symbol, res)

    def test_run_market_telegram_pipeline(self):
        parser = MarketParser(self.random_storage_file)
        test_price = round(random.uniform(1000.0, 9999.0), 2)
        parser.fetch_and_store(self.random_symbol, test_price)

        result = run_market_telegram_pipeline(
            storage_file=self.random_storage_file,
            symbol=self.random_symbol,
            chat_id=self.random_chat_id,
            url=self.random_url,
            telegram_token=self.random_token
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("symbol"), self.random_symbol)
        self.assertEqual(result.get("price"), test_price)
        self.assertEqual(result.get("chat_id"), self.random_chat_id)
        self.assertEqual(result.get("url"), self.random_url)

    def test_export_audit_logs_valid(self):
        parser = MarketParser(self.random_storage_file)
        parser.fetch_and_store(self.random_symbol, round(random.uniform(1.0, 10.0), 2))

        export_res = export_audit_logs(self.random_storage_file)
        self.assertTrue(export_res)

    def test_export_audit_logs_invalid(self):
        with open(self.random_storage_file, "w", encoding="utf-8") as f:
            f.write(uuid.uuid4().hex + "unclosed_json")

        export_res = export_audit_logs(self.random_storage_file)
        self.assertFalse(export_res)

    def test_run_pipeline_execution(self):
        parser = MarketParser(self.random_storage_file)
        initial_price = round(random.uniform(50.0, 500.0), 2)
        parser.fetch_and_store(self.random_symbol, initial_price)

        pipeline_result = run_pipeline(
            symbol=self.random_symbol,
            url=self.random_url,
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            storage_file=self.random_storage_file
        )
        self.assertTrue(pipeline_result)

    def test_start_new_and_ened_aliases(self):
        parser = MarketParser(self.random_storage_file)
        initial_price = round(random.uniform(10.0, 100.0), 2)
        parser.fetch_and_store(self.random_symbol, initial_price)

        res_new = start_new(
            symbol=self.random_symbol,
            url=self.random_url,
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            storage_file=self.random_storage_file
        )
        self.assertTrue(res_new)

        res_ened = start_ened(
            symbol=self.random_symbol,
            url=self.random_url,
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            storage_file=self.random_storage_file
        )
        self.assertTrue(res_ened)

if __name__ == '__main__':
    unittest.main()