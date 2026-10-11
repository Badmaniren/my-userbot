import unittest
from unittest.mock import patch
import os
import json
import io
import uuid
import random
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

class TestMarketPortfolioMonitorInquisitor(unittest.TestCase):

    def setUp(self):
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.url = f"https://{uuid.uuid4().hex}.com/api"
        self.telegram_token = f"{random.randint(100000, 999999)}:{uuid.uuid4().hex[:10]}"
        self.chat_id = str(random.randint(1000000, 99999999))
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.price = round(random.uniform(10.0, 1500.0), 2)

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

    def test_market_parser_corrupted_storage(self):
        garbage_content = ''.join(random.choices(string.ascii_letters + string.punctuation, k=25))
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(garbage_content)

        parser = MarketParser(storage_file=self.storage_file)
        loaded_data = parser.load_data(self.storage_file)
        self.assertEqual(loaded_data, {})

        parser.fetch_and_store(symbol=self.symbol, price=self.price)
        reloaded = parser.load_data(self.storage_file)
        self.assertEqual(reloaded.get(self.symbol), self.price)

    def test_market_parser_bytes_stream(self):
        parser = MarketParser(storage_file=None)
        random_bytes = io.BytesIO(json.dumps({self.symbol: self.price}).encode("utf-8"))
        read_result = parser._read_content(random_bytes)
        self.assertIn(self.symbol, read_result)

    def test_market_report_generator_symbol_report(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)

        gen = MarketReportGenerator(storage_file=self.storage_file)
        report = gen.generate_symbol_report(symbol=self.symbol)
        
        self.assertIn(self.symbol, report)
        self.assertIn(str(self.price), report)

    def test_market_report_generator_raw_stream_dump(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)

        gen = MarketReportGenerator(storage_file=self.storage_file)
        dump = gen.get_raw_stream_dump()
        
        self.assertIn(self.symbol, dump)
        self.assertIn(str(self.price), dump)

    def test_generate_market_report_helper(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)

        res = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
        self.assertIn(self.symbol, res)

    def test_run_market_telegram_pipeline(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)

        pipeline_res = run_market_telegram_pipeline(
            storage_file=self.storage_file,
            symbol=self.symbol,
            chat_id=self.chat_id,
            url=self.url,
            telegram_token=self.telegram_token
        )

        self.assertEqual(pipeline_res["status"], "success")
        self.assertEqual(pipeline_res["symbol"], self.symbol)
        self.assertEqual(pipeline_res["price"], self.price)
        self.assertEqual(pipeline_res["chat_id"], self.chat_id)
        self.assertEqual(pipeline_res["url"], self.url)

    def test_export_audit_logs_valid(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)

        exported = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(exported)

    def test_export_audit_logs_invalid(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(uuid.uuid4().hex)

        exported = export_audit_logs(storage_file=self.storage_file)
        self.assertFalse(exported)

    def test_run_pipeline_execution(self):
        res = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res)

    def test_start_new_execution(self):
        res = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res)

    def test_start_ened_execution(self):
        res = start_ened(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res)

if __name__ == '__main__':
    unittest.main()