import unittest
import json
import os
import io
import uuid
import random
from unittest.mock import patch, mock_open
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
        self.telegram_token = f"{random.randint(100000, 999999)}:AA{uuid.uuid4().hex[:20]}"
        self.chat_id = str(random.randint(-999999999, -100000000))
        self.storage_file = f"temp_storage_{uuid.uuid4().hex}.json"
        self.price = round(random.uniform(10.0, 5000.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_market_parser_fetch_and_store_and_load(self):
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, self.price)
        data = parser.load_data(self.storage_file)
        self.assertIsInstance(data, dict)
        self.assertIn(self.symbol, data)
        self.assertEqual(data[self.symbol], self.price)

    def test_market_parser_load_nonexistent(self):
        non_existent = f"ghost_{uuid.uuid4().hex}.json"
        parser = MarketParser(non_existent)
        data = parser.load_data(non_existent)
        self.assertIsNone(data)

    def test_market_parser_load_invalid_json(self):
        garbage = f"bad_json_{uuid.uuid4().hex}"
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(garbage)
        parser = MarketParser(self.storage_file)
        data = parser.load_data(self.storage_file)
        self.assertIsNone(data)

    def test_market_parser_load_non_dict_json(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump([random.randint(1, 100), uuid.uuid4().hex], f)
        parser = MarketParser(self.storage_file)
        data = parser.load_data(self.storage_file)
        self.assertEqual(data, {})

    def test_market_report_generator_symbol_report(self):
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, self.price)
        generator = MarketReportGenerator(self.storage_file)
        report = generator.generate_symbol_report(self.symbol)
        self.assertIn(self.symbol, report)
        self.assertIn(str(self.price), report)

    def test_market_report_generator_no_data(self):
        generator = MarketReportGenerator(self.storage_file)
        report = generator.generate_symbol_report(self.symbol)
        self.assertIn("No data", report)

    def test_market_report_generator_raw_stream_dump(self):
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, self.price)
        generator = MarketReportGenerator(self.storage_file)
        dump = generator.get_raw_stream_dump()
        self.assertIn(self.symbol, dump)
        self.assertIn(str(self.price), dump)

    def test_market_report_generator_raw_stream_dump_empty(self):
        generator = MarketReportGenerator(f"empty_{uuid.uuid4().hex}.json")
        dump = generator.get_raw_stream_dump()
        self.assertEqual(dump, "{}")

    def test_generate_market_report_wrapper(self):
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, self.price)
        res = generate_market_report(self.storage_file, self.symbol)
        self.assertIn(self.symbol, res)
        self.assertIn(str(self.price), res)

    def test_run_market_telegram_pipeline(self):
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, self.price)
        res = run_market_telegram_pipeline(
            storage_file=self.storage_file,
            symbol=self.symbol,
            chat_id=self.chat_id,
            url=self.url,
            telegram_token=self.telegram_token
        )
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["symbol"], self.symbol)
        self.assertEqual(res["price"], self.price)
        self.assertEqual(res["chat_id"], self.chat_id)
        self.assertEqual(res["url"], self.url)

    def test_run_market_telegram_pipeline_missing_storage(self):
        ghost_storage = f"ghost_{uuid.uuid4().hex}.json"
        res = run_market_telegram_pipeline(
            storage_file=ghost_storage,
            symbol=self.symbol,
            chat_id=self.chat_id,
            url=self.url,
            telegram_token=self.telegram_token
        )
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["price"], 0.0)

    def test_run_pipeline(self):
        success = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(success)

    def test_start_new_and_ened(self):
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
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, self.price)
        self.assertTrue(export_audit_logs(self.storage_file))

    def test_export_audit_logs_none_or_missing(self):
        self.assertFalse(export_audit_logs(None))
        self.assertFalse(export_audit_logs(f"fake_{uuid.uuid4().hex}.json"))

    def test_export_audit_logs_empty_file(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("   \n")
        self.assertFalse(export_audit_logs(self.storage_file))

    def test_export_audit_logs_invalid_json(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(uuid.uuid4().hex)
        self.assertFalse(export_audit_logs(self.storage_file))

    def test_export_audit_logs_non_dict_json(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump([random.randint(1, 50)], f)
        self.assertFalse(export_audit_logs(self.storage_file))

    def test_market_parser_with_bytes_io_mock(self):
        payload = json.dumps({self.symbol: self.price}).encode("utf-8")
        mock_file = io.BytesIO(payload)

        with patch("builtins.open", mock_open(read_data=payload.decode("utf-8"))):
            parser = MarketParser(self.storage_file)
            data = parser.load_data(self.storage_file)
            self.assertIsInstance(data, dict)
            self.assertIn(self.symbol, data)
            self.assertEqual(data[self.symbol], self.price)