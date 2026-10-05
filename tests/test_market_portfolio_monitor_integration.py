import unittest
import tempfile
import os
import json
import uuid
import random
from skills.market_portfolio_monitor import (
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
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.test_dir.name, f"test_storage_{uuid.uuid4()}.json")
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.url = f"https://api.telegram.org/bot{uuid.uuid4()}/sendMessage"
        self.telegram_token = str(uuid.uuid4())
        self.chat_id = str(random.randint(100000, 999999))

    def tearDown(self):
        self.test_dir.cleanup()

    def test_integration_pipeline_flow(self):
        initial_price = round(random.uniform(10.0, 500.0), 2)
        initial_data = {self.symbol: initial_price}
        
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        res_start = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res_start)

        res_alias = start_ened(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res_alias)

        parser = MarketParser(storage_file=self.storage_file)
        loaded = parser.load_data(self.storage_file)
        self.assertIsInstance(loaded, dict)
        self.assertIn(self.symbol, loaded)
        self.assertEqual(loaded[self.symbol], initial_price)

        new_price = round(random.uniform(501.0, 1000.0), 2)
        parser.fetch_and_store(symbol=self.symbol, price=new_price)
        
        reloaded = parser.load_data(self.storage_file)
        self.assertEqual(reloaded[self.symbol], new_price)

        report_gen = MarketReportGenerator(storage_file=self.storage_file)
        symbol_report = report_gen.generate_symbol_report(symbol=self.symbol)
        self.assertIn(self.symbol, symbol_report)
        self.assertIn(str(new_price), symbol_report)

        raw_dump = report_gen.get_raw_stream_dump()
        self.assertIsInstance(raw_dump, str)
        self.assertIn(self.symbol, raw_dump)

        gen_report = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
        self.assertIn(self.symbol, gen_report)

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
        self.assertEqual(telegram_res.get("price"), new_price)
        self.assertEqual(telegram_res.get("chat_id"), self.chat_id)
        self.assertEqual(telegram_res.get("url"), self.url)

        audit_result = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_result)

    def test_integration_empty_and_malformed_storage(self):
        parser = MarketParser(storage_file=self.storage_file)
        loaded_empty = parser.load_data(self.storage_file)
        self.assertEqual(loaded_empty, {})

        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("{malformed_json")

        loaded_malformed = parser.load_data(self.storage_file)
        self.assertEqual(loaded_malformed, {})

        audit_malformed = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_malformed)

        audit_none = export_audit_logs(storage_file=None)
        self.assertFalse(audit_none)

if __name__ == "__main__":
    unittest.main()