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
        self.random_prefix = uuid.uuid4().hex[:8]
        self.storage_file = f"temp_storage_{self.random_prefix}_{random.randint(1000, 9999)}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://{uuid.uuid4().hex[:8]}.org/api/{random.randint(1, 100)}"
        self.telegram_token = f"{random.randint(100000, 999999)}:AA{uuid.uuid4().hex[:20]}"
        self.chat_id = f"-{random.randint(100000000, 999999999)}"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_market_parser_load_and_store_random_data(self):
        random_price = round(random.uniform(10.0, 10000.0), 4)
        parser = MarketParser(storage_file=self.storage_file)
        
        parser.fetch_and_store(symbol=self.symbol, price=random_price)
        self.assertTrue(os.path.exists(self.storage_file))

        loaded_data = parser.load_data(storage_file=self.storage_file)
        self.assertIsInstance(loaded_data, dict)
        self.assertIn(self.symbol, loaded_data)
        self.assertEqual(loaded_data[self.symbol], random_price)

    def test_market_parser_load_empty_file(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("")
        
        parser = MarketParser(storage_file=self.storage_file)
        data = parser.load_data(storage_file=self.storage_file)
        self.assertEqual(data, {})

    def test_market_parser_unterminated_json_raises_error(self):
        corrupted_content = '{"' + uuid.uuid4().hex + '": ' + str(random.randint(1, 100))
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(corrupted_content)

        parser = MarketParser(storage_file=self.storage_file)
        with self.assertRaises(json.JSONDecodeError):
            parser.load_data(storage_file=self.storage_file)

        with self.assertRaises(json.JSONDecodeError):
            parser.fetch_and_store(symbol=self.symbol, price=random.random())

    def test_market_report_generator_with_and_without_data(self):
        generator = MarketReportGenerator(storage_file=self.storage_file)
        
        no_data_report = generator.generate_symbol_report(symbol=self.symbol)
        self.assertIn("No data", no_data_report)
        self.assertIn(self.symbol, no_data_report)

        random_price = round(random.uniform(1.0, 500.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=random_price)

        report = generator.generate_symbol_report(symbol=self.symbol)
        self.assertIn(str(random_price), report)
        self.assertIn(self.symbol, report)

        raw_dump = generator.get_raw_stream_dump()
        self.assertIn(self.symbol, raw_dump)

    def test_generate_market_report_wrapper(self):
        random_price = round(random.uniform(50.0, 5000.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=random_price)

        report = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
        self.assertIn(self.symbol, report)
        self.assertIn(str(random_price), report)

    def test_run_market_telegram_pipeline(self):
        random_price = round(random.uniform(0.1, 999.9), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=random_price)

        result = run_market_telegram_pipeline(
            storage_file=self.storage_file,
            symbol=self.symbol,
            chat_id=self.chat_id,
            url=self.url,
            telegram_token=self.telegram_token
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("symbol"), self.symbol)
        self.assertEqual(result.get("price"), random_price)
        self.assertEqual(result.get("chat_id"), self.chat_id)
        self.assertEqual(result.get("url"), self.url)

    def test_run_pipeline_execution(self):
        random_price = round(random.uniform(10.0, 50.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=random_price)

        pipeline_result = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(pipeline_result)

    def test_start_new_and_start_ened_aliases(self):
        random_price = round(random.uniform(100.0, 200.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=random_price)

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

    def test_export_audit_logs_scenarios(self):
        self.assertFalse(export_audit_logs(storage_file=None))
        self.assertFalse(export_audit_logs(storage_file=uuid.uuid4().hex))

        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("   ")
        self.assertFalse(export_audit_logs(storage_file=self.storage_file))

        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write('{"unclosed": ')
        self.assertFalse(export_audit_logs(storage_file=self.storage_file))

        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write('not a json string ' + ''.join(random.choices(string.ascii_letters, k=10)))
        self.assertFalse(export_audit_logs(storage_file=self.storage_file))

        valid_data = {uuid.uuid4().hex: random.randint(1, 500)}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(valid_data, f)
        self.assertTrue(export_audit_logs(storage_file=self.storage_file))

    def test_stream_bytes_io_mocking_mechanism(self):
        random_bytes = json.dumps({self.symbol: random.randint(5, 500)}).encode('utf-8')
        mock_file_stream = io.BytesIO(random_bytes)

        with patch("builtins.open", return_value=io.TextIOWrapper(mock_file_stream, encoding="utf-8")):
            generator = MarketReportGenerator(storage_file=self.storage_file)
            dump = generator.get_raw_stream_dump()
            self.assertIn(self.symbol, dump)