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
        self.test_dir = f"test_storage_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)
        self.storage_file = os.path.join(self.test_dir, f"portfolio_{uuid.uuid4().hex}.json")
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://api.test.local/{uuid.uuid4().hex}"
        self.telegram_token = f"token_{uuid.uuid4().hex}"
        self.chat_id = str(random.randint(100000, 999999))

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_full_pipeline_integration(self):
        initial_price = round(random.uniform(10.0, 1000.0), 2)
        initial_data = {self.symbol: initial_price}

        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        result_run = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(result_run)

        result_start = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(result_start)

        result_ened = start_ened(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(result_ened)

        parser = MarketParser(storage_file=self.storage_file)
        loaded = parser.load_data(self.storage_file)
        self.assertIsInstance(loaded, dict)
        self.assertIn(self.symbol, loaded)

        report_gen = MarketReportGenerator(storage_file=self.storage_file)
        symbol_report = report_gen.generate_symbol_report(symbol=self.symbol)
        self.assertIn(self.symbol, symbol_report)
        self.assertIn(str(initial_price), symbol_report)

        raw_dump = report_gen.get_raw_stream_dump()
        self.assertIn(self.symbol, raw_dump)

        market_report = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
        self.assertIn(self.symbol, market_report)

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
        self.assertEqual(telegram_res.get("chat_id"), self.chat_id)
        self.assertEqual(telegram_res.get("url"), self.url)
        self.assertEqual(telegram_res.get("price"), initial_price)

        audit_result = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_result)

    def test_corrupted_storage_handling(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("{corrupted_json_content_" + uuid.uuid4().hex)

        parser = MarketParser(storage_file=self.storage_file)
        data = parser.load_data(self.storage_file)
        self.assertEqual(data, {})

        new_price = round(random.uniform(1.0, 50.0), 2)
        parser.fetch_and_store(symbol=self.symbol, price=new_price)

        loaded_again = parser.load_data(self.storage_file)
        self.assertEqual(loaded_again.get(self.symbol), new_price)

        audit_result = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_result)

if __name__ == "__main__":
    unittest.main()