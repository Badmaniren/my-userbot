import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_monitor import start_new, export_audit_logs, MarketParser, MarketPortfolioMonitor

class TestMarketPortfolioMonitorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = f"test_storage_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)
        self.storage_file = os.path.join(self.test_dir, f"portfolio_{uuid.uuid4().hex}.json")
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.url = f"https://api.example.com/webhook/{uuid.uuid4().hex}"
        self.telegram_token = f"{random.randint(100000, 999999)}:ABC-{uuid.uuid4().hex[:6]}"
        self.chat_id = f"@{uuid.uuid4().hex[:8]}"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass
        if os.path.exists(self.test_dir):
            try:
                os.rmdir(self.test_dir)
            except OSError:
                pass

    def test_pipeline_integration_flow(self):
        initial_data = {self.symbol: round(random.uniform(10.0, 500.0), 2)}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        result = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )

        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.storage_file))

        parser = MarketParser(storage_file=self.storage_file)
        loaded_data = parser.load_data(storage_file=self.storage_file)
        self.assertIn(self.symbol, loaded_data)
        self.assertEqual(loaded_data[self.symbol], initial_data[self.symbol])

        audit_status = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(audit_status)

        # Monitor integration test
        monitor = MarketPortfolioMonitor(storage_file=self.storage_file)
        monitored_res = monitor.ingest_and_monitor()
        self.assertEqual(monitored_res["status"], "success")
        self.assertEqual(monitored_res["data"][self.symbol], initial_data[self.symbol])

        liquidity_state = monitor.assess_portfolio_liquidity_state(monitored_res["data"])
        self.assertEqual(liquidity_state, "liquid")

if __name__ == "__main__":
    unittest.main()