import unittest
import os
import tempfile
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
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.temp_dir.name, f"test_storage_{uuid.uuid4().hex}.json")
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://api.test.local/{uuid.uuid4().hex}"
        self.telegram_token = f"token_{uuid.uuid4().hex}"
        self.chat_id = str(random.randint(100000, 999999))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_full_autonomous_macro_liquidity_pipeline(self):
        initial_price = round(random.uniform(10.0, 1500.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=initial_price)

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
        self.assertIn(str(initial_price), symbol_report)

        raw_dump = report_gen.get_raw_stream_dump()
        self.assertIn(self.symbol, raw_dump)

        market_report = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
        self.assertIn(self.symbol, market_report)

        telegram_result = run_market_telegram_pipeline(
            storage_file=self.storage_file,
            symbol=self.symbol,
            chat_id=self.chat_id,
            url=self.url,
            telegram_token=self.telegram_token
        )
        self.assertIsInstance(telegram_result, dict)
        self.assertEqual(telegram_result.get("status"), "success")
        self.assertEqual(telegram_result.get("symbol"), self.symbol)
        self.assertEqual(telegram_result.get("price"), initial_price)
        self.assertEqual(telegram_result.get("chat_id"), self.chat_id)
        self.assertEqual(telegram_result.get("url"), self.url)

        audit_exported = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_exported)

    def test_corrupted_storage_resilience(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("{invalid_json_stream_" + uuid.uuid4().hex)

        parser = MarketParser(storage_file=self.storage_file)
        data = parser.load_data(storage_file=self.storage_file)
        self.assertEqual(data, {})

        new_price = round(random.uniform(1.0, 100.0), 2)
        parser.fetch_and_store(symbol=self.symbol, price=new_price)

        loaded_data = parser.load_data(storage_file=self.storage_file)
        self.assertIsInstance(loaded_data, dict)
        self.assertEqual(loaded_data.get(self.symbol), new_price)

        audit_status = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_status)

if __name__ == "__main__":
    unittest.main()