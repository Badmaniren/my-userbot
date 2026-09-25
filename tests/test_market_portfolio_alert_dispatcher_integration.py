import unittest
import os
import tempfile
import uuid
import random
from skills import market_portfolio_alert_dispatcher
from skills import market_portfolio_monitor
from skills import market_portfolio_valuation

class TestMarketPortfolioAlertDispatcherIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.test_dir.name, f"test_storage_{uuid.uuid4().hex}.json")
        self.symbol = f"TEST_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"http://127.0.0.1:{random.randint(10000, 65535)}/api/v1/portfolio"
        self.telegram_token = f"{random.randint(100000, 999999)}:AA{uuid.uuid4().hex[:20]}"
        self.chat_id = f"-{random.randint(100000000, 999999999)}"
        self.severity_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    def tearDown(self):
        self.test_dir.cleanup()

    def test_dispatch_portfolio_alerts_integration_flow(self):
        random_severity = random.choice(self.severity_levels)
        min_threshold = random.choice(self.severity_levels)
        
        result = market_portfolio_alert_dispatcher.dispatch_portfolio_alerts(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            severity_level=random_severity,
            min_threshold=min_threshold,
            channels=["telegram"]
        )

        severity_weights = {"LOW": 10, "MEDIUM": 20, "HIGH": 30, "CRITICAL": 40}
        current_weight = severity_weights.get(random_severity, 20)
        threshold_weight = severity_weights.get(min_threshold, 20)

        if current_weight < threshold_weight:
            self.assertEqual(result.get("status"), "filtered_out")
        else:
            self.assertEqual(result.get("status"), "dispatched")
            self.assertIn("summary", result)
            self.assertIn("pnl", result)
            self.assertTrue(os.path.exists(self.storage_file))

    def test_process_stream_alert_integration(self):
        random_alert_id = uuid.uuid4().hex
        stream_data = market_portfolio_alert_dispatcher.process_stream_alert(random_alert_id)
        self.assertTrue(hasattr(stream_data, "read"))

if __name__ == "__main__":
    unittest.main()