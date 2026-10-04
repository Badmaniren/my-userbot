import unittest
from unittest.mock import patch
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
    export_audit_logs,
)


class TestMarketPortfolioMonitor(unittest.TestCase):

    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.storage_file = f"test_storage_{self.random_suffix}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://{uuid.uuid4().hex[:6]}.com/api"
        self.telegram_token = uuid.uuid4().hex
        self.chat_id = str(random.randint(100000, 999999))

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_market_parser_load_data_nonexistent(self):
        parser = MarketParser(storage_file=self.storage_file)
        result = parser.load_data(self.storage_file)
        self.assertIsNone(result)

    def test_market_parser_load_data_empty(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("   ")
        parser = MarketParser(storage_file=self.storage_file)
        result = parser.load_data(self.storage_file)
        self.assertEqual(result, {})

    def test_market_parser_load_data_valid(self):
        random_price = round(random.uniform(10.0, 1000.0), 2)
        payload = {self.symbol: random_price}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(payload, f)
        
        parser = MarketParser(storage_file=self.storage_file)
        result = parser.load_data(self.storage_file)
        self.assertIsInstance(result, dict)
        self.assertIn(self.symbol, result)
        self.assertEqual(result[self.symbol], random_price)

    def test_market_parser_load_data_unterminated_json(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write('{"unterminated": true')
        
        parser = MarketParser(storage_file=self.storage_file)
        with self.assertRaises(json.JSONDecodeError):
            parser.load_data(self.storage_file)

    def test_market_parser_fetch_and_store(self):
        random_price = round(random.uniform(1.0, 500.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=random_price)

        self.assertTrue(os.path.exists(self.storage_file))
        data = parser.load_data(self.storage_file)
        self.assertEqual(data[self.symbol], random_price)

    def test_market_report_generator_symbol_report(self):
        random_price = round(random.uniform(50.0, 5000.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=random_price)

        gen = MarketReportGenerator(storage_file=self.storage_file)
        report = gen.generate_symbol_report(symbol=self.symbol)
        self.assertIn(self.symbol, report)
        self.assertIn(str(random_price), report)

    def test_market_report_generator_symbol_report_no_data(self):
        gen = MarketReportGenerator(storage_file=self.storage_file)
        report = gen.generate_symbol_report(symbol=f"ABSENT_{uuid.uuid4().hex[:4]}")
        self.assertIn("No data", report)

    def test_market_report_generator_get_raw_stream_dump(self):
        random_text = uuid.uuid4().hex
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(random_text)

        gen = MarketReportGenerator(storage_file=self.storage_file)
        dump = gen.get_raw_stream_dump()
        self.assertEqual(dump, random_text)

    def test_market_report_generator_get_raw_stream_dump_fallback(self):
        invalid_path = f"nonexistent_{uuid.uuid4().hex}.json"
        gen = MarketReportGenerator(storage_file=invalid_path)
        dump = gen.get_raw_stream_dump()
        self.assertEqual(dump, "{}")

    def test_generate_market_report_helper(self):
        random_price = round(random.uniform(1.0, 100.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=random_price)

        report = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
        self.assertIn(self.symbol, report)

    def test_run_market_telegram_pipeline(self):
        random_price = round(random.uniform(10.0, 500.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=random_price)

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
        payload = {uuid.uuid4().hex: random.randint(1, 100)}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(payload, f)

        self.assertTrue(export_audit_logs(storage_file=self.storage_file))

    def test_export_audit_logs_invalid(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("{invalid json")

        self.assertFalse(export_audit_logs(storage_file=self.storage_file))

    def test_export_audit_logs_nonexistent(self):
        self.assertFalse(export_audit_logs(storage_file=f"missing_{uuid.uuid4().hex}.json"))

    def test_run_pipeline(self):
        random_price = round(random.uniform(100.0, 999.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=random_price)

        res = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res)

    def test_start_new_and_ened_aliases(self):
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

    def test_stream_bytes_io_mocking(self):
        random_bytes_content = json.dumps({self.symbol: random.randint(1, 500)}).encode("utf-8")
        mock_file = io.BytesIO(random_bytes_content)

        with patch("builtins.open", return_value=io.StringIO(mock_file.read().decode("utf-8"))):
            parser = MarketParser(storage_file=self.storage_file)
            data = parser.load_data(self.storage_file)
            self.assertIn(self.symbol, data)


if __name__ == "__main__":
    unittest.main()