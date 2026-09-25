import unittest
from unittest.mock import patch
import io
import uuid
import random
import string
from skills.market_insider_activity_tracker import (
    MarketInsiderActivityTracker,
    MarketInsiderActivityTrackerModuleAPI,
    MarketInsiderActivityTrackerModuleIdempotentProxy,
)


class TestMarketInsiderActivityTracker(unittest.TestCase):

    def setUp(self):
        self.tracker_id = uuid.uuid4().hex
        self.tracker = MarketInsiderActivityTracker(id=self.tracker_id)

    def test_analyze_activity_none_stream(self):
        with self.assertRaises(ValueError):
            self.tracker.analyze_activity(None)

    def test_analyze_activity_empty_stream(self):
        empty_stream = io.BytesIO(b"")
        with self.assertRaises(ValueError):
            self.tracker.analyze_activity(empty_stream)

    def test_analyze_activity_normal(self):
        random_payload = "".join(random.choices(string.ascii_letters + string.digits, k=32)).encode("utf-8")
        stream = io.BytesIO(random_payload)
        result = self.tracker.analyze_activity(stream)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "NORMAL")
        self.assertIn("signature", result)

    def test_analyze_activity_anomaly(self):
        anomaly_keyword = "".join(random.choices(string.ascii_lowercase, k=5)).encode("utf-8")
        stream_content = anomaly_keyword + b"_anomaly_" + uuid.uuid4().hex.encode("utf-8")
        stream = io.BytesIO(stream_content)
        
        with patch("uuid.uuid4") as mock_uuid:
            mock_signature = uuid.uuid4().hex
            mock_uuid.return_value.hex = mock_signature
            result = self.tracker.analyze_activity(stream)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "ALERT")
        self.assertEqual(result.get("signature"), mock_signature)


class TestMarketInsiderActivityTrackerModuleAPI(unittest.TestCase):

    def test_track_activity_invalid_payload_type(self):
        invalid_payload = "".join(random.choices(string.ascii_letters, k=10))
        result = MarketInsiderActivityTrackerModuleAPI.track_activity(invalid_payload)
        
        self.assertIsInstance(result, dict)
        self.assertFalse(result.get("anomaly_detected"))
        self.assertIsNone(result.get("ticker_id"))

    def test_track_activity_normal_volume(self):
        ticker = "TICK_" + uuid.uuid4().hex[:6].upper()
        volume = random.uniform(100.0, 499999.0)
        multiplier = random.uniform(1.0, 4.0)
        
        payload = {
            "ticker_id": ticker,
            "volume": volume,
            "anomaly_multiplier": multiplier
        }
        
        result = MarketInsiderActivityTrackerModuleAPI.track_activity(payload)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("ticker_id"), ticker)
        self.assertEqual(result.get("volume"), float(volume))
        self.assertFalse(result.get("anomaly_detected"))
        self.assertIn("signature", result)

    def test_track_activity_anomaly_high_volume(self):
        ticker = "TICK_" + uuid.uuid4().hex[:6].upper()
        volume = random.uniform(500001.0, 2000000.0)
        multiplier = random.uniform(0.5, 3.0)
        
        payload = {
            "ticker_id": ticker,
            "volume": volume,
            "anomaly_multiplier": multiplier
        }
        
        result = MarketInsiderActivityTrackerModuleAPI.track_activity(payload)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("ticker_id"), ticker)
        self.assertTrue(result.get("anomaly_detected"))

    def test_track_activity_anomaly_high_multiplier(self):
        ticker = "TICK_" + uuid.uuid4().hex[:6].upper()
        volume = random.uniform(10.0, 1000.0)
        multiplier = random.uniform(5.1, 20.0)
        
        payload = {
            "ticker_id": ticker,
            "volume": volume,
            "anomaly_multiplier": multiplier
        }
        
        result = MarketInsiderActivityTrackerModuleAPI.track_activity(payload)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("ticker_id"), ticker)
        self.assertTrue(result.get("anomaly_detected"))

    def test_track_activity_corrupted_numeric_fields(self):
        ticker = "TICK_" + uuid.uuid4().hex[:6].upper()
        payload = {
            "ticker_id": ticker,
            "volume": "corrupted_volume_string",
            "anomaly_multiplier": "bad_multiplier"
        }
        
        result = MarketInsiderActivityTrackerModuleAPI.track_activity(payload)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("ticker_id"), ticker)
        self.assertEqual(result.get("volume"), 0.0)
        self.assertFalse(result.get("anomaly_detected"))


class TestMarketInsiderActivityTrackerModuleIdempotentProxy(unittest.TestCase):

    def test_proxy_alias_presence(self):
        self.assertEqual(
            MarketInsiderActivityTrackerModuleIdempotentProxy,
            MarketInsiderActivityTrackerModuleAPI
        )
        
        ticker = uuid.uuid4().hex
        payload = {"ticker_id": ticker, "volume": 10.0}
        res_proxy = MarketInsiderActivityTrackerModuleIdempotentProxy.track_activity(payload)
        res_api = MarketInsiderActivityTrackerModuleAPI.track_activity(payload)
        
        self.assertEqual(res_proxy.get("ticker_id"), res_api.get("ticker_id"))
        self.assertEqual(res_proxy.get("anomaly_detected"), res_api.get("anomaly_detected"))


if __name__ == "__main__":
    unittest.main()