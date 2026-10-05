import unittest
from unittest.mock import patch, mock_open
import os
import json
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
        self.random_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.random_url = f"https://{uuid.uuid4().hex[:8]}.com/api"
        self.random_token = uuid.uuid4().hex
        self.random_chat_id = str(random.randint(100000, 999999))
        self.random_storage = f"storage_{uuid.uuid4().hex[:8]}.json"
        self.random_price = round(random.uniform(10.0, 1500.0), 2)

    def test_market_parser_load_data_valid(self):
        test_data = {self.random_symbol: self.random_price}
        serialized = json.dumps(test_data)
        
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=serialized)):
            
            parser = MarketParser(storage_file=self.random_storage)
            result = parser.load_data(self.random_storage)
            
            self.assertIsInstance(result, dict)
            self.assertIn(self.random_symbol, result)
            self.assertEqual(result[self.random_symbol], self.random_price)

    def test_market_parser_load_data_corrupted_json(self):
        corrupted_content = "{" + uuid.uuid4().hex + ":" + uuid.uuid4().hex
        
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=corrupted_content)):
            
            parser = MarketParser(storage_file=self.random_storage)
            result = parser.load_data(self.random_storage)
            
            self.assertEqual(result, {})

    def test_market_parser_load_data_bytes_content(self):
        test_data = {self.random_symbol: self.random_price}
        byte_stream = io.BytesIO(json.dumps(test_data).encode("utf-8"))
        
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", return_value=byte_stream):
            
            parser = MarketParser(storage_file=self.random_storage)
            result = parser.load_data(self.random_storage)
            
            self.assertIsInstance(result, dict)
            self.assertEqual(result.get(self.random_symbol), self.random_price)

    def test_market_parser_fetch_and_store(self):
        initial_data = {uuid.uuid4().hex[:5]: round(random.uniform(1.0, 100.0), 2)}
        m_open = mock_open(read_data=json.dumps(initial_data))
        
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", m_open):
            
            parser = MarketParser(storage_file=self.random_storage)
            parser.fetch_and_store(symbol=self.random_symbol, price=self.random_price)
            
            m_open.assert_called()

    def test_market_report_generator_symbol_report(self):
        test_data = {self.random_symbol: self.random_price}
        
        with patch.object(MarketParser, "load_data", return_value=test_data):
            generator = MarketReportGenerator(storage_file=self.random_storage)
            report = generator.generate_symbol_report(symbol=self.random_symbol)
            
            self.assertIn(self.random_symbol, report)
            self.assertIn(str(self.random_price), report)

    def test_market_report_generator_raw_stream_dump(self):
        random_string_dump = uuid.uuid4().hex + "".join(random.choices(string.ascii_letters, k=10))
        
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=random_string_dump)):
            
            generator = MarketReportGenerator(storage_file=self.random_storage)
            dump = generator.get_raw_stream_dump()
            
            self.assertEqual(dump, random_string_dump)

    def test_generate_market_report(self):
        test_data = {self.random_symbol: self.random_price}
        
        with patch.object(MarketParser, "load_data", return_value=test_data):
            report = generate_market_report(storage_file=self.random_storage, symbol=self.random_symbol)
            
            self.assertIn(self.random_symbol, report)

    def test_run_market_telegram_pipeline(self):
        test_data = {self.random_symbol: self.random_price}
        
        with patch.object(MarketParser, "load_data", return_value=test_data):
            response = run_market_telegram_pipeline(
                storage_file=self.random_storage,
                symbol=self.random_symbol,
                chat_id=self.random_chat_id,
                url=self.random_url,
                telegram_token=self.random_token
            )
            
            self.assertIsInstance(response, dict)
            self.assertEqual(response["status"], "success")
            self.assertEqual(response["symbol"], self.random_symbol)
            self.assertEqual(response["price"], self.random_price)
            self.assertEqual(response["chat_id"], self.random_chat_id)
            self.assertEqual(response["url"], self.random_url)

    def test_export_audit_logs_valid_dict(self):
        test_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        serialized = json.dumps(test_data)
        
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=serialized)):
            
            result = export_audit_logs(storage_file=self.random_storage)
            self.assertTrue(result)

    def test_export_audit_logs_empty(self):
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data="   ")):
            
            result = export_audit_logs(storage_file=self.random_storage)
            self.assertFalse(result)

    def test_run_pipeline(self):
        test_data = {self.random_symbol: self.random_price}
        
        with patch.object(MarketParser, "load_data", return_value=test_data), \
             patch.object(MarketParser, "fetch_and_store", return_value=None), \
             patch("skills.market_portfolio_monitor.run_market_telegram_pipeline", return_value={"status": "success"}):
            
            success = run_pipeline(
                symbol=self.random_symbol,
                url=self.random_url,
                telegram_token=self.random_token,
                chat_id=self.random_chat_id,
                storage_file=self.random_storage
            )
            
            self.assertTrue(success)

    def test_start_new_and_ened_aliases(self):
        with patch("skills.market_portfolio_monitor.run_pipeline", return_value=True) as mock_run:
            res_new = start_new(
                symbol=self.random_symbol,
                url=self.random_url,
                telegram_token=self.random_token,
                chat_id=self.random_chat_id,
                storage_file=self.random_storage
            )
            res_ened = start_ened(
                symbol=self.random_symbol,
                url=self.random_url,
                telegram_token=self.random_token,
                chat_id=self.random_chat_id,
                storage_file=self.random_storage
            )
            
            self.assertTrue(res_new)
            self.assertTrue(res_ened)
            self.assertEqual(mock_run.call_count, 2)

if __name__ == "__main__":
    unittest.main()