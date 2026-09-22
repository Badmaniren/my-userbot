import unittest
import os
import json
import uuid
import random
from skills import market_portfolio_alert_event_sink

class TestMarketPortfolioAlertEventSinkIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_storage_dir"
        os.makedirs(self.test_dir, exist_ok=True)
        self.storage_file = os.path.join(self.test_dir, f"storage_{uuid.uuid4().hex}.json")
        
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.url = f"https://api.example.com/data/{uuid.uuid4().hex}"
        self.token = f"TOKEN_{uuid.uuid4().hex}"
        self.chat_id = str(random.randint(100000, 999999))
        self.severity = random.choice(["INFO", "WARNING", "CRITICAL"])
        self.threshold = round(random.uniform(1.0, 100.0), 2)
        self.channels = ["telegram", "webhook"]

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

    def test_process_event_sink_trigger_integration(self):
        result = market_portfolio_alert_event_sink.process_event_sink_trigger(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            severity_level=self.severity,
            min_threshold=self.threshold,
            channels=self.channels
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("symbol"), self.symbol)
        self.assertIn("dispatch_result", result)

        self.assertTrue(os.path.exists(self.storage_file), "Storage file must be created by integration sink")
        
        with open(self.storage_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data.get("symbol"), self.symbol)
            self.assertEqual(data.get("status"), "processed")

    def test_route_and_sink_alerts_integration(self):
        res = market_portfolio_alert_event_sink.route_and_sink_alerts(
            storage=self.storage_file,
            symbol=self.symbol,
            url=self.url,
            token=self.token,
            chat_id=self.chat_id,
            severity=self.severity,
            threshold=self.threshold,
            channels=self.channels
        )
        self.assertIsNotNone(res)

    def test_load_sink_stream_data_integration(self):
        res = market_portfolio_alert_event_sink.load_sink_stream_data(self.storage_file)
        self.assertIsInstance(res, (dict, list, type(None)))

if __name__ == "__main__":
    unittest.main()