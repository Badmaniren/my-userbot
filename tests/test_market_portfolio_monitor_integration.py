import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_monitor import (
    start_new,
    start_ened,
    run_pipeline,
    MarketParser,
    MarketReportGenerator,
    generate_market_report,
    run_market_telegram_pipeline,
    export_audit_logs
)

class TestMarketPortfolioMonitorIntegration(unittest.TestCase):
    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.storage_file = f"test_market_storage_{self.random_suffix}.json"
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.url = f"https://api.test.net/{uuid.uuid4().hex[:6]}"
        self.telegram_token = f"token_{uuid.uuid4().hex[:6]}"
        self.chat_id = str(random.randint(100000, 999999))

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_full_autonomous_macro_liquidity_pipeline(self):
        initial_price = round(random.uniform(10.0, 1500.0), 2)
        
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=initial_price)
        
        self.assertTrue(os.path.exists(self.storage_file), "Storage file must be created by MarketParser")

        pipeline_res = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(pipeline_res, "run_pipeline must return True on success")

        new_symbol = f"SYM_{random.randint(20000, 30000)}"
        new_price = round(random.uniform(1500.1, 5000.0), 2)
        
        start_new_res = start_new(
            symbol=new_symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(start_new_res, "start_new must return True")

        start_ened_res = start_ened(
            symbol=new_symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(start_ened_res, "start_ened alias must return True")

        report_gen = MarketReportGenerator(storage_file=self.storage_file)
        sym_report = report_gen.generate_symbol_report(symbol=new_symbol)
        self.assertIn(new_symbol, sym_report)

        raw_dump = report_gen.get_raw_stream_dump()
        self.assertIsInstance(raw_dump, str)
        parsed_dump = json.loads(raw_dump)
        self.assertIn(new_symbol, parsed_dump)

        market_report = generate_market_report(storage_file=self.storage_file, symbol=new_symbol)
        self.assertIn(new_symbol, market_report)

        tg_pipeline_data = run_market_telegram_pipeline(
            storage_file=self.storage_file,
            symbol=new_symbol,
            chat_id=self.chat_id,
            url=self.url,
            telegram_token=self.telegram_token
        )
        self.assertEqual(tg_pipeline_data["status"], "success")
        self.assertEqual(tg_pipeline_data["symbol"], new_symbol)
        self.assertEqual(tg_pipeline_data["chat_id"], self.chat_id)
        self.assertEqual(tg_pipeline_data["url"], self.url)

        audit_exported = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_exported, "Audit logs export must return True for valid JSON storage")

    def test_corrupted_storage_resilience(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("{corrupted_json_payload_" + uuid.uuid4().hex)

        parser = MarketParser(storage_file=self.storage_file)
        loaded = parser.load_data(self.storage_file)
        self.assertEqual(loaded, {}, "Parser must safely fallback to empty dict on malformed data")

        audit_exported = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_exported, "Audit log exporter must handle specific malformed structures gracefully")

if __name__ == "__main__":
    unittest.main()