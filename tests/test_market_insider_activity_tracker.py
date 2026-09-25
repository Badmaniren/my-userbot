import unittest
from unittest.mock import patch
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
        self.tracker = MarketInsiderActivityTracker(
            db_storage=uuid.uuid4().hex,
            market_portfolio_monitor=uuid.uuid4().hex
        )

    def test_analyze_activity_none_stream(self):
        with self.assertRaises(ValueError):
            self.tracker.analyze_activity(None)

    def test_analyze_activity_empty_stream(self):
        empty_stream = io.BytesIO(b"")
        with self.assertRaises(ValueError):
            self.tracker.analyze_activity(empty_stream)

    def test_analyze_activity_normal_stream(self):
        random_payload = "".join(random.choices(string.ascii_letters + string.digits, k=32)).encode('utf-8')
        stream = io.BytesIO(random_payload)
        result = self.tracker.analyze_activity(stream)
        self.assertEqual(result["status"], "NORMAL")
        self.assertIn("signature", result)
        self.assertEqual(len(result["signature"]), 32)

    def test_analyze_activity_anomaly_stream(self):
        prefix = "".join(random.choices(string.ascii_letters, k=10)).encode('utf-8')
        anomaly_payload = prefix + b"anomaly" + "".join(random.choices(string.ascii_letters, k=10)).encode('utf-8')
        stream = io.BytesIO(anomaly_payload)
        result = self.tracker.analyze_activity(stream)
        self.assertEqual(result["status"], "ALERT")
        self.assertIn("signature", result)
        self.assertEqual(len(result["signature"]), 32)


class TestMarketInsiderActivityTrackerModuleAPI(unittest.TestCase):

    def test_track_activity_invalid_payload(self):
        random_invalid = random.choice([None, uuid.uuid4().hex, random.randint(1, 100), []])
        result = MarketInsiderActivityTrackerModuleAPI.track_activity(random_invalid)
        self.assertIsInstance(result, dict)
        self.assertFalse(result["anomaly_detected"])
        self.assertIsNone(result["ticker_id"])
        self.assertEqual(result["volume"], 0.0)
        self.assertIn("signature", result)

    def test_track_activity_normal_volume(self):
        ticker = uuid.uuid4().hex
        normal_volume = random.uniform(10.0, 499999.0)
        normal_multiplier = random.uniform(1.0, 4.9)
        payload = {
            "ticker_id": ticker,
            "volume": normal_volume,
            "anomaly_multiplier": normal_multiplier
        }
        result = MarketInsiderActivityTrackerModuleAPI.track_activity(payload)
        self.assertFalse(result["anomaly_detected"])
        self.assertEqual(result["ticker_id"], ticker)
        self.assertEqual(result["volume"], float(normal_volume))
        self.assertIn("signature", result)

    def test_track_activity_anomaly_volume(self):
        ticker = uuid.uuid4().hex
        high_volume = random.uniform(500001.0, 1000000.0)
        payload = {
            "ticker_id": ticker,
            "volume": high_volume,
            "anomaly_multiplier": 1.0
        }
        result = MarketInsiderActivityTrackerModuleAPI.track_activity(payload)
        self.assertTrue(result["anomaly_detected"])
        self.assertEqual(result["ticker_id"], ticker)
        self.assertEqual(result["volume"], float(high_volume))

    def test_track_activity_anomaly_multiplier(self):
        ticker = uuid.uuid4().hex
        high_multiplier = random.uniform(5.1, 20.0)
        payload = {
            "ticker_id": ticker,
            "volume": 100.0,
            "anomaly_multiplier": high_multiplier
        }
        result = MarketInsiderActivityTrackerModuleAPI.track_activity(payload)
        self.assertTrue(result["anomaly_detected"])
        self.assertEqual(result["ticker_id"], ticker)

    def test_track_activity_malformed_numeric_fields(self):
        ticker = uuid.uuid4().hex
        bad_volume_str = uuid.uuid4().hex
        bad_multiplier_str = uuid.uuid4().hex
        payload = {
            "ticker_id": ticker,
            "volume": bad_volume_str,
            "anomaly_multiplier": bad_multiplier_str
        }
        result = MarketInsiderActivityTrackerModuleAPI.track_activity(payload)
        self.assertFalse(result["anomaly_detected"])
        self.assertEqual(result["ticker_id"], ticker)
        self.assertEqual(result["volume"], 0.0)


class TestMarketInsiderActivityTrackerModuleIdempotentProxy(unittest.TestCase):

    def test_proxy_alias_consistency(self):
        self.assertEqual(MarketInsiderActivityTrackerModuleIdempotentProxy, MarketInsiderActivityTrackerModuleAPI)
        ticker = uuid.uuid4().hex
        payload = {
            "ticker_id": ticker,
            "volume": random.uniform(600000.0, 900000.0),
            "anomaly_multiplier": 6.0
        }
        res_proxy = MarketInsiderActivityTrackerModuleIdempotentProxy.track_activity(payload)
        res_api = MarketInsiderActivityTrackerModuleAPI.track_activity(payload)
        self.assertEqual(res_proxy["anomaly_detected"], res_api["anomaly_detected"])
        self.assertEqual(res_proxy["ticker_id"], res_api["ticker_id"])


if __name__ == "__main__":
    unittest.main()