import unittest
import uuid
import random
import io
from skills.market_insider_activity_tracker import (
    MarketInsiderActivityTracker,
    MarketInsiderActivityTrackerModuleAPI,
    MarketInsiderActivityTrackerModuleIdempotentProxy,
    market_insider_activity_tracker
)

class TestMarketInsiderActivityTrackerIntegration(unittest.TestCase):
    def setUp(self):
        self.tracker = MarketInsiderActivityTracker()
        self.random_ticker = f"TICKER_{uuid.uuid4().hex[:8].upper()}"
        self.random_volume = float(random.randint(1000, 1000000))
        self.random_multiplier = round(random.uniform(1.0, 10.0), 2)

    def test_tracker_stream_normal_and_anomaly(self):
        normal_stream = io.BytesIO(b"normal market stream data")
        result_normal = self.tracker.analyze_activity(normal_stream)
        self.assertEqual(result_normal["status"], "NORMAL")
        self.assertIn("signature", result_normal)

        anomaly_stream = io.BytesIO(b"critical anomaly detected in stream")
        result_anomaly = self.tracker.analyze_activity(anomaly_stream)
        self.assertEqual(result_anomaly["status"], "ALERT")
        self.assertIn("signature", result_anomaly)

    def test_tracker_stream_exceptions(self):
        with self.assertRaises(ValueError):
            self.tracker.analyze_activity(None)
        
        empty_stream = io.BytesIO(b"")
        with self.assertRaises(ValueError):
            self.tracker.analyze_activity(empty_stream)

    def test_module_api_payload_processing(self):
        payload = {
            "ticker_id": self.random_ticker,
            "volume": self.random_volume,
            "anomaly_multiplier": self.random_multiplier
        }
        
        result = MarketInsiderActivityTrackerModuleAPI.track_activity(payload)
        
        self.assertEqual(result["ticker_id"], self.random_ticker)
        self.assertEqual(result["volume"], self.random_volume)
        self.assertIsInstance(result["anomaly_detected"], bool)
        self.assertIn("signature", result)

        expected_anomaly = self.random_volume > 500000.0 or self.random_multiplier > 5.0
        self.assertEqual(result["anomaly_detected"], expected_anomaly)

    def test_idempotent_proxy_and_globals_integration(self):
        payload = {
            "ticker_id": f"PROXY_{uuid.uuid4().hex[:6]}",
            "volume": "invalid_volume",
            "anomaly_multiplier": "invalid_mult"
        }
        
        proxy_result = MarketInsiderActivityTrackerModuleIdempotentProxy.track_activity(payload)
        self.assertEqual(proxy_result["volume"], 0.0)
        self.assertFalse(proxy_result["anomaly_detected"])

        global_func = globals()["market_insider_activity_tracker"].track_activity
        global_result = global_func({"ticker_id": self.random_ticker, "volume": 600000.0})
        self.assertTrue(global_result["anomaly_detected"])
        self.assertEqual(global_result["ticker_id"], self.random_ticker)

if __name__ == "__main__":
    unittest.main()