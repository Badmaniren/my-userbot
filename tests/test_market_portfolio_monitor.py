import unittest
import os
import json
import uuid
import random
import string
from unittest.mock import patch
from skills.market_portfolio_monitor import (
    MarketParser,
    MarketReportGenerator,
    generate_market_report,
    run_market_telegram_pipeline,
    run_compliance_export,
    export_audit_logs,
    run_pipeline,
    start_new
)

class TestMarketPortfolioMonitor(unittest.TestCase):

    def setUp(self):
        self.random_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.random_url = f"https://{uuid.uuid4().hex}.com/{uuid.uuid4().hex}"
        self.random_token = uuid.uuid4().hex
        self.random_chat_id = str(random.randint(100000, 999999))
        self.random_storage = f"{uuid.uuid4().hex}.json"
        self.random_export_path = f"export_{uuid.uuid4().hex}.log"
        self.random_price = round(random.uniform(1.0, 1000.0), 4)

    def tearDown(self):
        for path in [self.random_storage, self.random_export_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

    def test_market_parser_fetch_and_load(self):
        parser = MarketParser(storage_file=self.random_storage)
        parser.fetch_and_store(symbol=self.random_symbol, price=self.random_price)
        
        self.assertTrue(os.path.exists(self.random_storage))
        
        loaded_data = parser.load_data(self.random_storage)
        self.assertIsInstance(loaded_data, dict)
        self.assertIn(self.random_symbol, loaded_data)
        self.assertEqual(loaded_data[self.random_symbol], self.random_price)

    def test_market_parser_corrupted_json_handling(self):
        with open(self.random_storage, "w", encoding="utf-8") as f:
            f.write("invalid json content")

        parser = MarketParser(storage_file=self.random_storage)
        data = parser.load_data(self.random_storage)
        self.assertIsNone(data)

        # Storing to a corrupted file should reset it safely
        parser.fetch_and_store(symbol=self.random_symbol, price=self.random_price)
        loaded_data = parser.load_data(self.random_storage)
        self.assertEqual(loaded_data, {self.random_symbol: self.random_price})

    def test_market_parser_load_nonexistent(self):
        non_existent_file = f"{uuid.uuid4().hex}.json"
        parser = MarketParser(storage_file=non_existent_file)
        data = parser.load_data(non_existent_file)
        self.assertIsNone(data)

    def test_market_report_generator_symbol_report(self):
        parser = MarketParser(storage_file=self.random_storage)
        parser.fetch_and_store(symbol=self.random_symbol, price=self.random_price)
        
        report_gen = MarketReportGenerator(storage_file=self.random_storage)
        report = report_gen.generate_symbol_report(symbol=self.random_symbol)
        
        self.assertIn(self.random_symbol, report)
        self.assertIn(str(self.random_price), report)

    def test_market_report_generator_no_data(self):
        report_gen = MarketReportGenerator(storage_file=self.random_storage)
        report = report_gen.generate_symbol_report(symbol=self.random_symbol)
        
        self.assertIn(self.random_symbol, report)
        self.assertIn("No data", report)

    def test_market_report_generator_raw_stream_dump(self):
        parser = MarketParser(storage_file=self.random_storage)
        parser.fetch_and_store(symbol=self.random_symbol, price=self.random_price)
        
        report_gen = MarketReportGenerator(storage_file=self.random_storage)
        dump = report_gen.get_raw_stream_dump()
        
        parsed_dump = json.loads(dump)
        self.assertIn(self.random_symbol, parsed_dump)
        self.assertEqual(parsed_dump[self.random_symbol], self.random_price)

    def test_generate_market_report_function(self):
        parser = MarketParser(storage_file=self.random_storage)
        parser.fetch_and_store(symbol=self.random_symbol, price=self.random_price)
        
        report = generate_market_report(storage_file=self.random_storage, symbol=self.random_symbol)
        self.assertIn(self.random_symbol, report)
        self.assertIn(str(self.random_price), report)

    def test_run_market_telegram_pipeline(self):
        parser = MarketParser(storage_file=self.random_storage)
        parser.fetch_and_store(symbol=self.random_symbol, price=self.random_price)
        
        result = run_market_telegram_pipeline(
            storage_file=self.random_storage,
            symbol=self.random_symbol,
            chat_id=self.random_chat_id,
            url=self.random_url,
            telegram_token=self.random_token
        )
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["symbol"], self.random_symbol)
        self.assertEqual(result["price"], self.random_price)
        self.assertEqual(result["chat_id"], self.random_chat_id)
        self.assertEqual(result["url"], self.random_url)

    def test_run_compliance_export(self):
        parser = MarketParser(storage_file=self.random_storage)
        parser.fetch_and_store(symbol=self.random_symbol, price=self.random_price)
        res = run_compliance_export(self.random_export_path, storage_file=self.random_storage)
        self.assertTrue(res)

    def test_export_audit_logs(self):
        parser = MarketParser(storage_file=self.random_storage)
        parser.fetch_and_store(symbol=self.random_symbol, price=self.random_price)
        res = export_audit_logs(self.random_export_path, storage_file=self.random_storage)
        self.assertTrue(res)

    def test_run_pipeline(self):
        success = run_pipeline(
            symbol=self.random_symbol,
            url=self.random_url,
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            storage_file=self.random_storage
        )
        self.assertTrue(success)
        self.assertTrue(os.path.exists(self.random_storage))

    def test_start_new(self):
        success = start_new(
            symbol=self.random_symbol,
            url=self.random_url,
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            storage_file=self.random_storage
        )
        self.assertTrue(success)
        parser = MarketParser(storage_file=self.random_storage)
        data = parser.load_data(self.random_storage)
        self.assertIn(self.random_symbol, data)

if __name__ == "__main__":
    unittest.main()
