import unittest
from unittest.mock import patch, mock_open
import os
import json
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
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://{uuid.uuid4().hex[:8]}.com/api"
        self.telegram_token = f"{random.randint(1000, 9999)}:{uuid.uuid4().hex[:10]}"
        self.chat_id = f"@{uuid.uuid4().hex[:6]}"
        self.storage_file = f"storage_{uuid.uuid4().hex[:8]}.json"
        self.price = round(random.uniform(10.0, 5000.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_market_parser_fetch_and_load(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)
        
        loaded_data = parser.load_data(self.storage_file)
        self.assertIsInstance(loaded_data, dict)
        self.assertIn(self.symbol, loaded_data)
        self.assertEqual(loaded_data[self.symbol], self.price)

    def test_market_parser_load_nonexistent_file(self):
        non_existent = f"missing_{uuid.uuid4().hex}.json"
        parser = MarketParser(storage_file=non_existent)
        data = parser.load_data(non_existent)
        self.assertIsNone(data)

    def test_market_parser_corrupted_json(self):
        junk_data = uuid.uuid4().hex
        with patch("builtins.open", mock_open(read_data=junk_data)):
            parser = MarketParser(storage_file=self.storage_file)
            data = parser.load_data(self.storage_file)
            self.assertIsNone(data)

    def test_market_report_generator_symbol_report(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)

        report_gen = MarketReportGenerator(storage_file=self.storage_file)
        report = report_gen.generate_symbol_report(symbol=self.symbol)
        
        self.assertIn(self.symbol, report)
        self.assertIn(str(self.price), report)

    def test_market_report_generator_no_data(self):
        other_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        report_gen = MarketReportGenerator(storage_file=self.storage_file)
        report = report_gen.generate_symbol_report(symbol=other_symbol)
        
        self.assertIn(other_symbol, report)
        self.assertIn("No data", report)

    def test_market_report_generator_raw_stream_dump(self):
        dump_content = json.dumps({self.symbol: self.price})
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=dump_content)):
                report_gen = MarketReportGenerator(storage_file=self.storage_file)
                raw_dump = report_gen.get_raw_stream_dump()
                self.assertEqual(raw_dump, dump_content)

    def test_generate_market_report_function(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)
        
        report = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
        self.assertIn(self.symbol, report)
        self.assertIn(str(self.price), report)

    def test_run_market_telegram_pipeline(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)

        res = run_market_telegram_pipeline(
            storage_file=self.storage_file,
            symbol=self.symbol,
            chat_id=self.chat_id,
            url=self.url,
            telegram_token=self.telegram_token
        )

        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("status"), "success")
        self.assertEqual(res.get("symbol"), self.symbol)
        self.assertEqual(res.get("price"), self.price)
        self.assertEqual(res.get("chat_id"), self.chat_id)
        self.assertEqual(res.get("url"), self.url)

    def test_run_pipeline_execution(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)

        result = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(result)

    def test_start_new_and_ened_aliases(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)

        res_new = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res_new)

        res_ened = start_ened(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res_ened)

    def test_export_audit_logs_valid(self):
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=uuid.uuid4().hex)):
                self.assertTrue(export_audit_logs(storage_file=self.storage_file))

    def test_export_audit_logs_empty(self):
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data="   ")):
                self.assertFalse(export_audit_logs(storage_file=self.storage_file))

    def test_export_audit_logs_nonexistent(self):
        self.assertFalse(export_audit_logs(storage_file=None))
        self.assertFalse(export_audit_logs(storage_file=uuid.uuid4().hex))


if __name__ == "__main__":
    unittest.main()