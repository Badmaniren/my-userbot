import unittest
import os
import json
import uuid
import random
import tempfile
import io
from unittest.mock import patch

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
        self.random_storage = f"{uuid.uuid4().hex}.json"
        self.random_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.random_price = round(random.uniform(10.0, 5000.0), 2)
        self.random_url = f"https://{uuid.uuid4().hex[:8]}.com/webhook"
        self.random_token = uuid.uuid4().hex
        self.random_chat_id = str(random.randint(100000, 9999999))

    def tearDown(self):
        if os.path.exists(self.random_storage):
            try:
                os.remove(self.random_storage)
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

    def test_market_parser_load_nonexistent(self):
        nonexistent_file = f"{uuid.uuid4().hex}.json"
        parser = MarketParser(storage_file=nonexistent_file)
        result = parser.load_data(nonexistent_file)
        self.assertIsNone(result)

    def test_market_parser_load_invalid_json(self):
        garbage_content = uuid.uuid4().hex.encode('utf-8')
        with patch('builtins.open', unittest.mock.mock_open(read_data=garbage_content.decode('utf-8'))):
            with patch('os.path.exists', return_value=True):
                parser = MarketParser(storage_file=self.random_storage)
                res = parser.load_data(self.random_storage)
                self.assertIsNone(res)

    def test_market_report_generator_symbol_report(self):
        parser = MarketParser(storage_file=self.random_storage)
        parser.fetch_and_store(symbol=self.random_symbol, price=self.random_price)

        gen = MarketReportGenerator(storage_file=self.random_storage)
        report = gen.generate_symbol_report(symbol=self.random_symbol)
        
        self.assertIn(self.random_symbol, report)
        self.assertIn(str(self.random_price), report)

    def test_market_report_generator_no_data(self):
        gen = MarketReportGenerator(storage_file=self.random_storage)
        report = gen.generate_symbol_report(symbol=self.random_symbol)
        
        self.assertIn(self.random_symbol, report)
        self.assertIn("No data", report)

    def test_market_report_generator_raw_stream_dump(self):
        parser = MarketParser(storage_file=self.random_storage)
        parser.fetch_and_store(symbol=self.random_symbol, price=self.random_price)

        gen = MarketReportGenerator(storage_file=self.random_storage)
        dump = gen.get_raw_stream_dump()
        
        self.assertIsInstance(dump, str)
        parsed_dump = json.loads(dump)
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

        res = run_market_telegram_pipeline(
            storage_file=self.random_storage,
            symbol=self.random_symbol,
            chat_id=self.random_chat_id,
            url=self.random_url,
            telegram_token=self.random_token
        )

        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("status"), "success")
        self.assertEqual(res.get("symbol"), self.random_symbol)
        self.assertEqual(res.get("price"), self.random_price)
        self.assertEqual(res.get("chat_id"), self.random_chat_id)
        self.assertEqual(res.get("url"), self.random_url)

    def test_run_pipeline(self):
        parser = MarketParser(storage_file=self.random_storage)
        parser.fetch_and_store(symbol=self.random_symbol, price=self.random_price)

        status = run_pipeline(
            symbol=self.random_symbol,
            url=self.random_url,
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            storage_file=self.random_storage
        )
        self.assertTrue(status)

    def test_start_new_and_ened_aliases(self):
        parser = MarketParser(storage_file=self.random_storage)
        parser.fetch_and_store(symbol=self.random_symbol, price=self.random_price)

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

    def test_export_audit_logs_valid(self):
        payload = {uuid.uuid4().hex: random.randint(1, 100)}
        with open(self.random_storage, "w", encoding="utf-8") as f:
            json.dump(payload, f)

        res = export_audit_logs(storage_file=self.random_storage)
        self.assertTrue(res)

    def test_export_audit_logs_invalid(self):
        with open(self.random_storage, "w", encoding="utf-8") as f:
            f.write(uuid.uuid4().hex + " invalid json structure {{{")

        res = export_audit_logs(storage_file=self.random_storage)
        self.assertFalse(res)

    def test_export_audit_logs_empty_or_missing(self):
        self.assertFalse(export_audit_logs(storage_file=None))
        self.assertFalse(export_audit_logs(storage_file=f"{uuid.uuid4().hex}.json"))

        with open(self.random_storage, "w", encoding="utf-8") as f:
            f.write("   \n   ")
        self.assertFalse(export_audit_logs(storage_file=self.random_storage))

if __name__ == '__main__':
    unittest.main()