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
        self.fd, self.storage_file = tempfile.mkstemp(suffix=".json")
        os.close(self.fd)
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://api.test.internal/{uuid.uuid4().hex[:8]}"
        self.telegram_token = f"token_{uuid.uuid4().hex[:10]}"
        self.chat_id = str(random.randint(100000, 999999))
        self.initial_price = round(random.uniform(10.0, 1500.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_full_monitoring_pipeline_integration(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.initial_price)

        res_start = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res_start)

        res_ened = start_ened(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res_ened)

        report_text = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
        self.assertIn(self.symbol, report_text)
        self.assertIn(str(self.initial_price), report_text)

        pipeline_result = run_market_telegram_pipeline(
            storage_file=self.storage_file,
            symbol=self.symbol,
            chat_id=self.chat_id,
            url=self.url,
            telegram_token=self.telegram_token
        )
        self.assertIsInstance(pipeline_result, dict)
        self.assertEqual(pipeline_result.get("status"), "success")
        self.assertEqual(pipeline_result.get("symbol"), self.symbol)
        self.assertEqual(pipeline_result.get("price"), self.initial_price)
        self.assertEqual(pipeline_result.get("chat_id"), self.chat_id)
        self.assertEqual(pipeline_result.get("url"), self.url)

        audit_exported = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_exported)

        generator = MarketReportGenerator(storage_file=self.storage_file)
        stream_dump = generator.get_raw_stream_dump()
        self.assertIn(self.symbol, stream_dump)
        self.assertIn(str(self.initial_price), stream_dump)

if __name__ == "__main__":
    unittest.main()