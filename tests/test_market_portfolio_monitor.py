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
        self.random_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.random_url = f"https://{uuid.uuid4().hex}.com/{uuid.uuid4().hex}"
        self.random_token = uuid.uuid4().hex
        self.random_chat_id = str(random.randint(100000, 999999))
        self.random_storage = f"{uuid.uuid4().hex}.json"

    def tearDown(self):
        if os.path.exists(self.random_storage):
            try:
                os.remove(self.random_storage)
            except OSError:
                pass

    def test_market_parser_read_content_bytes(self):
        parser = MarketParser(self.random_storage)
        random_bytes = uuid.uuid4().bytes
        stream = io.BytesIO(random_bytes)
        content = parser._read_content(stream)
        self.assertIsInstance(content, str)

    def test_market_parser_fetch_and_load(self):
        parser = MarketParser(self.random_storage)
        random_price = round(random.uniform(10.0, 1000.0), 2)
        
        parser.fetch_and_store(symbol=self.random_symbol, price=random_price)
        data = parser.load_data(storage_file=self.random_storage)
        
        self.assertIsInstance(data, dict)
        self.assertIn(self.random_symbol, data)
        self.assertEqual(data[self.random_symbol], random_price)

    def test_market_parser_load_data_invalid_json(self):
        invalid_content = uuid.uuid4().hex + "{"
        with open(self.random_storage, "w", encoding="utf-8") as f:
            f.write(invalid_content)
        
        parser = MarketParser(self.random_storage)
        data = parser.load_data(storage_file=self.random_storage)
        self.assertEqual(data, {})

    def test_market_report_generator_symbol(self):
        parser = MarketParser(self.random_storage)
        random_price = round(random.uniform(1.0, 500.0), 4)
        parser.fetch_and_store(symbol=self.random_symbol, price=random_price)

        report_gen = MarketReportGenerator(storage_file=self.random_storage)
        report = report_gen.generate_symbol_report(symbol=self.random_symbol)
        
        self.assertIn(self.random_symbol, report)
        self.assertIn(str(random_price), report)

    def test_market_report_generator_no_data(self):
        report_gen = MarketReportGenerator(storage_file=self.random_storage)
        report = report_gen.generate_symbol_report(symbol=self.random_symbol)
        self.assertIn("No data", report)

    def test_get_raw_stream_dump(self):
        random_payload = {uuid.uuid4().hex: random.randint(1, 100)}
        with open(self.random_storage, "w", encoding="utf-8") as f:
            json.dump(random_payload, f)

        report_gen = MarketReportGenerator(storage_file=self.random_storage)
        dump = report_gen.get_raw_stream_dump()
        
        parsed_dump = json.loads(dump)
        self.assertEqual(parsed_dump, random_payload)

    def test_generate_market_report_wrapper(self):
        parser = MarketParser(self.random_storage)
        random_price = round(random.uniform(50.0, 500.0), 2)
        parser.fetch_and_store(symbol=self.random_symbol, price=random_price)

        res = generate_market_report(storage_file=self.random_storage, symbol=self.random_symbol)
        self.assertIn(self.random_symbol, res)

    def test_run_market_telegram_pipeline(self):
        parser = MarketParser(self.random_storage)
        random_price = round(random.uniform(0.1, 99.9), 2)
        parser.fetch_and_store(symbol=self.random_symbol, price=random_price)

        result = run_market_telegram_pipeline(
            storage_file=self.random_storage,
            symbol=self.random_symbol,
            chat_id=self.random_chat_id,
            url=self.random_url,
            telegram_token=self.random_token
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["symbol"], self.random_symbol)
        self.assertEqual(result["price"], random_price)
        self.assertEqual(result["chat_id"], self.random_chat_id)
        self.assertEqual(result["url"], self.random_url)

    def test_export_audit_logs_success(self):
        random_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        with open(self.random_storage, "w", encoding="utf-8") as f:
            json.dump(random_data, f)

        res = export_audit_logs(storage_file=self.random_storage)
        self.assertTrue(res)

    def test_export_audit_logs_failure(self):
        with open(self.random_storage, "w", encoding="utf-8") as f:
            f.write(uuid.uuid4().hex + "{unclosed")

        res = export_audit_logs(storage_file=self.random_storage)
        self.assertFalse(res)

    def test_run_pipeline_execution(self):
        with patch("skills.market_portfolio_monitor.run_market_telegram_pipeline") as mock_telegram:
            mock_telegram.return_value = {"status": "success"}
            
            res = run_pipeline(
                symbol=self.random_symbol,
                url=self.random_url,
                telegram_token=self.random_token,
                chat_id=self.random_chat_id,
                storage_file=self.random_storage
            )
            self.assertTrue(res)
            mock_telegram.assert_called_once()

    def test_start_new_execution(self):
        with patch("skills.market_portfolio_monitor.run_pipeline") as mock_run:
            mock_run.return_value = True
            
            res = start_new(
                symbol=self.random_symbol,
                url=self.random_url,
                telegram_token=self.random_token,
                chat_id=self.random_chat_id,
                storage_file=self.random_storage
            )
            self.assertTrue(res)
            mock_run.assert_called_once_with(
                symbol=self.random_symbol,
                url=self.random_url,
                telegram_token=self.random_token,
                chat_id=self.random_chat_id,
                storage_file=self.random_storage
            )

    def test_start_ened_execution(self):
        with patch("skills.market_portfolio_monitor.start_new") as mock_start:
            mock_start.return_value = True
            
            res = start_ened(
                symbol=self.random_symbol,
                url=self.random_url,
                telegram_token=self.random_token,
                chat_id=self.random_chat_id,
                storage_file=self.random_storage
            )
            self.assertTrue(res)
            mock_start.assert_called_once_with(
                symbol=self.random_symbol,
                url=self.random_url,
                telegram_token=self.random_token,
                chat_id=self.random_chat_id,
                storage_file=self.random_storage
            )