import unittest
import os
import uuid
import random
import tempfile

from skills.market_portfolio_realtime_stream_dashboard_bridge import (
    MarketPortfolioRealtimeStreamDashboardBridge,
    market_portfolio_realtime_stream_dashboard_bridge,
    process_dashboard_stream_bridge,
    process_dashboard_bridge_stream
)


class TestMarketPortfolioRealtimeStreamDashboardBridgeIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.temp_dir.name, f"test_storage_{uuid.uuid4()}.db")
        self.output_path = os.path.join(self.temp_dir.name, f"audit_output_{uuid.uuid4()}.json")
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.bridge = MarketPortfolioRealtimeStreamDashboardBridge(
            storage_file=self.storage_file,
            stream_source="test_stream"
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_bridge_class_process_and_audit(self):
        random_val = random.uniform(10.0, 500.0)
        context = {
            "metrics": {
                "symbol": self.symbol,
                "price": random_val
            }
        }
        
        result = self.bridge.process_and_bridge(context=context, output_path=self.output_path)
        
        self.assertIsInstance(result, dict)
        self.assertTrue(os.path.exists(self.output_path))

    def test_bridge_functional_wrapper(self):
        random_threshold = random.randint(1, 100)
        payload = {
            "event_id": str(uuid.uuid4()),
            "value": random_threshold
        }
        
        res = market_portfolio_realtime_stream_dashboard_bridge(
            storage_file=self.storage_file,
            stream_source="functional_stream",
            output_path=self.output_path,
            symbol=self.symbol,
            threshold=random_threshold,
            payload=payload,
            context={"init": True}
        )
        
        self.assertIn("analytics", res)
        self.assertIn("alert_sink", res)
        self.assertIsInstance(res["analytics"], dict)

    def test_process_dashboard_stream_bridge(self):
        res = process_dashboard_stream_bridge(
            storage_file=self.storage_file,
            symbol=self.symbol
        )
        self.assertIn("metrics", res)

    def test_process_dashboard_bridge_stream(self):
        random_price = random.randint(50, 5000)
        payload = {"price": random_price, "id": str(uuid.uuid4())}
        
        res = process_dashboard_bridge_stream(
            storage=self.storage_file,
            stream_source="stream_src",
            payload=payload,
            output_path=self.output_path,
            symbol=self.symbol
        )
        
        self.assertIsInstance(res, dict)
        metrics = self.bridge.get_realtime_metrics(self.symbol)
        self.assertIsInstance(metrics, (dict, type(None)))


if __name__ == "__main__":
    unittest.main()