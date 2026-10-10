import unittest
import os
import uuid
import tempfile
from skills.market_portfolio_stream_alert_bridge import (
    process_stream_and_dispatch,
    evaluate_stream_anomaly_bridge,
    process_stream_and_dispatch_alert
)

class TestMarketPortfolioStreamAlertBridgeIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.output_path = os.path.join(self.test_dir.name, f"stream_out_{uuid.uuid4().hex}.json")
        self.storage_file = os.path.join(self.test_dir.name, f"storage_{uuid.uuid4().hex}.json")
        
        self.payload = {
            "event_id": str(uuid.uuid4()),
            "symbol": self.symbol,
            "price": 150.25,
            "volume": 1000,
            "anomaly_detected": True
        }
        
        self.url = "https://api.test-target-endpoint.local/webhook"
        self.telegram_token = "test_token_123456:ABC-DEF1234abcd"
        self.chat_id = "@test_channel_alerts"
        self.severity_level = "HIGH"
        self.min_threshold = 5.0
        self.channels = ["telegram", "webhook"]
        self.context = {"env": "test", "session_id": str(uuid.uuid4())}
        self.stream_source = "websocket://market.feed.local/v1/stream"
        self.alert_message_template = "PRICE_SPIKE_ALERT"

    def tearDown(self):
        self.test_dir.cleanup()

    def test_process_stream_and_dispatch_integration(self):
        result = process_stream_and_dispatch(
            payload=self.payload,
            output_path=self.output_path,
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            severity_level=self.severity_level,
            min_threshold=self.min_threshold,
            channels=self.channels
        )

        self.assertIn("stream_processing", result)
        self.assertIn("alert_dispatch_status", result)
        self.assertTrue(result["alert_dispatched"])
        self.assertTrue(os.path.exists(self.output_path))

    def test_evaluate_stream_anomaly_bridge_integration(self):
        result = evaluate_stream_anomaly_bridge(
            context=self.context,
            stream_source=self.stream_source,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            alert_message_template=self.alert_message_template
        )

        self.assertIsInstance(result, dict)
        self.assertIn("source_id", result)

    def test_process_stream_and_dispatch_alert_integration(self):
        result = process_stream_and_dispatch_alert(
            context=self.context,
            stream_source=self.stream_source,
            payload=self.payload,
            output_path=self.output_path,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            severity_level=self.severity_level,
            min_threshold=self.min_threshold,
            channels=self.channels
        )

        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("event_id"), self.payload["event_id"])
        self.assertTrue(result.get("dispatched"))
        self.assertIn("stream_processing", result)
        self.assertIn("alert_dispatch_status", result)
        self.assertTrue(os.path.exists(self.output_path))

if __name__ == "__main__":
    unittest.main()