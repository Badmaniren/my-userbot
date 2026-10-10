import unittest
import os
import json
import uuid
import random
from skills.market_portfolio_realtime_anomaly_reactor import market_portfolio_realtime_anomaly_reactor

class TestMarketPortfolioRealtimeAnomalyReactorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = f"test_output_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)
        self.output_file = os.path.join(self.test_dir, f"report_{uuid.uuid4().hex}.json")

        self.session_id = str(uuid.uuid4())
        self.ticker = f"TICK_{random.randint(1000, 9999)}"
        self.exchange = f"EX_{random.choice(['NYSE', 'NASDAQ', 'LSE'])}"

        self.payload = {
            "session_id": self.session_id,
            "ticker": self.ticker,
            "price": round(random.uniform(10.0, 1000.0), 2),
            "volume": random.randint(100, 50000)
        }
        self.context = {
            "session_id": self.session_id,
            "ticker": self.ticker,
            "environment": "integration_test"
        }

    def tearDown(self):
        if os.path.exists(self.output_file):
            try:
                os.remove(self.output_file)
            except OSError:
                pass
        if os.path.exists(self.test_dir):
            try:
                os.rmdir(self.test_dir)
            except OSError:
                pass

    def test_reactor_integration_flow(self):
        result = market_portfolio_realtime_anomaly_reactor(
            context=self.context,
            stream_source=self.output_file,
            payload=self.payload,
            exchange=self.exchange,
            ticker=self.ticker
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "success")
        self.assertIn("ingest_result", result)
        self.assertIn("detection_result", result)
        self.assertEqual(result.get("payload"), self.payload)

        self.assertTrue(os.path.exists(self.output_file))

        with open(self.output_file, "r", encoding="utf-8") as f:
            file_data = json.load(f)

        self.assertEqual(file_data.get("session_id"), self.session_id)
        self.assertIn("result", file_data)
        self.assertEqual(file_data["result"]["status"], "success")

if __name__ == "__main__":
    unittest.main()