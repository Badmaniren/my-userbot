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
        self.random_suffix = str(uuid.uuid4())[:8]
        self.storage_file = f"test_portfolio_storage_{self.random_suffix}.json"
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.url = f"https://api.test-telegram-{self.random_suffix}.org/bot"
        self.telegram_token = f"token_{uuid.uuid4()}"
        self.chat_id = str(random.randint(100000, 999999))
        self.price = round(random.uniform(10.0, 1500.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_integration_pipeline_and_storage_lifecycle(self):
        initial_data = {self.symbol: self.price}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        pipeline_result = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(pipeline_result)

        parser = MarketParser(storage_file=self.storage_file)
        loaded_data = parser.load_data(self.storage_file)
        self.assertIsInstance(loaded_data, dict)
        self.assertIn(self.symbol, loaded_data)
        self.assertEqual(loaded_data[self.symbol], self.price)

        report_gen = MarketReportGenerator(storage_file=self.storage_file)
        symbol_report = report_gen.generate_symbol_report(symbol=self.symbol)
        self.assertIn(self.symbol, symbol_report)
        self.assertIn(str(self.price), symbol_report)

        free_report = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
        self.assertEqual(symbol_report, free_report)

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
        self.assertEqual(telegram_res.get("price"), self.price)
        self.assertEqual(telegram_res.get("chat_id"), self.chat_id)
        self.assertEqual(telegram_res.get("url"), self.url)

        audit_status = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_status)

        new_symbol = f"NEW_{random.randint(1000, 9999)}"
        start_new_res = start_new(
            symbol=new_symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(start_new_res)

        start_ened_res = start_ened(
            symbol=new_symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(start_ened_res)

        final_data = parser.load_data(self.storage_file)
        self.assertIn(new_symbol, final_data)

if __name__ == "__main__":
    unittest.main()