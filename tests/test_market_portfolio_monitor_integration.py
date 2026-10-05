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
        self.test_dir = f"test_storage_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)
        self.storage_file = os.path.join(self.test_dir, f"portfolio_{uuid.uuid4().hex}.json")
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://api.test.local/{uuid.uuid4().hex}"
        self.telegram_token = f"token_{uuid.uuid4().hex}"
        self.chat_id = str(random.randint(100000, 999999))
        self.initial_price = round(random.uniform(10.0, 5000.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_full_pipeline_integration(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.initial_price)

        self.assertTrue(os.path.exists(self.storage_file))

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

        report_gen = MarketReportGenerator(storage_file=self.storage_file)
        symbol_report = report_gen.generate_symbol_report(symbol=self.symbol)
        self.assertIn(self.symbol, symbol_report)
        self.assertIn(str(self.initial_price), symbol_report)

        raw_dump = report_gen.get_raw_stream_dump()
        self.assertIn(self.symbol, raw_dump)

        func_report = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
        self.assertIn(self.symbol, func_report)

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
        self.assertEqual(tg_result.get("price"), self.initial_price)
        self.assertEqual(tg_result.get("chat_id"), self.chat_id)
        self.assertEqual(tg_result.get("url"), self.url)

        audit_status = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_status)

if __name__ == "__main__":
    unittest.main()