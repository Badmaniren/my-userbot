import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_monitor import start_new, start_ened, export_audit_logs, MarketParser, MarketReportGenerator, market_portfolio_monitor

class TestMarketPortfolioMonitorIntegration(unittest.TestCase):
    def setUp(self):
        self.symbol = f"SYM_{uuid.uuid4().hex[:8].upper()}"
        self.url = f"https://api.mock-market-{uuid.uuid4().hex[:6]}.com/v1"
        self.telegram_token = f"bot{random.randint(100000, 999999)}:AAG{uuid.uuid4().hex[:6]}"
        self.chat_id = str(random.randint(10000000, 99999999))
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"
        self.initial_price = round(random.uniform(10.0, 1500.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_pipeline_and_storage_integration(self):
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=self.initial_price)
        
        self.assertTrue(os.path.exists(self.storage_file), "Storage file was not created by MarketParser")

        new_price = round(self.initial_price * 1.05, 2)

        result_start_new = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(result_start_new, "start_new pipeline execution failed")

        report_gen = MarketReportGenerator(storage_file=self.storage_file)
        raw_dump = report_gen.get_raw_stream_dump()
        parsed_dump = json.loads(raw_dump)

        self.assertIn(self.symbol, parsed_dump, f"Symbol {self.symbol} missing in raw stream dump")

        symbol_report = report_gen.generate_symbol_report(self.symbol)
        self.assertIn(self.symbol, symbol_report)

        result_start_ened = start_ened(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(result_start_ened, "start_ened alias execution failed")

        audit_exported = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_exported, "Audit log export failed for valid storage file")

    def test_liquidity_monitoring_integration(self):
        portfolio_payload = {
            "positions": [self.symbol, "BTC", "ETH"],
            "liquidity_score": 0.85,
            "avg_spread": 0.0005
        }
        res = market_portfolio_monitor(portfolio_payload)
        self.assertEqual(res["status"], "HEALTHY")
        self.assertEqual(res["positions_evaluated"], 3)
        self.assertAlmostEqual(res["liquidity_score"], 0.85)

if __name__ == '__main__':
    unittest.main()
