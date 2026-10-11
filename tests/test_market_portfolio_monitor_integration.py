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
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://api.test.internal/{uuid.uuid4().hex[:8]}"
        self.telegram_token = f"bot{uuid.uuid4().hex[:10]}"
        self.chat_id = f"-{random.randint(100000000, 999999999)}"
        self.storage_file = f"test_storage_{uuid.uuid4().hex[:8]}.json"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_full_monitoring_pipeline_integration(self):
        initial_price = round(random.uniform(10.0, 5000.0), 2)
        
        parser_init = MarketParser(storage_file=self.storage_file)
        parser_init.fetch_and_store(symbol=self.symbol, price=initial_price)
        
        self.assertTrue(os.path.exists(self.storage_file), "Storage file must be created during fetch_and_store")
        
        pipeline_result = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(pipeline_result, "run_pipeline should return True on success")

        start_new_result = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(start_new_result, "start_new should return True on success")

        start_ened_result = start_ened(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(start_ened_result, "start_ened alias should return True on success")

        report_gen = MarketReportGenerator(storage_file=self.storage_file)
        symbol_report = report_gen.generate_symbol_report(symbol=self.symbol)
        self.assertIn(self.symbol, symbol_report)
        self.assertIn(str(initial_price), symbol_report)

        raw_dump = report_gen.get_raw_stream_dump()
        self.assertIn(self.symbol, raw_dump)

        func_report = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
        self.assertIn(self.symbol, func_report)

        tg_response = run_market_telegram_pipeline(
            storage_file=self.storage_file,
            symbol=self.symbol,
            chat_id=self.chat_id,
            url=self.url,
            telegram_token=self.telegram_token
        )
        self.assertEqual(tg_response["status"], "success")
        self.assertEqual(tg_response["symbol"], self.symbol)
        self.assertEqual(tg_response["price"], initial_price)
        self.assertEqual(tg_response["chat_id"], self.chat_id)
        self.assertEqual(tg_response["url"], self.url)

        audit_exported = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_exported, "export_audit_logs should successfully validate and export valid JSON storage")

if __name__ == "__main__":
    unittest.main()