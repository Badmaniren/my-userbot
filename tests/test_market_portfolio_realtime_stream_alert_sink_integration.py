import unittest
import os
import tempfile
import uuid
import random
from skills.market_portfolio_realtime_stream_alert_sink import market_portfolio_realtime_stream_alert_sink

class TestMarketPortfolioRealtimeStreamAlertSinkIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.output_path = os.path.join(self.test_dir.name, f"stream_output_{uuid.uuid4().hex}.json")
        self.storage_path = os.path.join(self.test_dir.name, f"storage_{uuid.uuid4().hex}.db")
        
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.payload = {
            "symbol": self.symbol,
            "price": round(random.uniform(10.0, 1000.0), 2),
            "volume": random.randint(100, 10000),
            "timestamp": uuid.uuid4().int
        }
        self.url = f"https://api.telegram.org/bot{uuid.uuid4().hex}/sendMessage"
        self.token = uuid.uuid4().hex
        self.chat_id = str(random.randint(100000, 999999))
        self.severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.threshold = round(random.uniform(1.0, 50.0), 2)
        self.channels = ["telegram", "webhook"]

    def tearDown(self):
        self.test_dir.cleanup()

    def test_market_portfolio_realtime_stream_alert_sink_integration(self):
        result = market_portfolio_realtime_stream_alert_sink(
            payload=self.payload,
            output_path=self.output_path,
            storage=self.storage_path,
            url=self.url,
            token=self.token,
            chat_id=self.chat_id,
            severity=self.severity,
            threshold=self.threshold,
            channels=self.channels,
            symbol=self.symbol
        )

        self.assertIsInstance(result, dict)
        self.assertIn("sink_result", result)
        self.assertIn("route_result", result)

        self.assertTrue(
            os.path.exists(self.output_path),
            f"Integration failure: Output stream file {self.output_path} was not created."
        )

        file_size = os.path.getsize(self.output_path)
        self.assertGreater(file_size, 0, "Integration failure: Output stream file is empty.")

if __name__ == "__main__":
    unittest.main()