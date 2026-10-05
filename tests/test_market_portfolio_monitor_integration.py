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
        self.random_suffix = uuid.uuid4().hex[:8]
        self.storage_file = f"test_storage_{self.random_suffix}.json"
        self.symbol = f"SYM_{random.randint(100, 999)}"
        self.price = round(random.uniform(10.0, 1000.0), 2)
        self.chat_id = str(random.randint(100000, 999999))
        self.url = f"https://api.telegram.org/bot{random.randint(1000,9999)}:test/sendMessage"
        self.telegram_token = f"{random.randint(1000,9999)}:ABC-DEF{random.randint(100,999)}"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_full_integration_pipeline_and_storage(self):
        initial_data = {self.symbol: self.price}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        pipeline_result = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(pipeline_result)

        alias_result = start_ened(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(alias_result)

        parser = MarketParser(storage_file=self.storage_file)
        loaded_data = parser.load_data(self.storage_file)
        self.assertIsInstance(loaded_data, dict)
        self.assertIn(self.symbol, loaded_data)
        self.assertEqual(loaded_data[self.symbol], self.price)

        report_gen = MarketReportGenerator(storage_file=self.storage_file)
        symbol_report = report_gen.generate_symbol_report(symbol=self.symbol)
        self.assertIn(self.symbol, symbol_report)
        self.assertIn(str(self.price), symbol_report)

        raw_dump = report_gen.get_raw_stream_dump()
        self.assertIn(self.symbol, raw_dump)

        general_report = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
        self.assertIn(self.symbol, general_report)

        telegram_response = run_market_telegram_pipeline(
            storage_file=self.storage_file,
            symbol=self.symbol,
            chat_id=self.chat_id,
            url=self.url,
            telegram_token=self.telegram_token
        )
        self.assertIsInstance(telegram_response, dict)
        self.assertEqual(telegram_response.get("status"), "success")
        self.assertEqual(telegram_response.get("symbol"), self.symbol)
        self.assertEqual(telegram_response.get("price"), self.price)
        self.assertEqual(telegram_response.get("chat_id"), self.chat_id)
        self.assertEqual(telegram_response.get("url"), self.url)

        audit_status = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_status)

if __name__ == "__main__":
    unittest.main()