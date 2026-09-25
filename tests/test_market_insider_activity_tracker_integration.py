import unittest
import uuid
import random
import io
from skills.market_insider_activity_tracker import (
    MarketInsiderActivityTracker,
    MarketInsiderActivityTrackerModuleAPI,
    market_insider_activity_tracker
)

class TestMarketInsiderActivityTrackerIntegration(unittest.TestCase):
    def setUp(self):
        self.tracker = MarketInsiderActivityTracker()
        self.api = MarketInsiderActivityTrackerModuleAPI()
        self.random_ticker = f"TICKER_{uuid.uuid4().hex[:6].upper()}"
        self.random_volume = float(random.randint(100000, 1000000))
        self.random_multiplier = round(random.uniform(1.0, 10.0), 2)

    def test_tracker_stream_normal_and_anomaly(self):
        normal_stream = io.BytesIO(b"normal market transactions stream data")
        result_normal = self.tracker.analyze_activity(normal_stream)
        self.assertEqual(result_normal["status"], "NORMAL")
        self.assertIn("signature", result_normal)
        self.assertTrue(uuid.UUID(result_normal["signature"], version=4))

        anomaly_stream = io.BytesIO(b"critical anomaly detected in stream")
        result_anomaly = self.tracker.analyze_activity(anomaly_stream)
        self.assertEqual(result_anomaly["status"], "ALERT")
        self.assertIn("signature", result_anomaly)
        self.assertTrue(uuid.UUID(result_anomaly["signature"], version=4))

    def test_tracker_stream_exceptions(self):
        with self.assertRaises(ValueError):
            self.tracker.analyze_activity(None)
        
        empty_stream = io.BytesIO(b"")
        with self.assertRaises(ValueError):
            self.tracker.analyze_activity(empty_stream)

    def test_api_payload_processing_and_idempotency(self):
        payload = {
            "ticker_id": self.random_ticker,
            "volume": self.random_volume,
            "anomaly_multiplier": self.random_multiplier
        }

        result = MarketInsiderActivityTrackerModuleAPI.track_activity(payload)
        
        self.assertEqual(result["ticker_id"], self.random_ticker)
        self.assertEqual(result["volume"], self.random_volume)
        self.assertIn("anomaly_detected", result)
        self.assertIn("signature", result)
        self.assertTrue(uuid.UUID(result["signature"], version=4))

        expected_anomaly = self.random_volume > 500000.0 or self.random_multiplier > 5.0
        self.assertEqual(result["anomaly_detected"], expected_anomaly)

        global_callable = globals().get("market_insider_activity_tracker")
        self.assertIsNotNone(global_callable)
        
        global_result = global_callable.track_activity(payload)
        self.assertEqual(global_result["ticker_id"], self.random_ticker)
        self.assertEqual(global_result["volume"], self.random_volume)

    def test_api_malformed_payload_handling(self):
        malformed_payload = {
            "ticker_id": self.random_ticker,
            "volume": "invalid_vol",
            "anomaly_multiplier": "invalid_mult"
        }

        result = self.api.track_activity(malformed_payload)
        self.assertEqual(result["ticker_id"], self.random_ticker)
        self.assertEqual(result["volume"], 0.0)
        self.assertFalse(result["anomaly_detected"])
        self.assertIn("signature", result)

        non_dict_payload = "not_a_dictionary"
        fallback_result = self.api.track_activity(non_dict_payload)
        self.assertIsNone(fallback_result["ticker_id"])
        self.assertEqual(fallback_result["volume"], 0.0)
        self.assertFalse(fallback_result["anomaly_detected"])

if __name__ == "__main__":
    unittest.main()