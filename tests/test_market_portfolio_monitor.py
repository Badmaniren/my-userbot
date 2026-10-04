import unittest
from unittest.mock import patch, mock_open
import json
import os
import io
import random
import uuid
import string

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
        self.random_symbol = "".join(random.choices(string.ascii_uppercase, k=5)) + "_" + uuid.uuid4().hex[:6]
        self.random_url = f"https://{uuid.uuid4().hex[:8]}.com/{uuid.uuid4().hex[:4]}"
        self.random_token = uuid.uuid4().hex
        self.random_chat_id = str(random.randint(100000, 99999999))
        self.random_file = f"{uuid.uuid4().hex}.json"
        self.random_price = round(random.uniform(10.0, 5000.0), 2)

    def test_market_parser_load_data_valid(self):
        payload = {self.random_symbol: self.random_price}
        json_content = json.dumps(payload)
        
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=json_content)):
            
            parser = MarketParser(storage_file=self.random_file)
            loaded = parser.load_data(self.random_file)
            
            self.assertIsInstance(loaded, dict)
            self.assertIn(self.random_symbol, loaded)
            self.assertEqual(loaded[self.random_symbol], self.random_price)

    def test_market_parser_load_data_corrupted_json(self):
        corrupted_data = "{" + uuid.uuid4().hex  # Некорректный JSON

        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=corrupted_data)):
            
            parser = MarketParser(storage_file=self.random_file)
            loaded = parser.load_data(self.random_file)
            
            self.assertEqual(loaded, {})

    def test_market_parser_load_data_non_existent(self):
        with patch("os.path.exists", return_value=False):
            parser = MarketParser(storage_file=self.random_file)
            loaded = parser.load_data(self.random_file)
            
            self.assertIsNone(loaded)

    def test_market_parser_fetch_and_store(self):
        initial_data = {uuid.uuid4().hex[:4]: round(random.uniform(1.0, 100.0), 2)}
        json_content = json.dumps(initial_data)

        mock_file = mock_open(read_data=json_content)
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_file):
            
            parser = MarketParser(storage_file=self.random_file)
            parser.fetch_and_store(symbol=self.random_symbol, price=self.random_price)
            
            mock_file.assert_called()
            handle = mock_file()
            written_data = "".join(call.args[0] for call in handle.write.mock_calls)
            parsed_written = json.loads(written_data)
            
            self.assertIn(self.random_symbol, parsed_written)
            self.assertEqual(parsed_written[self.random_symbol], self.random_price)

    def test_market_report_generator_symbol_report(self):
        payload = {self.random_symbol: self.random_price}
        
        with patch.object(MarketParser, "load_data", return_value=payload):
            reporter = MarketReportGenerator(storage_file=self.random_file)
            report = reporter.generate_symbol_report(symbol=self.random_symbol)
            
            self.assertIn(self.random_symbol, report)
            self.assertIn(str(self.random_price), report)

    def test_market_report_generator_symbol_report_missing(self):
        other_symbol = "XYZ_" + uuid.uuid4().hex[:4]
        payload = {other_symbol: self.random_price}
        
        with patch.object(MarketParser, "load_data", return_value=payload):
            reporter = MarketReportGenerator(storage_file=self.random_file)
            report = reporter.generate_symbol_report(symbol=self.random_symbol)
            
            self.assertIn(self.random_symbol, report)
            self.assertIn("No data", report)

    def test_market_report_generator_get_raw_stream_dump(self):
        raw_stream_data = json.dumps({uuid.uuid4().hex: random.randint(1, 100)})

        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=raw_stream_data)):
            
            reporter = MarketReportGenerator(storage_file=self.random_file)
            dump = reporter.get_raw_stream_dump()
            
            self.assertEqual(dump, raw_stream_data)

    def test_generate_market_report(self):
        payload = {self.random_symbol: self.random_price}
        with patch.object(MarketParser, "load_data", return_value=payload):
            res = generate_market_report(storage_file=self.random_file, symbol=self.random_symbol)
            self.assertIn(self.random_symbol, res)
            self.assertIn(str(self.random_price), res)

    def test_run_market_telegram_pipeline(self):
        payload = {self.random_symbol: self.random_price}
        with patch.object(MarketParser, "load_data", return_value=payload):
            result = run_market_telegram_pipeline(
                storage_file=self.random_file,
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

    def test_export_audit_logs_valid(self):
        payload = {uuid.uuid4().hex: random.randint(1, 50)}
        json_content = json.dumps(payload)

        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=json_content)):
            
            res = export_audit_logs(storage_file=self.random_file)
            self.assertTrue(res)

    def test_export_audit_logs_empty(self):
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data="   ")):
            
            res = export_audit_logs(storage_file=self.random_file)
            self.assertFalse(res)

    def test_run_pipeline_orchestration(self):
        payload = {self.random_symbol: self.random_price}
        
        with patch.object(MarketParser, "load_data", return_value=payload), \
             patch.object(MarketParser, "fetch_and_store") as mock_fetch, \
             patch("skills.market_portfolio_monitor.generate_market_report") as mock_gen_market, \
             patch("skills.market_portfolio_monitor.run_market_telegram_pipeline") as mock_tg:
            
            success = run_pipeline(
                symbol=self.random_symbol,
                url=self.random_url,
                telegram_token=self.random_token,
                chat_id=self.random_chat_id,
                storage_file=self.random_file
            )
            
            self.assertTrue(success)
            mock_fetch.assert_called_once()
            mock_gen_market.assert_called_once()
            mock_tg.assert_called_once()

    def test_start_new_and_start_ened_aliases(self):
        payload = {self.random_symbol: self.random_price}
        
        with patch.object(MarketParser, "load_data", return_value=payload), \
             patch.object(MarketParser, "fetch_and_store"), \
             patch("skills.market_portfolio_monitor.generate_market_report"), \
             patch("skills.market_portfolio_monitor.run_market_telegram_pipeline"):
            
            res_new = start_new(
                symbol=self.random_symbol,
                url=self.random_url,
                telegram_token=self.random_token,
                chat_id=self.random_chat_id,
                storage_file=self.random_file
            )
            
            res_ened = start_ened(
                symbol=self.random_symbol,
                url=self.random_url,
                telegram_token=self.random_token,
                chat_id=self.random_chat_id,
                storage_file=self.random_file
            )
            
            self.assertTrue(res_new)
            self.assertTrue(res_ened)


if __name__ == "__main__":
    unittest.main()