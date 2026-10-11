import unittest
from unittest.mock import patch
import json
import os
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
        self.random_symbol = ''.join(random.choices(string.ascii_uppercase, k=5)) + "_" + uuid.uuid4().hex[:6]
        self.random_url = "https://" + uuid.uuid4().hex[:8] + ".com/" + uuid.uuid4().hex[:6]
        self.random_token = uuid.uuid4().hex + ":" + uuid.uuid4().hex[:10]
        self.random_chat_id = str(random.randint(100000, 99999999))
        self.random_storage = f"test_storage_{uuid.uuid4().hex[:8]}.json"
        self.random_price = round(random.uniform(10.0, 5000.0), 4)

    def tearDown(self):
        if os.path.exists(self.random_storage):
            try:
                os.remove(self.random_storage)
            except OSError:
                pass

    def test_market_parser_fetch_and_load(self):
        parser = MarketParser(storage_file=self.random_storage)
        parser.fetch_and_store(symbol=self.random_symbol, price=self.random_price)
        
        loaded_data = parser.load_data(self.random_storage)
        self.assertIsInstance(loaded_data, dict)
        self.assertIn(self.random_symbol, loaded_data)
        self.assertEqual(loaded_data[self.random_symbol], self.random_price)

    def test_market_parser_corrupted_json(self):
        garbage_content = io.BytesIO(uuid.uuid4().bytes + b"{invalid_json")
        with patch("builtins.open", return_value=garbage_content):
            parser = MarketParser(storage_file=self.random_storage)
            data = parser.load_data(self.random_storage)
            self.assertEqual(data, {})

    def test_market_report_generator_symbol(self):
        parser = MarketParser(storage_file=self.random_storage)
        parser.fetch_and_store(symbol=self.random_symbol, price=self.random_price)
        
        gen = MarketReportGenerator(storage_file=self.random_storage)
        report = gen.generate_symbol_report(symbol=self.random_symbol)
        self.assertIn(self.random_symbol, report)
        self.assertIn(str(self.random_price), report)

    def test_market_report_generator_no_data(self):
        missing_symbol = uuid.uuid4().hex[:6]
        gen = MarketReportGenerator(storage_file=self.random_storage)
        report = gen.generate_symbol_report(symbol=missing_symbol)
        self.assertIn(missing_symbol, report)
        self.assertIn("No data", report)

    def test_get_raw_stream_dump(self):
        parser = MarketParser(storage_file=self.random_storage)
        parser.fetch_and_store(symbol=self.random_symbol, price=self.random_price)
        
        gen = MarketReportGenerator(storage_file=self.random_storage)
        dump = gen.get_raw_stream_dump()
        self.assertIn(self.random_symbol, dump)
        self.assertIn(str(self.random_price), dump)

    def test_generate_market_report_wrapper(self):
        parser = MarketParser(storage_file=self.random_storage)
        parser.fetch_and_store(symbol=self.random_symbol, price=self.random_price)
        
        res = generate_market_report(storage_file=self.random_storage, symbol=self.random_symbol)
        self.assertIn(self.random_symbol, res)

    def test_run_market_telegram_pipeline(self):
        parser = MarketParser(storage_file=self.random_storage)
        parser.fetch_and_store(symbol=self.random_symbol, price=self.random_price)
        
        pipeline_res = run_market_telegram_pipeline(
            storage_file=self.random_storage,
            symbol=self.random_symbol,
            chat_id=self.random_chat_id,
            url=self.random_url,
            telegram_token=self.random_token
        )
        self.assertEqual(pipeline_res["status"], "success")
        self.assertEqual(pipeline_res["symbol"], self.random_symbol)
        self.assertEqual(pipeline_res["price"], self.random_price)
        self.assertEqual(pipeline_res["chat_id"], self.random_chat_id)
        self.assertEqual(pipeline_res["url"], self.random_url)

    def test_run_pipeline_execution(self):
        result = run_pipeline(
            symbol=self.random_symbol,
            url=self.random_url,
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            storage_file=self.random_storage
        )
        self.assertTrue(result)
        parser = MarketParser(storage_file=self.random_storage)
        data = parser.load_data(storage_file=self.random_storage)
        self.assertIn(self.random_symbol, data)

    def test_start_new_and_ened_aliases(self):
        res_new = start_new(
            symbol=self.random_symbol,
            url=self.random_url,
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            storage_file=self.random_storage
        )
        self.assertTrue(res_new)

        random_symbol_2 = uuid.uuid4().hex[:8]
        res_ened = start_ened(
            symbol=random_symbol_2,
            url=self.random_url,
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            storage_file=self.random_storage
        )
        self.assertTrue(res_ened)

    def test_export_audit_logs_valid(self):
        parser = MarketParser(storage_file=self.random_storage)
        parser.fetch_and_store(symbol=self.random_symbol, price=self.random_price)
        
        audit_res = export_audit_logs(storage_file=self.random_storage)
        self.assertTrue(audit_res)

    def test_export_audit_logs_invalid(self):
        invalid_storage = f"invalid_{uuid.uuid4().hex[:8]}.json"
        with open(invalid_storage, "w", encoding="utf-8") as f:
            f.write(uuid.uuid4().hex + "broken_json")
        try:
            audit_res = export_audit_logs(storage_file=invalid_storage)
            self.assertFalse(audit_res)
        finally:
            if os.path.exists(invalid_storage):
                os.remove(invalid_storage)

if __name__ == '__main__':
    unittest.main()