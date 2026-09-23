import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
from skills.market_insider_activity_tracker import (
    MarketInsiderActivityTracker,
    MarketInsiderActivityTrackerModuleAPI,
    MarketInsiderActivityTrackerModuleIdempotentProxy
)

class TestMarketInsiderActivityTracker(unittest.TestCase):

    def setUp(self):
        self.random_dep_key = uuid.uuid4().hex
        self.random_dep_val = uuid.uuid4().hex
        self.tracker = MarketInsiderActivityTracker(**{self.random_dep_key: self.random_dep_val})

    def test_init_stores_deps(self):
        self.assertEqual(self.tracker.deps.get(self.random_dep_key), self.random_dep_val)

    def test_analyze_activity_empty_stream_raises_value_error(self):
        empty_stream = io.BytesIO(b"")
        with self.assertRaises(ValueError) as ctx:
            self.tracker.analyze_activity(empty_stream)
        self.assertEqual(str(ctx.exception), "Empty stream")

    def test_analyze_activity_invalid_stream_type_raises_type_error(self):
        with self.assertRaises(TypeError):
            self.tracker.analyze_activity(None)
        with self.assertRaises(TypeError):
            self.tracker.analyze_activity("not_a_stream")

    def test_analyze_activity_stream_read_error_raises_value_error(self):
        failing_stream = MagicMock()
        failing_stream.read.side_effect = IOError("Disk read error")
        with self.assertRaises(ValueError) as ctx:
            self.tracker.analyze_activity(failing_stream)
        self.assertIn("Failed to read raw data stream", str(ctx.exception))

    def test_analyze_activity_unsupported_content_type_raises_type_error(self):
        invalid_content_stream = MagicMock()
        invalid_content_stream.read.return_value = 12345
        with self.assertRaises(TypeError) as ctx:
            self.tracker.analyze_activity(invalid_content_stream)
        self.assertIn("Stream content must be bytes or string", str(ctx.exception))

    def test_analyze_activity_string_stream(self):
        str_stream = io.StringIO("str_anomaly_data")
        result = self.tracker.analyze_activity(str_stream)
        self.assertEqual(result.get("status"), "ALERT")

        normal_str_stream = io.StringIO("normal_string_data")
        result_normal = self.tracker.analyze_activity(normal_str_stream)
        self.assertEqual(result_normal.get("status"), "NORMAL")

    def test_analyze_activity_detects_anomaly(self):
        random_prefix = uuid.uuid4().hex.encode('utf-8')
        anomaly_payload = random_prefix + b"anomaly" + uuid.uuid4().hex.encode('utf-8')
        stream = io.BytesIO(anomaly_payload)
        
        result = self.tracker.analyze_activity(stream)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "ALERT")
        self.assertIn("signature", result)
        self.assertEqual(len(result.get("signature")), 32)

    def test_analyze_activity_returns_normal(self):
        random_normal_data = uuid.uuid4().hex.encode('utf-8')
        stream = io.BytesIO(random_normal_data)
        
        result = self.tracker.analyze_activity(stream)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "NORMAL")
        self.assertIn("signature", result)
        self.assertEqual(len(result.get("signature")), 32)


class TestMarketInsiderActivityTrackerModuleAPI(unittest.TestCase):

    def test_api_init(self):
        api_obj = MarketInsiderActivityTrackerModuleAPI("arg1", key1="val1")
        self.assertEqual(api_obj.config["args"], ["arg1"])
        self.assertEqual(api_obj.config["kwargs"], {"key1": "val1"})

    def test_track_activity_invalid_payload_type(self):
        with self.assertRaises(TypeError):
            MarketInsiderActivityTrackerModuleAPI.track_activity("not_a_dict")

    def test_track_activity_missing_ticker_id(self):
        with self.assertRaises(ValueError):
            MarketInsiderActivityTrackerModuleAPI.track_activity({})
        with self.assertRaises(ValueError):
            MarketInsiderActivityTrackerModuleAPI.track_activity({"ticker_id": "  "})

    def test_track_activity_invalid_volume(self):
        with self.assertRaises(ValueError):
            MarketInsiderActivityTrackerModuleAPI.track_activity({"ticker_id": "AAPL", "volume": -10.0})
        with self.assertRaises(ValueError):
            MarketInsiderActivityTrackerModuleAPI.track_activity({"ticker_id": "AAPL", "volume": "invalid"})

    def test_track_activity_invalid_multiplier(self):
        with self.assertRaises(ValueError):
            MarketInsiderActivityTrackerModuleAPI.track_activity({"ticker_id": "AAPL", "anomaly_multiplier": -1.0})
        with self.assertRaises(ValueError):
            MarketInsiderActivityTrackerModuleAPI.track_activity({"ticker_id": "AAPL", "anomaly_multiplier": "invalid"})

    def test_track_activity_detects_volume_anomaly(self):
        random_ticker = uuid.uuid4().hex
        high_volume = random.uniform(500001.0, 2000000.0)
        normal_multiplier = random.uniform(0.1, 4.0)
        
        payload = {
            "ticker_id": random_ticker,
            "volume": high_volume,
            "anomaly_multiplier": normal_multiplier
        }
        
        result = MarketInsiderActivityTrackerModuleAPI.track_activity(payload)
        
        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("anomaly_detected"))
        self.assertEqual(result.get("ticker_id"), random_ticker)
        self.assertEqual(result.get("volume"), high_volume)
        self.assertIn("signature", result)

    def test_track_activity_detects_multiplier_anomaly(self):
        random_ticker = uuid.uuid4().hex
        low_volume = random.uniform(0.0, 500000.0)
        high_multiplier = random.uniform(5.1, 20.0)
        
        payload = {
            "ticker_id": random_ticker,
            "volume": low_volume,
            "anomaly_multiplier": high_multiplier
        }
        
        result = MarketInsiderActivityTrackerModuleAPI.track_activity(payload)
        
        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("anomaly_detected"))
        self.assertEqual(result.get("ticker_id"), random_ticker)
        self.assertEqual(result.get("volume"), low_volume)

    def test_track_activity_returns_normal(self):
        random_ticker = uuid.uuid4().hex
        low_volume = random.uniform(0.0, 500000.0)
        normal_multiplier = random.uniform(0.1, 5.0)
        
        payload = {
            "ticker_id": random_ticker,
            "volume": low_volume,
            "anomaly_multiplier": normal_multiplier
        }
        
        result = MarketInsiderActivityTrackerModuleAPI.track_activity(payload)
        
        self.assertIsInstance(result, dict)
        self.assertFalse(result.get("anomaly_detected"))
        self.assertEqual(result.get("ticker_id"), random_ticker)
        self.assertEqual(result.get("volume"), low_volume)

    def test_idempotent_proxy_alias(self):
        proxy_obj = MarketInsiderActivityTrackerModuleIdempotentProxy()
        self.assertTrue(proxy_obj.proxy_active)

        random_ticker = uuid.uuid4().hex
        payload = {
            "ticker_id": random_ticker,
            "volume": random.uniform(100.0, 1000.0),
            "anomaly_multiplier": 1.0
        }

        result = MarketInsiderActivityTrackerModuleIdempotentProxy.track_activity(payload)
        self.assertEqual(result.get("ticker_id"), random_ticker)

if __name__ == "__main__":
    unittest.main()