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
    start_ened,
    MarketParser,
    MarketReportGenerator,
    generate_market_report,
    run_market_telegram_pipeline,
    export_audit_logs
)

class TestMarketPortfolioMonitor(unittest.TestCase):

    def setUp(self):
        self.symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        self.url = f"https://api.{uuid.uuid4().hex[:6]}.com/v1"
        self.telegram_token = f"BOT:{uuid.uuid4().hex[:10]}"
        self.chat_id = f"-{random.randint(100000, 999999)}"
        self.storage_file = f"storage_{uuid.uuid4().hex[:8]}.json"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_market_parser_read_content_bytes(self):
        random_bytes = uuid.uuid4().bytes
        stream = io.BytesIO(random_bytes)
        parser = MarketParser(self.storage_file)
        content = parser._read_content(stream)
        self.assertIsInstance(content, str)

    def test_market_parser_read_content_invalid_unicode(self):
        bad_bytes = b'\xff\xfe\x99\x88'
        stream = io.BytesIO(bad_bytes)
        parser = MarketParser(self.storage_file)
        content = parser._read_content(stream)
        self.assertIsInstance(content, str)

    def test_market_parser_fetch_and_store_and_load(self):
        random_price = round(random.uniform(1.0, 1000.0), 4)
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, random_price)
        
        loaded_data = parser.load_data(self.storage_file)
        self.assertIsInstance(loaded_data, dict)
        self.assertIn(self.symbol, loaded_data)
        self.assertEqual(loaded_data[self.symbol], random_price)

    def test_market_parser_load_data_none(self):
        parser = MarketParser(self.storage_file)
        res = parser.load_data(None)
        self.assertIsNone(res)

    def test_market_parser_load_data_nonexistent(self):
        fake_path = f"missing_{uuid.uuid4().hex}.json"
        parser = MarketParser(fake_path)
        res = parser.load_data(fake_path)
        self.assertEqual(res, {})

    def test_market_parser_load_data_malformed_json(self):
        corrupted_content = f"{{invalid_json_{uuid.uuid4().hex}"
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(corrupted_content)
        parser = MarketParser(self.storage_file)
        res = parser.load_data(self.storage_file)
        self.assertEqual(res, {})

    def test_market_parser_load_data_non_dict_json(self):
        list_json = json.dumps([random.randint(1, 100), random.randint(101, 200)])
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(list_json)
        parser = MarketParser(self.storage_file)
        res = parser.load_data(self.storage_file)
        self.assertEqual(res, {})

    def test_market_report_generator_symbol_report(self):
        random_price = round(random.uniform(10.0, 500.0), 2)
        data = {self.symbol: random_price}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(data, f)
        
        gen = MarketReportGenerator(self.storage_file)
        report = gen.generate_symbol_report(self.symbol)
        self.assertIn(self.symbol, report)
        self.assertIn(str(random_price), report)

    def test_market_report_generator_symbol_report_no_data(self):
        gen = MarketReportGenerator(self.storage_file)
        report = gen.generate_symbol_report(self.symbol)
        self.assertIn(self.symbol, report)
        self.assertIn("No data", report)

    def test_market_report_generator_get_raw_stream_dump(self):
        gen = MarketReportGenerator(None)
        self.assertEqual(gen.get_raw_stream_dump(), "{}")

        random_text = uuid.uuid4().hex
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(random_text)
        
        gen_valid = MarketReportGenerator(self.storage_file)
        self.assertEqual(gen_valid.get_raw_stream_dump(), random_text)

    def test_generate_market_report_wrapper(self):
        random_price = round(random.uniform(1.0, 50.0), 2)
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, random_price)
        
        res = generate_market_report(self.storage_file, self.symbol)
        self.assertIn(self.symbol, res)

    def test_run_market_telegram_pipeline(self):
        random_price = round(random.uniform(50.0, 100.0), 2)
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, random_price)

        res = run_market_telegram_pipeline(
            storage_file=self.storage_file,
            symbol=self.symbol,
            chat_id=self.chat_id,
            url=self.url,
            telegram_token=self.telegram_token
        )
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["symbol"], self.symbol)
        self.assertEqual(res["price"], random_price)
        self.assertEqual(res["chat_id"], self.chat_id)
        self.assertEqual(res["url"], self.url)

    def test_export_audit_logs_valid(self):
        valid_data = {uuid.uuid4().hex: random.randint(1, 1000)}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(valid_data, f)
        
        self.assertTrue(export_audit_logs(self.storage_file))

    def test_export_audit_logs_invalid(self):
        self.assertFalse(export_audit_logs(None))
        self.assertFalse(export_audit_logs(f"fake_{uuid.uuid4().hex}.json"))

        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("")
        self.assertFalse(export_audit_logs(self.storage_file))

        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(f"{{broken_{uuid.uuid4().hex}")
        self.assertFalse(export_audit_logs(self.storage_file))

        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump([1, 2, 3], f)
        self.assertFalse(export_audit_logs(self.storage_file))

    def test_run_pipeline(self):
        random_price = round(random.uniform(200.0, 300.0), 2)
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, random_price)

        with patch("skills.market_portfolio_monitor.run_market_telegram_pipeline") as mock_telegram:
            mock_telegram.return_value = {"status": "mocked"}
            result = run_pipeline(
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                storage_file=self.storage_file
            )
            self.assertTrue(result)
            mock_telegram.assert_called_once()

    def test_start_new(self):
        with patch("skills.market_portfolio_monitor.run_pipeline") as mock_run:
            mock_run.return_value = True
            res = start_new(
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                storage_file=self.storage_file
            )
            self.assertTrue(res)
            mock_run.assert_called_once()

    def test_start_ened(self):
        with patch("skills.market_portfolio_monitor.start_new") as mock_start:
            mock_start.return_value = True
            res = start_ened(
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                storage_file=self.storage_file
            )
            self.assertTrue(res)
            mock_start.assert_called_once()

if __name__ == '__main__':
    unittest.main()