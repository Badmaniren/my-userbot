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
    export_audit_logs
)

class TestMarketPortfolioMonitor(unittest.TestCase):

    def setUp(self):
        self.rand_symbol = f"SYM_{uuid.uuid4().hex[:8].upper()}"
        self.rand_url = f"https://api.{uuid.uuid4().hex[:6]}.org/v1/hook"
        self.rand_token = f"tok_{uuid.uuid4().hex}"
        self.rand_chat = f"-100{random.randint(1000000, 99999999)}"
        self.rand_file = f"store_{uuid.uuid4().hex}.json"
        self.rand_price = round(random.uniform(10.0, 5000.0), 4)

    def tearDown(self):
        if os.path.exists(self.rand_file):
            try:
                os.remove(self.rand_file)
            except OSError:
                pass

    def test_market_parser_fetch_and_store_and_load(self):
        parser = MarketParser(self.rand_file)
        parser.fetch_and_store(self.rand_symbol, self.rand_price)
        
        self.assertTrue(os.path.exists(self.rand_file))
        
        loaded = parser.load_data(self.rand_file)
        self.assertIsInstance(loaded, dict)
        self.assertIn(self.rand_symbol, loaded)
        self.assertEqual(loaded[self.rand_symbol], self.rand_price)

    def test_market_parser_load_data_invalid_json(self):
        garbage = f"{{invalid_json_{uuid.uuid4().hex}"
        with open(self.rand_file, "w", encoding="utf-8") as f:
            f.write(garbage)
            
        parser = MarketParser(self.rand_file)
        res = parser.load_data(self.rand_file)
        self.assertEqual(res, {})

    def test_market_parser_load_non_existent(self):
        non_file = f"non_{uuid.uuid4().hex}.json"
        parser = MarketParser(non_file)
        self.assertIsNone(parser.load_data(non_file))

    def test_market_report_generator_symbol_report(self):
        data = {self.rand_symbol: self.rand_price}
        with open(self.rand_file, "w", encoding="utf-8") as f:
            json.dump(data, f)
            
        gen = MarketReportGenerator(self.rand_file)
        report = gen.generate_symbol_report(self.rand_symbol)
        self.assertIn(self.rand_symbol, report)
        self.assertIn(str(self.rand_price), report)

    def test_market_report_generator_no_data(self):
        gen = MarketReportGenerator(self.rand_file)
        report = gen.generate_symbol_report(self.rand_symbol)
        self.assertIn("No data", report)

    def test_market_report_generator_get_raw_stream_dump(self):
        dump_data = {uuid.uuid4().hex: random.randint(1, 100)}
        with open(self.rand_file, "w", encoding="utf-8") as f:
            json.dump(dump_data, f)
            
        gen = MarketReportGenerator(self.rand_file)
        raw = gen.get_raw_stream_dump()
        parsed_raw = json.loads(raw)
        self.assertEqual(parsed_raw, dump_data)

    def test_generate_market_report_func(self):
        data = {self.rand_symbol: self.rand_price}
        with open(self.rand_file, "w", encoding="utf-8") as f:
            json.dump(data, f)
            
        res = generate_market_report(self.rand_file, self.rand_symbol)
        self.assertIn(self.rand_symbol, res)

    def test_run_market_telegram_pipeline(self):
        data = {self.rand_symbol: self.rand_price}
        with open(self.rand_file, "w", encoding="utf-8") as f:
            json.dump(data, f)
            
        pipeline_res = run_market_telegram_pipeline(
            storage_file=self.rand_file,
            symbol=self.rand_symbol,
            chat_id=self.rand_chat,
            url=self.rand_url,
            telegram_token=self.rand_token
        )
        
        self.assertEqual(pipeline_res["status"], "success")
        self.assertEqual(pipeline_res["symbol"], self.rand_symbol)
        self.assertEqual(pipeline_res["price"], self.rand_price)
        self.assertEqual(pipeline_res["chat_id"], self.rand_chat)
        self.assertEqual(pipeline_res["url"], self.rand_url)

    def test_run_pipeline(self):
        res = run_pipeline(
            symbol=self.rand_symbol,
            url=self.rand_url,
            telegram_token=self.rand_token,
            chat_id=self.rand_chat,
            storage_file=self.rand_file
        )
        self.assertTrue(res)
        self.assertTrue(os.path.exists(self.rand_file))

    def test_start_new_and_ened_aliases(self):
        res_new = start_new(
            symbol=self.rand_symbol,
            url=self.rand_url,
            telegram_token=self.rand_token,
            chat_id=self.rand_chat,
            storage_file=self.rand_file
        )
        self.assertTrue(res_new)

        res_ened = start_ened(
            symbol=self.rand_symbol,
            url=self.rand_url,
            telegram_token=self.rand_token,
            chat_id=self.rand_chat,
            storage_file=self.rand_file
        )
        self.assertTrue(res_ened)

    def test_export_audit_logs_empty(self):
        with open(self.rand_file, "w", encoding="utf-8") as f:
            f.write("   ")
        self.assertFalse(export_audit_logs(self.rand_file))

    def test_export_audit_logs_valid_json(self):
        data = {uuid.uuid4().hex: uuid.uuid4().hex}
        with open(self.rand_file, "w", encoding="utf-8") as f:
            json.dump(data, f)
        self.assertTrue(export_audit_logs(self.rand_file))

    def test_export_audit_logs_malformed_json_like(self):
        garbage = f"{{{uuid.uuid4().hex}"
        with open(self.rand_file, "w", encoding="utf-8") as f:
            f.write(garbage)
        self.assertTrue(export_audit_logs(self.rand_file))

    def test_io_bytes_stream_mocking(self):
        stream_content = json.dumps({self.rand_symbol: self.rand_price}).encode("utf-8")
        mock_file_obj = io.BytesIO(stream_content)
        
        with patch("builtins.open", return_value=mock_file_obj):
            parser = MarketParser(self.rand_file)
            data = parser.load_data(self.rand_file)
            self.assertIsInstance(data, dict)

if __name__ == "__main__":
    unittest.main()