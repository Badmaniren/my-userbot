import unittest
from unittest.mock import MagicMock, patch
import io
import uuid
import random
import string
from skills.market_insider_activity_tracker import (
    MarketInsiderActivityTracker,
    MarketInsiderActivityTrackerModuleAPI,
    MarketInsiderActivityTrackerModuleIdempotentProxy
)

class TestMarketInsiderActivityTracker(unittest.TestCase):

    def setUp(self):
        self.db_storage_mock = MagicMock()
        self.tracker = MarketInsiderActivityTracker(db_storage=self.db_storage_mock)

    def test_analyze_activity_none_stream_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.tracker.analyze_activity(None)

    def test_analyze_activity_empty_stream_raises_value_error(self):
        empty_stream = io.BytesIO(b"")
        with self.assertRaises(ValueError):
            self.tracker.analyze_activity(empty_stream)

    def test_analyze_activity_anomaly_detection(self):
        rand_prefix = ''.join(random.choices(string.ascii_letters, k=10))
        stream_data = f"{rand_prefix} anomaly detected in sector".encode('utf-8')
        stream = io.BytesIO(stream_data)

        result = self.tracker.analyze_activity(stream)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "ALERT")
        self.assertIn("signature", result)
        self.assertTrue(uuid.UUID(result["signature"], version=4))

    def test_analyze_activity_normal_flow(self):
        rand_content = ''.join(random.choices(string.ascii_letters + string.digits, k=32)).encode('utf-8')
        stream = io.BytesIO(rand_content)

        result = self.tracker.analyze_activity(stream)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "NORMAL")
        self.assertIn("signature", result)
        self.assertTrue(uuid.UUID(result["signature"], version=4))


class TestMarketInsiderActivityTrackerModuleAPI(unittest.TestCase):

    def test_track_activity_invalid_payload_fallback(self):
        invalid_payloads = [
            ''.join(random.choices(string.ascii_letters, k=8)),
            random.randint(1000, 99999),
            None,
            [random.randint(1, 100)]
        ]
        for payload in invalid_payloads:
            result = MarketInsiderActivityTrackerModuleAPI.track_activity(payload)
            self.assertIsInstance(result, dict)
            self.assertIn("anomaly_detected", result)
            self.assertIsNone(result.get("ticker_id"))
            self.assertEqual(result.get("volume"), 0.0)

    def test_track_activity_high_volume_anomaly(self):
        ticker_id = f"TICKER_{uuid.uuid4().hex[:6].upper()}"
        volume = random.uniform(500001.0, 2000000.0)
        multiplier = random.uniform(0.1, 4.9)
        
        payload = {
            "ticker_id": ticker_id,
            "volume": volume,
            "anomaly_multiplier": multiplier
        }

        result = MarketInsiderActivityTrackerModuleAPI.track_activity(payload)

        self.assertTrue(result["anomaly_detected"])
        self.assertEqual(result["ticker_id"], ticker_id)
        self.assertEqual(result["volume"], float(volume))
        self.assertIn("signature", result)

    def test_track_activity_high_multiplier_anomaly(self):
        ticker_id = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        volume = random.uniform(10.0, 499999.0)
        multiplier = random.uniform(5.1, 20.0)

        payload = {
            "ticker_id": ticker_id,
            "volume": str(volume),
            "anomaly_multiplier": str(multiplier)
        }

        result = MarketInsiderActivityTrackerModuleAPI.track_activity(payload)

        self.assertTrue(result["anomaly_detected"])
        self.assertEqual(result["ticker_id"], ticker_id)
        self.assertEqual(result["volume"], float(volume))

    def test_track_activity_normal_operation(self):
        ticker_id = f"STK_{uuid.uuid4().hex[:6].upper()}"
        volume = random.uniform(100.0, 400000.0)
        multiplier = random.uniform(1.0, 4.0)

        payload = {
            "ticker_id": ticker_id,
            "volume": volume,
            "anomaly_multiplier": multiplier
        }

        result = MarketInsiderActivityTrackerModuleAPI.track_activity(payload)

        self.assertFalse(result["anomaly_detected"])
        self.assertEqual(result["ticker_id"], ticker_id)
        self.assertEqual(result["volume"], float(volume))

    def test_track_activity_malformed_numeric_inputs(self):
        ticker_id = f"ERR_{uuid.uuid4().hex[:6].upper()}"
        bad_volume = ''.join(random.choices(string.ascii_letters, k=5))
        bad_multiplier = ''.join(random.choices(string.punctuation, k=4))

        payload = {
            "ticker_id": ticker_id,
            "volume": bad_volume,
            "anomaly_multiplier": bad_multiplier
        }

        result = MarketInsiderActivityTrackerModuleAPI.track_activity(payload)

        self.assertFalse(result["anomaly_detected"])
        self.assertEqual(result["ticker_id"], ticker_id)
        self.assertEqual(result["volume"], 0.0)


class TestMarketInsiderActivityTrackerModuleIdempotentProxy(unittest.TestCase):

    def test_proxy_alias_existence(self):
        self.assertIs(
            MarketInsiderActivityTrackerModuleIdempotentProxy,
            MarketInsiderActivityTrackerModuleAPI
        )
        
        ticker_id = f"PROXY_{uuid.uuid4().hex[:6]}"
        payload = {"ticker_id": ticker_id, "volume": random.randint(10, 100)}
        res = MarketInsiderActivityTrackerModuleIdempotentProxy.track_activity(payload)
        self.assertEqual(res["ticker_id"], ticker_id)

if __name__ == "__main__":
    unittest.main()