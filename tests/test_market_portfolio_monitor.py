import unittest
from unittest.mock import patch, mock_open
import os
import io
import json
import uuid
import random
import string

from skills.market_portfolio_monitor import (
    MarketParser,
    MarketReportGenerator,
    MarketPortfolioMonitor,
    market_portfolio_monitor,
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
        self.random_token = f"{random.randint(100000, 999999)}:{uuid.uuid4().hex[:10]}"
        self.random_chat_id = str(random.randint(-999999999, -100000000))
        self.random_storage = f"/tmp/{uuid.uuid4().hex}.json"
        self.random_price = round(random.uniform(10.0, 5000.0), 2)

    def tearDown(self):
        if os.path.exists(self.random_storage):
            try:
                os.remove(self.random_storage)
            except OSError:
                pass

    def test_market_parser_load_data_none(self):
        parser = MarketParser(storage_file=None)
        res = parser.load_data(None)
        self.assertIsNone(res)

    def test_market_parser_load_data_nonexistent(self):
        non_existent = f"/tmp/{uuid.uuid4().hex}.json"
        parser = MarketParser(storage_file=non_existent)
        res = parser.load_data(non_existent)
        self.assertEqual(res, {})

    def test_market_parser_fetch_and_load_valid(self):
        parser = MarketParser(storage_file=self.random_storage)
        parser.fetch_and_store(symbol=self.random_symbol, price=self.random_price)
        
        loaded = parser.load_data(self.random_storage)
        self.assertIsInstance(loaded, dict)
        self.assertIn(self.random_symbol, loaded)
        self.assertEqual(loaded[self.random_symbol], self.random_price)

    def test_market_parser_corrupted_json_handling(self):
        garbage_content = ''.join(random.choices(string.ascii_letters + string.punctuation, k=30))
        with open(self.random_storage, "w", encoding="utf-8") as f:
            f.write(garbage_content)

        parser = MarketParser(storage_file=self.random_storage)
        data = parser.load_data(self.random_storage)
        self.assertEqual(data, {})

    def test_market_parser_binary_stream_handling(self):
        binary_data = io.BytesIO(json.dumps({self.random_symbol: self.random_price}).encode("utf-8"))
        
        with patch("builtins.open", mock_open(read_data=binary_data.read())):
            parser = MarketParser(storage_file=self.random_storage)
            data = parser.load_data(self.random_storage)
            self.assertIsInstance(data, dict)

    def test_market_report_generator_symbol_report(self):
        parser = MarketParser(storage_file=self.random_storage)
        parser.fetch_and_store(symbol=self.random_symbol, price=self.random_price)

        gen = MarketReportGenerator(storage_file=self.random_storage)
        report = gen.generate_symbol_report(symbol=self.random_symbol)
        
        self.assertIn(self.random_symbol, report)
        self.assertIn(str(self.random_price), report)

    def test_market_report_generator_no_data(self):
        gen = MarketReportGenerator(storage_file=self.random_storage)
        report = gen.generate_symbol_report(symbol=self.random_symbol)
        
        self.assertIn(self.random_symbol, report)
        self.assertIn("No data", report)

    def test_market_report_generator_get_raw_stream_dump(self):
        payload = {uuid.uuid4().hex: random.randint(1, 100)}
        with open(self.random_storage, "w", encoding="utf-8") as f:
            json.dump(payload, f)

        gen = MarketReportGenerator(storage_file=self.random_storage)
        dump = gen.get_raw_stream_dump()
        
        self.assertIsInstance(dump, str)
        loaded_dump = json.loads(dump)
        self.assertEqual(loaded_dump, payload)

    def test_generate_market_report_helper(self):
        parser = MarketParser(storage_file=self.random_storage)
        parser.fetch_and_store(symbol=self.random_symbol, price=self.random_price)

        res = generate_market_report(storage_file=self.random_storage, symbol=self.random_symbol)
        self.assertIn(self.random_symbol, res)
        self.assertIn(str(self.random_price), res)

    def test_run_market_telegram_pipeline(self):
        parser = MarketParser(storage_file=self.random_storage)
        parser.fetch_and_store(symbol=self.random_symbol, price=self.random_price)

        result = run_market_telegram_pipeline(
            storage_file=self.random_storage,
            symbol=self.random_symbol,
            chat_id=self.random_chat_id,
            url=self.random_url,
            telegram_token=self.random_token
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["symbol"], self.random_symbol)
        self.assertEqual(result["price"], self.random_price)
        self.assertEqual(result["chat_id"], self.random_chat_id)
        self.assertEqual(result["url"], self.random_url)

    def test_export_audit_logs_valid_file(self):
        payload = {uuid.uuid4().hex: uuid.uuid4().hex}
        with open(self.random_storage, "w", encoding="utf-8") as f:
            json.dump(payload, f)

        res = export_audit_logs(storage_file=self.random_storage)
        self.assertTrue(res)

    def test_export_audit_logs_nonexistent(self):
        res = export_audit_logs(storage_file=None)
        self.assertFalse(res)

    def test_run_pipeline_execution(self):
        res = run_pipeline(
            symbol=self.random_symbol,
            url=self.random_url,
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            storage_file=self.random_storage
        )
        self.assertTrue(res)

    def test_start_new_execution(self):
        res = start_new(
            symbol=self.random_symbol,
            url=self.random_url,
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            storage_file=self.random_storage
        )
        self.assertTrue(res)

    def test_start_ened_execution(self):
        res = start_ened(
            symbol=self.random_symbol,
            url=self.random_url,
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            storage_file=self.random_storage
        )
        self.assertTrue(res)

    def test_market_portfolio_monitor_class_methods(self):
        monitor = MarketPortfolioMonitor(storage_file=self.random_storage)
        self.assertEqual(monitor.storage_file, self.random_storage)

        # Test ingest_and_monitor
        with open(self.random_storage, "w", encoding="utf-8") as f:
            json.dump({self.random_symbol: self.random_price}, f)
        res = monitor.ingest_and_monitor()
        self.assertEqual(res.get("status"), "success")
        self.assertEqual(res.get("data", {}).get(self.random_symbol), self.random_price)

        # Test get_portfolio_liquidity
        liq = monitor.get_portfolio_liquidity(self.random_symbol)
        self.assertEqual(liq, 100.0)
        self.assertEqual(monitor.get_portfolio_liquidity(""), 0.0)

        # Test assess_portfolio_liquidity_state
        self.assertEqual(monitor.assess_portfolio_liquidity_state(None), "liquid")
        self.assertEqual(monitor.assess_portfolio_liquidity_state({"risk_level": "high"}), "illiquid")
        self.assertEqual(monitor.assess_portfolio_liquidity_state({"risk_level": "low"}), "liquid")

        # Test load_macro_state_from_file
        macro_file = f"/tmp/{uuid.uuid4().hex}_macro.json"
        try:
            with open(macro_file, "w", encoding="utf-8") as f:
                json.dump({"macro_index": 0.85}, f)
            macro_data = MarketPortfolioMonitor.load_macro_state_from_file(macro_file)
            self.assertEqual(macro_data, {"macro_index": 0.85})
        finally:
            if os.path.exists(macro_file):
                os.remove(macro_file)

        # Test load_macro_state_from_file nonexistent
        self.assertEqual(MarketPortfolioMonitor.load_macro_state_from_file("nonexistent.json"), {})

    def test_market_portfolio_monitor_alias(self):
        self.assertEqual(market_portfolio_monitor, MarketPortfolioMonitor)
        inst = market_portfolio_monitor()
        self.assertIsInstance(inst, MarketPortfolioMonitor)

if __name__ == "__main__":
    unittest.main()