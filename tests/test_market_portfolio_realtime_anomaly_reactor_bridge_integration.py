import unittest
import os
import json
import uuid
import tempfile
from skills.market_portfolio_realtime_anomaly_reactor_bridge import market_portfolio_realtime_anomaly_reactor_bridge

class TestMarketPortfolioRealtimeAnomalyReactorBridgeIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.random_ticker = f"TICKER_{uuid.uuid4().hex[:6].upper()}"
        self.output_filename = f"reaction_{uuid.uuid4().hex}.json"
        self.output_path = os.path.join(self.test_dir.name, self.output_filename)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_real_integration_flow(self):
        payload = {
            "source": "integration_test_stream",
            "data": uuid.uuid4().hex
        }

        result = market_portfolio_realtime_anomaly_reactor_bridge(
            payload_or_context=payload,
            output_path=self.output_path,
            ticker=self.random_ticker
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "reacted")
        self.assertIn("ingested_data", result)
        self.assertIn("detection_result", result)

        self.assertTrue(os.path.exists(self.output_path))

        with open(self.output_path, "r", encoding="utf-8") as f:
            file_data = json.load(f)

        self.assertEqual(file_data.get("status"), "reacted")
        self.assertIn("detection_result", file_data)
        self.assertIn("ingested_data", file_data)

if __name__ == "__main__":
    unittest.main()