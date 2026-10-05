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
        self.random_suffix = uuid.uuid4().hex[:8]
        self.storage_file = f"test_storage_{self.random_suffix}.json"
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.url = f"https://api.telegram.org/bot{uuid.uuid4().hex}"
        self.telegram_token = uuid.uuid4().hex
        self.chat_id = str(random.randint(100000, 999999))
        self.initial_price = round(random.uniform(10.0, 1500.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_full_pipeline_and_aliases_integration(self):
        initial_data = {self.symbol: self.initial_price}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        res_pipeline = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res_pipeline)

        new_symbol = f"NEW_{uuid.uuid4().hex[:4]}"
        res_start_new = start_new(
            symbol=new_symbol,
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

        parser = MarketParser(storage_file=self.storage_file)
        loaded_data = parser.load_data(self.storage_file)
        self.assertIsInstance(loaded_data, dict)
        self.assertIn(new_symbol, loaded_data)
        self.assertIn(self.symbol, loaded_data)

        report_gen = MarketReportGenerator(storage_file=self.storage_file)
        symbol_report = report_gen.generate_symbol_report(symbol=self.symbol)
        self.assertIn(self.symbol, symbol_report)
        self.assertIn(str(loaded_data[self.symbol]), symbol_report)

        raw_dump = report_gen.get_raw_stream_dump()
        self.assertIsInstance(raw_dump, str)
        self.assertIn(self.symbol, raw_dump)

        gen_market_rep = generate_market_report(storage_file=self.storage_file, symbol=new_symbol)
        self.assertIn(new_symbol, gen_market_rep)

        tg_result = run_market_telegram_pipeline(
            storage_file=self.storage_file,
            symbol=self.symbol,
            chat_id=self.chat_id,
            url=self.url,
            telegram_token=self.telegram_token
        )
        self.assertIsInstance(tg_result, dict)
        self.assertEqual(tg_result.get("status"), "success")
        self.assertEqual(tg_result.get("symbol"), self.symbol)
        self.assertEqual(tg_result.get("chat_id"), self.chat_id)
        self.assertEqual(tg_result.get("url"), self.url)
        self.assertEqual(tg_result.get("price"), loaded_data[self.symbol])

        audit_exported = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_exported)

    def test_corrupted_storage_handling(self):
        malformed_content = "{invalid_json_" + uuid.uuid4().hex
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(malformed_content)

        parser = MarketParser(storage_file=self.storage_file)
        data = parser.load_data(self.storage_file)
        self.assertEqual(data, {})

        res = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res)

        self.assertTrue(os.path.exists(self.storage_file))
        audit_res = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_res)

if __name__ == "__main__":
    unittest.main()