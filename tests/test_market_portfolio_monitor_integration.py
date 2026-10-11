import unittest
import os
import tempfile
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
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.test_dir.name, f"storage_{uuid.uuid4().hex}.json")
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://api.telegram.org/bot{uuid.uuid4().hex}/sendMessage"
        self.telegram_token = uuid.uuid4().hex
        self.chat_id = str(random.randint(100000, 99999999))

    def tearDown(self):
        self.test_dir.cleanup()

    def test_full_pipeline_integration(self):
        result_run = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(result_run)
        self.assertTrue(os.path.exists(self.storage_file))

        parser = MarketParser(storage_file=self.storage_file)
        loaded_data = parser.load_data(storage_file=self.storage_file)
        self.assertIsInstance(loaded_data, dict)
        self.assertIn(self.symbol, loaded_data)

        report_gen = MarketReportGenerator(storage_file=self.storage_file)
        symbol_report = report_gen.generate_symbol_report(symbol=self.symbol)
        self.assertIn(self.symbol, symbol_report)

        stream_dump = report_gen.get_raw_stream_dump()
        self.assertIsInstance(stream_dump, str)
        self.assertIn(self.symbol, stream_dump)

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
        self.assertEqual(telegram_res.get("chat_id"), self.chat_id)
        self.assertEqual(telegram_res.get("url"), self.url)

        audit_exported = export_audit_logs(storage_file=self.storage_file)
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

        symbol_ened = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        res_ened = start_ened(
            symbol=symbol_ened,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res_ened)

        parser = MarketParser(storage_file=self.storage_file)
        data = parser.load_data(storage_file=self.storage_file)
        self.assertIn(symbol_ened, data)

    def test_corrupted_storage_handling(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("{invalid_json_content")

        parser = MarketParser(storage_file=self.storage_file)
        data = parser.load_data(storage_file=self.storage_file)
        self.assertEqual(data, {})

        audit_exported = export_audit_logs(storage_file=self.storage_file)
        self.assertFalse(audit_exported)

        random_price = round(random.uniform(10.0, 1000.0), 2)
        parser.fetch_and_store(symbol=self.symbol, price=random_price)

        fixed_data = parser.load_data(storage_file=self.storage_file)
        self.assertIn(self.symbol, fixed_data)
        self.assertEqual(fixed_data[self.symbol], random_price)

if __name__ == "__main__":
    unittest.main()