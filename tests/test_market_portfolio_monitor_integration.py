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
        self.storage_file = os.path.join(self.test_dir.name, f"storage_{uuid.uuid4()}.json")
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://api.telegram.org/bot{uuid.uuid4()}/sendMessage"
        self.telegram_token = str(uuid.uuid4())
        self.chat_id = str(random.randint(100000, 999999))
        self.price = round(random.uniform(10.0, 1500.0), 2)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_integration_pipeline_execution(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.price)

        self.assertTrue(os.path.exists(self.storage_file))

        pipeline_result = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(pipeline_result)

        start_new_result = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(start_new_result)

        start_ened_result = start_ened(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(start_ened_result)

        report_gen = MarketReportGenerator(storage_file=self.storage_file)
        symbol_report = report_gen.generate_symbol_report(symbol=self.symbol)
        self.assertIn(self.symbol, symbol_report)
        self.assertIn(str(self.price), symbol_report)

        raw_dump = report_gen.get_raw_stream_dump()
        self.assertIn(self.symbol, raw_dump)

        market_report = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
        self.assertIn(self.symbol, market_report)

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

        audit_exported = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_exported)

if __name__ == "__main__":
    unittest.main()