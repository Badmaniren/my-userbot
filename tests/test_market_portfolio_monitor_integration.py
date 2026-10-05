import unittest
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
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://api.telegram.org/bot{uuid.uuid4().hex}/sendMessage"
        self.telegram_token = uuid.uuid4().hex
        self.chat_id = str(random.randint(100000, 999999))
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"
        self.initial_price = round(random.uniform(10.0, 1000.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_full_pipeline_and_start_aliases(self):
        initial_data = {self.symbol: self.initial_price}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

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

        parser = MarketParser(storage_file=self.storage_file)
        loaded = parser.load_data(self.storage_file)
        self.assertIsInstance(loaded, dict)
        self.assertIn(self.symbol, loaded)

        report_gen = MarketReportGenerator(storage_file=self.storage_file)
        symbol_report = report_gen.generate_symbol_report(symbol=self.symbol)
        self.assertIn(self.symbol, symbol_report)
        self.assertIn(str(self.initial_price), symbol_report)

        raw_dump = report_gen.get_raw_stream_dump()
        self.assertIsInstance(raw_dump, str)
        self.assertTrue(len(raw_dump) > 0)

        gen_market_rep = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
        self.assertIn(self.symbol, gen_market_rep)

        tg_result = run_market_telegram_pipeline(
            storage_file=self.storage_file,
            symbol=self.symbol,
            chat_id=self.chat_id,
            url=self.url,
            telegram_token=self.telegram_token
        )
        self.assertIsInstance(tg_result, dict)
        self.assertEqual(tg_result.get("status"), "success")
        self.assertEqual(tg_result.get("symbol"), self.symbol)
        self.assertEqual(tg_result.get("chat_id"), self.chat_id)
        self.assertEqual(tg_result.get("url"), self.url)

        audit_exported = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_exported)

    def test_parser_edge_cases_and_persistence(self):
        parser = MarketParser(storage_file=self.storage_file)
        new_price = round(random.uniform(1.0, 500.0), 2)
        parser.fetch_and_store(symbol=self.symbol, price=new_price)

        self.assertTrue(os.path.exists(self.storage_file))
        data = parser.load_data(self.storage_file)
        self.assertEqual(data.get(self.symbol), new_price)

        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("{invalid_json")

        bad_load = parser.load_data(self.storage_file)
        self.assertEqual(bad_load, {})

        audit_bad = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_bad)

if __name__ == "__main__":
    unittest.main()