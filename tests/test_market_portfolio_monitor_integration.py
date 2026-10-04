import unittest
import os
import tempfile
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
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.test_dir.name, f"test_storage_{uuid.uuid4()}.json")
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://api.example.com/v1/market/{uuid.uuid4().hex[:4]}"
        self.telegram_token = f"bot{random.randint(100000, 999999)}:AAG{uuid.uuid4().hex[:10]}"
        self.chat_id = str(random.randint(10000000, 99999999))
        self.initial_price = round(random.uniform(10.0, 1000.0), 2)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_full_pipeline_integration(self):
        # 1. Prepare initial state with a random price
        initial_data = {self.symbol: self.initial_price}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        # Generate new random price to verify update through pipeline
        updated_price = round(random.uniform(1001.0, 5000.0), 2)
        
        # We manually update storage to simulate parser loading and storing new metrics
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=updated_price)

        # 2. Execute start_new integration pipeline
        pipeline_result = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(pipeline_result)

        # 3. Verify alias start_ened works identically
        alias_result = start_ened(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(alias_result)

        # 4. Check MarketReportGenerator integration
        report_gen = MarketReportGenerator(storage_file=self.storage_file)
        report_text = report_gen.generate_symbol_report(symbol=self.symbol)
        self.assertIn(self.symbol, report_text)
        self.assertIn(str(updated_price), report_text)

        # 5. Check standalone report generation
        standalone_report = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
        self.assertEqual(report_text, standalone_report)

        # 6. Check telegram pipeline integration returns correct payload matching inputs
        tg_response = run_market_telegram_pipeline(
            storage_file=self.storage_file,
            symbol=self.symbol,
            chat_id=self.chat_id,
            url=self.url,
            telegram_token=self.telegram_token
        )
        self.assertEqual(tg_response["status"], "success")
        self.assertEqual(tg_response["symbol"], self.symbol)
        self.assertEqual(tg_response["price"], updated_price)
        self.assertEqual(tg_response["chat_id"], self.chat_id)
        self.assertEqual(tg_response["url"], self.url)

        # 7. Check audit log export integration
        audit_status = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_status)

    def test_corrupted_storage_handling_integration(self):
        # Write corrupted JSON to storage to test robustness across modules
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write('{"unclosed_json": ')

        # Audit logs should safely reject corrupted storage
        self.assertFalse(export_audit_logs(storage_file=self.storage_file))

        # Parser load_data should raise JSONDecodeError on unterminated object
        parser = MarketParser(storage_file=self.storage_file)
        with self.assertRaises(json.JSONDecodeError):
            parser.load_data(self.storage_file)

if __name__ == "__main__":
    unittest.main()