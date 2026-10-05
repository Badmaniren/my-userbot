import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_monitor import (
    start_new,
    start_ened,
    run_pipeline,
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
        self.telegram_token = str(random.randint(100000000, 999999999)) + ":" + uuid.uuid4().hex[:10]
        self.chat_id = str(random.randint(-999999999, -100000000))
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"
        
        initial_price = round(random.uniform(10.0, 1500.0), 2)
        initial_data = {self.symbol: initial_price}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_full_pipeline_integration(self):
        success = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(success)

        parser = MarketParser(self.storage_file)
        loaded_data = parser.load_data(self.storage_file)
        self.assertIsInstance(loaded_data, dict)
        self.assertIn(self.symbol, loaded_data)

        report_gen = MarketReportGenerator(self.storage_file)
        symbol_report = report_gen.generate_symbol_report(self.symbol)
        self.assertIn(self.symbol, symbol_report)

        raw_dump = report_gen.get_raw_stream_dump()
        self.assertIn(self.symbol, raw_dump)

        market_report = generate_market_report(self.storage_file, self.symbol)
        self.assertIn(self.symbol, market_report)

        tg_result = run_market_telegram_pipeline(
            storage_file=self.storage_file,
            symbol=self.symbol,
            chat_id=self.chat_id,
            url=self.url,
            telegram_token=self.telegram_token
        )
        self.assertEqual(tg_result["status"], "success")
        self.assertEqual(tg_result["symbol"], self.symbol)
        self.assertEqual(tg_result["chat_id"], self.chat_id)
        self.assertEqual(tg_result["url"], self.url)

        audit_exported = export_audit_logs(self.storage_file)
        self.assertTrue(audit_exported)

    def test_start_aliases_integration(self):
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

if __name__ == "__main__":
    unittest.main()