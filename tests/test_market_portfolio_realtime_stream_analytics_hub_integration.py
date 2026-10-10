import unittest
import os
import uuid
import tempfile
from skills.market_portfolio_realtime_stream_analytics_hub import (
    MarketPortfolioRealtimeStreamAnalyticsHub,
    process_realtime_stream_hub
)

class TestMarketPortfolioRealtimeStreamAnalyticsHubIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.test_dir.name, f"storage_{uuid.uuid4().hex}.json")
        self.output_path = os.path.join(self.test_dir.name, f"output_{uuid.uuid4().hex}.json")
        self.stream_source = f"wss://market-stream.test/{uuid.uuid4().hex}"
        self.symbol = f"TICKER_{uuid.uuid4().hex[:6].upper()}"
        
        with open(self.storage_file, "w") as f:
            f.write("{}")

    def tearDown(self):
        self.test_dir.cleanup()

    def test_hub_composition_and_processing(self):
        hub = MarketPortfolioRealtimeStreamAnalyticsHub(self.storage_file, self.stream_source)
        
        context = {
            "session_id": uuid.uuid4().hex,
            "symbol": self.symbol,
            "timestamp": uuid.uuid4().int
        }
        
        stream_result = hub.process_stream(context)
        self.assertIsInstance(stream_result, dict)

        payload = {
            "data": uuid.uuid4().hex,
            "metrics_id": uuid.uuid4().hex
        }
        audit_result = hub.audit_stream_data(payload, self.output_path)
        self.assertIsInstance(audit_result, dict)

        metrics = hub.get_realtime_metrics(self.symbol)
        self.assertIsInstance(metrics, dict)

        performance = hub.evaluate_stream_performance(self.symbol)
        self.assertIsInstance(performance, dict)

        hub_function_result = process_realtime_stream_hub(self.output_path, self.storage_file, self.symbol)
        self.assertIsInstance(hub_function_result, dict)
        self.assertEqual(hub_function_result["output_path"], self.output_path)
        self.assertEqual(hub_function_result["storage_file"], self.storage_file)
        self.assertIn("metrics", hub_function_result)
        self.assertEqual(hub_function_result["metrics"]["symbol"], self.symbol)

if __name__ == "__main__":
    unittest.main()