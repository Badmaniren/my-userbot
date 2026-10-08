import unittest
import os
import tempfile
import uuid
import random
from skills import market_portfolio_alert_dispatcher

class TestMarketPortfolioAlertDispatcherIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"http://localhost:{random.randint(1024, 65535)}/{uuid.uuid4().hex[:8]}"
        self.telegram_token = f"{random.randint(100000, 999999)}:AAG{uuid.uuid4().hex[:21].upper()}"
        self.chat_id = str(random.randint(10000000, 99999999))
        self.storage_file = os.path.join(self.test_dir.name, f"portfolio_{uuid.uuid4().hex[:8]}.json")
        self.alert_id = random.randint(10000, 99999)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_dispatch_portfolio_alerts_integration(self):
        severity_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        chosen_severity = random.choice(severity_levels)
        chosen_threshold = random.choice(severity_levels)

        result = market_portfolio_alert_dispatcher.dispatch_portfolio_alerts(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            severity_level=chosen_severity,
            min_threshold=chosen_threshold,
            channels=["telegram"]
        )

        severity_weights = {"LOW": 10, "MEDIUM": 20, "HIGH": 30, "CRITICAL": 40}
        current_weight = severity_weights.get(chosen_severity, 20)
        threshold_weight = severity_weights.get(chosen_threshold, 20)

        if current_weight < threshold_weight:
            self.assertEqual(result.get("status"), "filtered_out")
        else:
            self.assertEqual(result.get("status"), "dispatched")
            self.assertIn("summary", result)
            self.assertIn("pnl", result)
            self.assertTrue(os.path.exists(self.storage_file))

    def test_process_stream_alert_integration(self):
        stream_result = market_portfolio_alert_dispatcher.process_stream_alert(self.alert_id)
        self.assertIsNotNone(stream_result)

if __name__ == "__main__":
    unittest.main()