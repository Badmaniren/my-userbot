import unittest
from unittest.mock import patch, mock_open
import os
import json
import uuid
import random
import io
from skills.market_portfolio_monitor import (
    run_pipeline,
    start_new,
    MarketParser,
    MarketReportGenerator,
    generate_market_report,
    run_market_telegram_pipeline
)

class TestMarketPortfolioMonitor(unittest.TestCase):
    def setUp(self):
        self.symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        self.price = round(random.uniform(10.0, 1000.0), 2)
        self.url = f"https://{uuid.uuid4().hex[:8]}.com/api"
        self.telegram_token = f"{random.randint(1000,9999)}:ABC-{uuid.uuid4().hex[:6]}"
        self.chat_id = f"-100{random.randint(100000,999999)}"
        self.storage_file = f"storage_{uuid.uuid4().hex[:8]}.json"

    def test_market_parser_fetch_and_store(self):
        parser = MarketParser(storage_file=self.storage_file)
        random_data_key = f"KEY_{uuid.uuid4().hex[:4]}"
        random_data_val = round(random.uniform(1.0, 500.0), 2)
        
        initial_data = json.dumps({random_data_key: random_data_val})
        
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=initial_data)) as mock_file:

            parser.fetch_and_store(self.symbol, self.price)
            mock_file.assert_called()

    def test_market_parser_load_data_not_exists(self):
        parser = MarketParser(storage_file=self.storage_file)
        with patch("os.path.exists", return_value=False):
            result = parser.load_data(self.storage_file)
            self.assertIsNone(result)

    def test_market_parser_load_data_exists(self):
        parser = MarketParser(storage_file=self.storage_file)
        payload = {self.symbol: self.price}
        payload_str = json.dumps(payload)
        
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=payload_str)):
            res = parser.load_data(self.storage_file)
            self.assertEqual(res.get(self.symbol), self.price)

    def test_market_report_generator_symbol_report(self):
        generator = MarketReportGenerator(storage_file=self.storage_file)
        payload = {self.symbol: self.price}
        
        with patch.object(MarketParser, "load_data", return_value=payload):
            report = generator.generate_symbol_report(self.symbol)
            self.assertIn(self.symbol, report)
            self.assertIn(str(self.price), report)

    def test_market_report_generator_symbol_report_no_data(self):
        generator = MarketReportGenerator(storage_file=self.storage_file)
        
        with patch.object(MarketParser, "load_data", return_value={}):
            report = generator.generate_symbol_report(self.symbol)
            self.assertIn("No data", report)

    def test_market_report_generator_raw_stream_dump(self):
        generator = MarketReportGenerator(storage_file=self.storage_file)
        dump_content = uuid.uuid4().hex
        
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=dump_content)):
            stream = generator.get_raw_stream_dump()
            self.assertEqual(stream, dump_content)

    def test_market_report_generator_raw_stream_dump_empty(self):
        generator = MarketReportGenerator(storage_file=self.storage_file)
        
        with patch("os.path.exists", return_value=False):
            stream = generator.get_raw_stream_dump()
            self.assertEqual(stream, "{}")

    def test_generate_market_report_wrapper(self):
        expected_msg = f"Report for {self.symbol}: {self.price}"
        with patch("skills.market_portfolio_monitor.MarketReportGenerator.generate_symbol_report", return_value=expected_msg) as mock_gen:
            res = generate_market_report(self.storage_file, self.symbol)
            mock_gen.assert_called_once_with(self.symbol)
            self.assertEqual(res, expected_msg)

    def test_run_market_telegram_pipeline(self):
        payload = {self.symbol: self.price}
        with patch.object(MarketParser, "load_data", return_value=payload):
            result = run_market_telegram_pipeline(
                storage_file=self.storage_file,
                symbol=self.symbol,
                chat_id=self.chat_id,
                url=self.url,
                telegram_token=self.telegram_token
            )
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["symbol"], self.symbol)
            self.assertEqual(result["price"], self.price)
            self.assertEqual(result["chat_id"], self.chat_id)
            self.assertEqual(result["url"], self.url)

    def test_run_pipeline(self):
        with patch("skills.market_portfolio_monitor.MarketParser.fetch_and_store") as mock_fetch, \
             patch("skills.market_portfolio_monitor.MarketReportGenerator.generate_symbol_report") as mock_gen_sym, \
             patch("skills.market_portfolio_monitor.generate_market_report") as mock_gen_mkt, \
             patch("skills.market_portfolio_monitor.run_market_telegram_pipeline") as mock_tg:

            success = run_pipeline(
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                storage_file=self.storage_file
            )
            self.assertTrue(success)
            mock_fetch.assert_called_once()
            mock_gen_sym.assert_called_once()
            mock_gen_mkt.assert_called_once()
            mock_tg.assert_called_once()

    def test_start_new(self):
        with patch("skills.market_portfolio_monitor.run_pipeline", return_value=True) as mock_run:
            res = start_new(
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                storage_file=self.storage_file
            )
            self.assertTrue(res)
            mock_run.assert_called_once_with(
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                storage_file=self.storage_file
            )

if __name__ == "__main__":
    unittest.main()