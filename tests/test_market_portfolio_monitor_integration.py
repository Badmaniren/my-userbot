import unittest
import os
import json
import uuid
import random
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

class TestMarketPortfolioMonitorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.unique_id = str(uuid.uuid4())[:8]
        self.storage_file = os.path.join(self.test_dir, f"test_storage_{self.unique_id}.json")
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.url = f"https://api.test.internal/{uuid.uuid4()}"
        self.telegram_token = f"token_{uuid.uuid4()}"
        self.chat_id = str(random.randint(100000, 999999))

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_full_monitoring_pipeline_integration(self):
        initial_price = round(random.uniform(10.0, 1000.0), 2)
        initial_data = {self.symbol: initial_price}

        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

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

        parser = MarketParser(storage_file=self.storage_file)
        loaded_data = parser.load_data(storage_file=self.storage_file)
        self.assertIsInstance(loaded_data, dict)
        self.assertIn(self.symbol, loaded_data)
        self.assertEqual(loaded_data[self.symbol], initial_price)

        report_gen = MarketReportGenerator(storage_file=self.storage_file)
        symbol_report = report_gen.generate_symbol_report(symbol=self.symbol)
        self.assertIn(self.symbol, symbol_report)
        self.assertIn(str(initial_price), symbol_report)

        raw_dump = report_gen.get_raw_stream_dump()
        self.assertIsInstance(raw_dump, str)
        self.assertIn(self.symbol, raw_dump)

        gen_report_res = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
        self.assertEqual(gen_report_res, symbol_report)

        telegram_res = run_market_telegram_pipeline(
            storage_file=self.storage_file,
            symbol=self.symbol,
            chat_id=self.chat_id,
            url=self.url,
            telegram_token=self.telegram_token
        )
        self.assertIsInstance(telegram_res, dict)
        self.assertEqual(telegram_res.get("status"), "success")
        self.assertEqual(telegram_res.get("symbol"), self.symbol)
        self.assertEqual(telegram_res.get("price"), initial_price)
        self.assertEqual(telegram_res.get("chat_id"), self.chat_id)
        self.assertEqual(telegram_res.get("url"), self.url)

        audit_exported = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_exported)

    def test_parser_resilience_and_corrupted_data(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("{invalid_json_structure")

        parser = MarketParser(storage_file=self.storage_file)
        loaded_data = parser.load_data(storage_file=self.storage_file)
        self.assertEqual(loaded_data, {})

        new_price = round(random.uniform(1.0, 50.0), 2)
        parser.fetch_and_store(symbol=self.symbol, price=new_price)

        reloaded = parser.load_data(storage_file=self.storage_file)
        self.assertEqual(reloaded.get(self.symbol), new_price)

        audit_result = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_result)

if __name__ == "__main__":
    unittest.main()