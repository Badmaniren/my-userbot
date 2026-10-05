import unittest
from unittest.mock import patch
import os
import json
import uuid
import random
import io
import tempfile

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
        self.temp_dir = tempfile.TemporaryDirectory()
        self.random_filename = os.path.join(self.temp_dir.name, f"{uuid.uuid4().hex}.json")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_market_parser_load_data_valid(self):
        symbol = uuid.uuid4().hex[:6]
        price = round(random.uniform(10.0, 1000.0), 2)
        data = {symbol: price}
        
        with open(self.random_filename, "w", encoding="utf-8") as f:
            json.dump(data, f)

        parser = MarketParser(self.storage_file) if hasattr(self, 'storage_file') else MarketParser(self.random_filename)
        loaded = parser.load_data(self.random_filename)
        
        self.assertIsInstance(loaded, dict)
        self.assertIn(symbol, loaded)
        self.assertEqual(loaded[symbol], price)

    def test_market_parser_load_data_corrupted_json(self):
        garbage = f"{{{uuid.uuid4().hex}: {random.randint(1, 100)}"
        with open(self.random_filename, "w", encoding="utf-8") as f:
            f.write(garbage)

        parser = MarketParser(self.random_filename)
        loaded = parser.load_data(self.random_filename)
        self.assertEqual(loaded, {})

    def test_market_parser_fetch_and_store(self):
        symbol = uuid.uuid4().hex[:8]
        price = round(random.uniform(1.0, 500.0), 4)

        parser = MarketParser(self.random_filename)
        parser.fetch_and_store(symbol, price)

        self.assertTrue(os.path.exists(self.random_filename))
        with open(self.random_filename, "r", encoding="utf-8") as f:
            content = json.load(f)
        
        self.assertIn(symbol, content)
        self.assertEqual(content[symbol], price)

    def test_market_report_generator_symbol_report(self):
        symbol = uuid.uuid4().hex[:5]
        price = round(random.uniform(50.0, 200.0), 2)
        data = {symbol: price}

        with open(self.random_filename, "w", encoding="utf-8") as f:
            json.dump(data, f)

        gen = MarketReportGenerator(storage_file=self.random_filename)
        report = gen.generate_symbol_report(symbol)
        
        self.assertIn(symbol, report)
        self.assertIn(str(price), report)

    def test_market_report_generator_raw_stream_dump(self):
        random_str = uuid.uuid4().hex
        with open(self.random_filename, "w", encoding="utf-8") as f:
            f.write(random_str)

        gen = MarketReportGenerator(storage_file=self.random_filename)
        dump = gen.get_raw_stream_dump()
        self.assertEqual(dump, random_str)

    def test_generate_market_report(self):
        symbol = uuid.uuid4().hex[:6]
        price = round(random.uniform(100.0, 999.0), 2)
        data = {symbol: price}

        with open(self.random_filename, "w", encoding="utf-8") as f:
            json.dump(data, f)

        res = generate_market_report(self.random_filename, symbol)
        self.assertIn(symbol, res)

    def test_run_market_telegram_pipeline(self):
        symbol = uuid.uuid4().hex[:5]
        chat_id = str(random.randint(100000, 999999))
        url = f"https://{uuid.uuid4().hex}.com/api"
        token = uuid.uuid4().hex
        price = round(random.uniform(1.0, 10.0), 2)

        data = {symbol: price}
        with open(self.random_filename, "w", encoding="utf-8") as f:
            json.dump(data, f)

        pipeline_result = run_market_telegram_pipeline(
            storage_file=self.random_filename,
            symbol=symbol,
            chat_id=chat_id,
            url=url,
            telegram_token=token
        )

        self.assertEqual(pipeline_result["status"], "success")
        self.assertEqual(pipeline_result["symbol"], symbol)
        self.assertEqual(pipeline_result["price"], price)
        self.assertEqual(pipeline_result["chat_id"], chat_id)
        self.assertEqual(pipeline_result["url"], url)

    def test_export_audit_logs_valid(self):
        log_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        with open(self.random_filename, "w", encoding="utf-8") as f:
            json.dump(log_data, f)

        exported = export_audit_logs(self.random_filename)
        self.assertTrue(exported)

    def test_export_audit_logs_empty(self):
        with open(self.random_filename, "w", encoding="utf-8") as f:
            f.write("   ")

        exported = export_audit_logs(self.random_filename)
        self.assertFalse(exported)

    def test_run_pipeline(self):
        symbol = uuid.uuid4().hex[:6]
        url = f"https://{uuid.uuid4().hex}.org"
        token = uuid.uuid4().hex
        chat_id = str(random.randint(100, 999))

        result = run_pipeline(
            symbol=symbol,
            url=url,
            telegram_token=token,
            chat_id=chat_id,
            storage_file=self.random_filename
        )
        self.assertTrue(result)

    def test_start_new_and_ened(self):
        symbol = uuid.uuid4().hex[:6]
        url = f"https://{uuid.uuid4().hex}.net"
        token = uuid.uuid4().hex
        chat_id = str(random.randint(1000, 9999))

        res_new = start_new(
            symbol=symbol,
            url=url,
            telegram_token=token,
            chat_id=chat_id,
            storage_file=self.random_filename
        )
        self.assertTrue(res_new)

        res_ened = start_ened(
            symbol=symbol,
            url=url,
            telegram_token=token,
            chat_id=chat_id,
            storage_file=self.random_filename
        )
        self.assertTrue(res_ened)

    def test_parser_with_binary_stream_mock(self):
        binary_content = uuid.uuid4().hex.encode('utf-8')
        mock_file = io.BytesIO(binary_content)

        with patch("builtins.open", return_value=mock_file):
            parser = MarketParser(self.random_filename)
            data = parser.load_data(self.random_filename)
            self.assertEqual(data, {})

if __name__ == "__main__":
    unittest.main()