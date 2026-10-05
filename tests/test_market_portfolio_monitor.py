import unittest
from unittest.mock import patch
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
        self.random_prefix = uuid.uuid4().hex
        self.storage_file = f"{self.random_prefix}_storage.json"
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.price = round(random.uniform(10.0, 1000.0), 2)
        self.url = f"https://{uuid.uuid4().hex}.test/api"
        self.telegram_token = uuid.uuid4().hex
        self.chat_id = str(random.randint(100000, 999999))

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_market_parser_load_and_store(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)

        self.assertTrue(os.path.exists(self.storage_file))

        loaded_data = parser.load_data(storage_file=self.storage_file)
        self.assertIsInstance(loaded_data, dict)
        self.assertIn(self.symbol, loaded_data)
        self.assertEqual(loaded_data[self.symbol], self.price)

    def test_market_parser_load_data_none_and_missing(self):
        parser = MarketParser(storage_file=None)
        self.assertIsNone(parser.load_data(None))

        non_existent_file = f"{uuid.uuid4().hex}_missing.json"
        parser_missing = MarketParser(storage_file=non_existent_file)
        self.assertEqual(parser_missing.load_data(non_existent_file), {})

    def test_market_parser_malformed_json(self):
        malformed_contents = [
            "{unclosed_json",
            "just random string data " + uuid.uuid4().hex,
            "12345"
        ]
        for content in malformed_contents:
            with open(self.storage_file, "w", encoding="utf-8") as f:
                f.write(content)
            
            parser = MarketParser(storage_file=self.storage_file)
            data = parser.load_data(self.storage_file)
            self.assertEqual(data, {})

    def test_market_report_generator_symbol_report(self):
        data = {self.symbol: self.price}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(data, f)

        gen = MarketReportGenerator(storage_file=self.storage_file)
        report = gen.generate_symbol_report(self.symbol)
        self.assertIn(self.symbol, report)
        self.assertIn(str(self.price), report)

        missing_symbol = f"MIS_{uuid.uuid4().hex}"
        missing_report = gen.generate_symbol_report(missing_symbol)
        self.assertIn(missing_symbol, missing_report)
        self.assertIn("No data", missing_report)

    def test_market_report_generator_get_raw_stream_dump(self):
        gen_none = MarketReportGenerator(storage_file=None)
        self.assertEqual(gen_none.get_raw_stream_dump(), "{}")

        data = {uuid.uuid4().hex: random.randint(1, 100)}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(data, f)

        gen = MarketReportGenerator(storage_file=self.storage_file)
        dump = gen.get_raw_stream_dump()
        self.assertIn(list(data.keys())[0], dump)

    def test_generate_market_report_wrapper(self):
        data = {self.symbol: self.price}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(data, f)

        report = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
        self.assertIn(self.symbol, report)
        self.assertIn(str(self.price), report)

    def test_run_market_telegram_pipeline(self):
        data = {self.symbol: self.price}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(data, f)

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

    def test_export_audit_logs(self):
        self.assertFalse(export_audit_logs(storage_file=None))
        
        non_file = f"{uuid.uuid4().hex}_audit.json"
        self.assertFalse(export_audit_logs(storage_file=non_file))

        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("   ")
        self.assertFalse(export_audit_logs(storage_file=self.storage_file))

        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("{partial_json")
        self.assertTrue(export_audit_logs(storage_file=self.storage_file))

        valid_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(valid_data, f)
        self.assertTrue(export_audit_logs(storage_file=self.storage_file))

    def test_pipelines_execution(self):
        res_pipeline = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res_pipeline)

        res_start_new = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res_start_new)

        res_start_ened = start_ened(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res_start_ened)


if __name__ == "__main__":
    unittest.main()