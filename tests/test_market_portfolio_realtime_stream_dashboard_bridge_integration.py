import unittest
import os
import uuid
import random
import tempfile

from skills.market_portfolio_realtime_stream_analytics_hub import (
    MarketPortfolioRealtimeStreamAnalyticsHub,
    process_realtime_stream_hub
)
from skills.market_portfolio_realtime_stream_alert_sink import (
    market_portfolio_realtime_stream_alert_sink,
    process_stream_and_dispatch_alerts
)
from skills.market_portfolio_realtime_stream_dashboard_bridge import (
    process_dashboard_bridge_stream,
    MarketPortfolioRealtimeStreamDashboardBridge
)


class TestMarketPortfolioRealtimeStreamDashboardBridgeIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.test_dir.name, f"storage_{uuid.uuid4()}.db")
        self.output_path = os.path.join(self.test_dir.name, f"output_{uuid.uuid4()}.json")
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.stream_source = f"source_{uuid.uuid4()}"
        
        self.payload = {
            "event_id": str(uuid.uuid4()),
            "value": round(random.uniform(100.0, 1500.0), 2),
            "volume": random.randint(10, 5000),
            "status": "active"
        }
        
        self.url = f"https://api.mock-dashboard-{uuid.uuid4()}.local/v1/stream"
        self.token = str(uuid.uuid4())
        self.chat_id = str(random.randint(100000, 999999))
        self.severity = random.choice(["INFO", "WARNING", "CRITICAL"])
        self.threshold = round(random.uniform(50.0, 500.0), 2)
        self.channels = ["console", "webhook"]
        self.context = {
            "session_id": str(uuid.uuid4()),
            "metrics": self.payload
        }

    def tearDown(self):
        self.test_dir.cleanup()

    def test_end_to_end_realtime_stream_dashboard_bridge(self):
        hub = MarketPortfolioRealtimeStreamAnalyticsHub(
            storage_file=self.storage_file,
            stream_source=self.stream_source
        )
        
        hub_processed_result = hub.process_stream(self.context)
        self.assertIsInstance(hub_processed_result, dict)

        metrics = hub.get_realtime_metrics(self.symbol)
        self.assertIsInstance(metrics, dict)

        performance = hub.evaluate_stream_performance(self.symbol)
        self.assertIsInstance(performance, dict)

        audited_data = hub.audit_stream_data(self.payload, self.output_path)
        self.assertIsInstance(audited_data, dict)
        self.assertTrue(os.path.exists(self.output_path))

        hub_helper_result = process_realtime_stream_hub(
            output_path=self.output_path,
            storage_file=self.storage_file,
            symbol=self.symbol
        )
        self.assertIsInstance(hub_helper_result, dict)

        alert_result = market_portfolio_realtime_stream_alert_sink(
            payload=self.payload,
            output_path=self.output_path,
            storage=self.storage_file,
            url=self.url,
            token=self.token,
            chat_id=self.chat_id,
            severity=self.severity,
            threshold=self.threshold,
            channels=self.channels,
            symbol=self.symbol
        )
        self.assertIsNotNone(alert_result)

        dispatch_result = process_stream_and_dispatch_alerts(
            context=self.context,
            stream_source=self.stream_source,
            payload=self.payload,
            output_path=self.output_path,
            symbol=self.symbol,
            url=self.url,
            token=self.token,
            chat_id=self.chat_id,
            storage=self.storage_file,
            severity=self.severity,
            threshold=self.threshold,
            channels=self.channels
        )
        self.assertIsNotNone(dispatch_result)

        bridge_instance = MarketPortfolioRealtimeStreamDashboardBridge(
            storage=self.storage_file,
            stream_source=self.stream_source
        )
        bridge_metrics = bridge_instance.process_and_bridge(self.context, self.output_path)
        self.assertIsInstance(bridge_metrics, dict)

        functional_bridge_res = process_dashboard_bridge_stream(
            storage=self.storage_file,
            stream_source=self.stream_source,
            payload=self.payload,
            output_path=self.output_path,
            symbol=self.symbol,
            url=self.url,
            token=self.token
        )
        self.assertIsInstance(functional_bridge_res, dict)
        self.assertTrue(os.path.exists(self.output_path))


if __name__ == "__main__":
    unittest.main()