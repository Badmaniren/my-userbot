import unittest
import io
import uuid
import random
from skills.market_insider_activity_tracker import (
    MarketInsiderActivityTracker,
    MarketInsiderActivityTrackerModuleAPI,
    MarketInsiderActivityTrackerModuleIdempotentProxy
)

class TestMarketInsiderActivityTrackerIntegration(unittest.TestCase):
    def setUp(self):
        self.tracker = MarketInsiderActivityTracker()
        self.api = MarketInsiderActivityTrackerModuleAPI()
        self.proxy = MarketInsiderActivityTrackerModuleIdempotentProxy()

    def test_tracker_anomaly_flow(self):
        random_suffix = uuid.uuid4().hex
        payload_content = f"market data stream anomaly_detected {random_suffix}".encode("utf-8")
        stream = io.BytesIO(payload_content)

        result = self.tracker.analyze_activity(stream)

        self.assertEqual(result["status"], "ALERT")
        self.assertIn("signature", result)
        self.assertTrue(isinstance(result["signature"], str))
        self.assertTrue(len(result["signature"]) > 0)

    def test_tracker_normal_flow(self):
        random_suffix = uuid.uuid4().hex
        payload_content = f"regular market volume steady {random_suffix}".encode("utf-8")
        stream = io.BytesIO(payload_content)

        result = self.tracker.analyze_activity(stream)

        self.assertEqual(result["status"], "NORMAL")
        self.assertIn("signature", result)

    def test_tracker_empty_stream_raises(self):
        with self.assertRaises(ValueError):
            self.tracker.analyze_activity(None)
        
        with self.assertRaises(ValueError):
            self.tracker.analyze_activity(io.BytesIO(b""))

    def test_api_and_proxy_integration_anomaly(self):
        random_ticker = f"TICK_{random.randint(1000, 9999)}_" + uuid.uuid4().hex[:6]
        random_volume = random.uniform(500001.0, 2000000.0)
        random_multiplier = random.uniform(5.1, 10.0)

        payload = {
            "ticker_id": random_ticker,
            "volume": random_volume,
            "anomaly_multiplier": random_multiplier
        }

        api_result = self.api.track_activity(payload)
        proxy_result = self.proxy.track_activity(payload)

        self.assertTrue(api_result["anomaly_detected"])
        self.assertEqual(api_result["ticker_id"], random_ticker)
        self.assertEqual(api_result["volume"], random_volume)
        self.assertIn("signature", api_result)

        self.assertEqual(api_result["anomaly_detected"], proxy_result["anomaly_detected"])
        self.assertEqual(api_result["ticker_id"], proxy_result["ticker_id"])

    def test_api_and_proxy_integration_normal(self):
        random_ticker = f"TICK_{random.randint(1000, 9999)}_" + uuid.uuid4().hex[:6]
        random_volume = random.uniform(10.0, 499999.0)
        random_multiplier = random.uniform(0.1, 4.9)

        payload = {
            "ticker_id": random_ticker,
            "volume": random_volume,
            "anomaly_multiplier": random_multiplier
        }

        api_result = self.api.track_activity(payload)

        self.assertFalse(api_result["anomaly_detected"])
        self.assertEqual(api_result["ticker_id"], random_ticker)
        self.assertEqual(api_result["volume"], random_volume)
        self.assertIn("signature", api_result)

if __name__ == "__main__":
    unittest.main()