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
        self.tracker = MarketInsiderActivityTracker(env="test_integration")
        self.api = MarketInsiderActivityTrackerModuleAPI(env="test_integration")
        self.proxy = MarketInsiderActivityTrackerModuleIdempotentProxy(env="test_integration")

        self.random_ticker = f"TICK_{uuid.uuid4().hex[:6].upper()}"
        self.random_volume = float(random.randint(1000, 1000000))
        self.random_multiplier = round(random.uniform(1.0, 10.0), 2)

    def test_analyze_activity_normal_flow(self):
        normal_data = f"market_data_{uuid.uuid4().hex}".encode("utf-8")
        stream = io.BytesIO(normal_data)
        
        result = self.tracker.analyze_activity(stream)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "NORMAL")
        self.assertIn("signature", result)
        self.assertEqual(len(result.get("signature")), 32)

    def test_analyze_activity_anomaly_flow(self):
        anomaly_data = f"anomaly_detected_{uuid.uuid4().hex}".encode("utf-8")
        stream = io.BytesIO(anomaly_data)
        
        result = self.tracker.analyze_activity(stream)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "ALERT")
        self.assertIn("signature", result)
        self.assertEqual(len(result.get("signature")), 32)

    def test_analyze_activity_empty_stream_raises_error(self):
        empty_stream = io.BytesIO(b"")
        
        with self.assertRaises(ValueError) as context:
            self.tracker.analyze_activity(empty_stream)

        self.assertEqual(str(context.exception), "Empty stream")

    def test_analyze_activity_invalid_input(self):
        with self.assertRaises(TypeError):
            self.tracker.analyze_activity(12345)

    def test_module_api_track_activity_payload(self):
        payload = {
            "ticker_id": self.random_ticker,
            "volume": self.random_volume,
            "anomaly_multiplier": self.random_multiplier
        }
        
        result = self.api.track_activity(payload)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("ticker_id"), self.random_ticker)
        self.assertEqual(result.get("volume"), self.random_volume)
        self.assertIn("anomaly_detected", result)
        self.assertIn("signature", result)
        
        expected_anomaly = self.random_volume > 500000.0 or self.random_multiplier > 5.0
        self.assertEqual(result.get("anomaly_detected"), expected_anomaly)

    def test_module_api_invalid_payloads(self):
        with self.assertRaises(TypeError):
            self.api.track_activity(["invalid_type"])
        with self.assertRaises(ValueError):
            self.api.track_activity({"ticker_id": ""})

    def test_idempotent_proxy_equivalence(self):
        payload = {
            "ticker_id": self.random_ticker,
            "volume": self.random_volume,
            "anomaly_multiplier": self.random_multiplier
        }
        
        api_result = self.api.track_activity(payload)
        proxy_result = self.proxy.track_activity(payload)
        
        self.assertEqual(api_result.get("ticker_id"), proxy_result.get("ticker_id"))
        self.assertEqual(api_result.get("volume"), proxy_result.get("volume"))
        self.assertEqual(api_result.get("anomaly_detected"), proxy_result.get("anomaly_detected"))
        self.assertNotEqual(api_result.get("signature"), proxy_result.get("signature"))

if __name__ == "__main__":
    unittest.main()