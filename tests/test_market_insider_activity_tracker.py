import unittest
import io
import uuid
import random
from unittest.mock import patch
from skills.market_insider_activity_tracker import (
    MarketInsiderActivityTracker,
    MarketInsiderActivityTrackerModuleAPI
)

class TestMarketInsiderActivityTracker(unittest.TestCase):

    def setUp(self):
        self.tracker_key = uuid.uuid4().hex
        self.tracker = MarketInsiderActivityTracker(key=self.tracker_key)
        self.api = MarketInsiderActivityTrackerModuleAPI()

    def test_analyze_activity_empty_stream_raises(self):
        with self.assertRaises(ValueError):
            self.tracker.analyze_activity(None)

        empty_stream = io.BytesIO(b"")
        with self.assertRaises(ValueError):
            self.tracker.analyze_activity(empty_stream)

    def test_analyze_activity_normal(self):
        random_payload = f"normal_data_{uuid.uuid4().hex}".encode('utf-8')
        stream = io.BytesIO(random_payload)
        result = self.tracker.analyze_activity(stream)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "NORMAL")
        self.assertIn("signature", result)
        self.assertTrue(len(result["signature"]) > 0)

    def test_analyze_activity_anomaly(self):
        anomaly_keyword = random.choice([b"anomaly", b"anomaly_detected"])
        random_payload = f"prefix_{uuid.uuid4().hex}_".encode('utf-8') + anomaly_keyword + f"_suffix_{uuid.uuid4().hex}".encode('utf-8')
        stream = io.BytesIO(random_payload)
        result = self.tracker.analyze_activity(stream)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "ALERT")
        self.assertIn("signature", result)
        self.assertTrue(len(result["signature"]) > 0)

    def test_track_activity_invalid_payload(self):
        invalid_inputs = [None, uuid.uuid4().hex, random.randint(1, 100), []]
        for invalid in invalid_inputs:
            result = self.api.track_activity(invalid)
            self.assertIsInstance(result, dict)
            self.assertIn("anomaly_detected", result)
            self.assertIn("ticker_id", result)
            self.assertIn("volume", result)
            self.assertIn("signature", result)

    def test_track_activity_normal_metrics(self):
        ticker = f"TICK_{uuid.uuid4().hex[:6].upper()}"
        vol = round(random.uniform(100.0, 499999.0), 2)
        mult = round(random.uniform(0.1, 4.9), 2)
        
        payload = {
            "ticker_id": ticker,
            "volume": vol,
            "anomaly_multiplier": mult
        }
        
        result = self.api.track_activity(payload)
        self.assertFalse(result["anomaly_detected"])
        self.assertEqual(result["ticker_id"], ticker)
        self.assertEqual(result["volume"], vol)
        self.assertIn("signature", result)

    def test_track_activity_high_volume_anomaly(self):
        ticker = f"TICK_{uuid.uuid4().hex[:6].upper()}"
        vol = round(random.uniform(500001.0, 2000000.0), 2)
        mult = round(random.uniform(0.1, 4.9), 2)
        
        payload = {
            "ticker_id": ticker,
            "volume": vol,
            "anomaly_multiplier": mult
        }
        
        result = self.api.track_activity(payload)
        self.assertTrue(result["anomaly_detected"])
        self.assertEqual(result["ticker_id"], ticker)
        self.assertEqual(result["volume"], vol)

    def test_track_activity_high_multiplier_anomaly(self):
        ticker = f"TICK_{uuid.uuid4().hex[:6].upper()}"
        vol = round(random.uniform(100.0, 1000.0), 2)
        mult = round(random.uniform(5.1, 20.0), 2)
        
        payload = {
            "ticker_id": ticker,
            "volume": vol,
            "anomaly_multiplier": mult
        }
        
        result = self.api.track_activity(payload)
        self.assertTrue(result["anomaly_detected"])
        self.assertEqual(result["ticker_id"], ticker)

    def test_track_activity_malformed_types(self):
        ticker = uuid.uuid4().hex
        payload = {
            "ticker_id": ticker,
            "volume": f"bad_vol_{uuid.uuid4().hex}",
            "anomaly_multiplier": f"bad_mult_{uuid.uuid4().hex}"
        }
        
        result = self.api.track_activity(payload)
        self.assertFalse(result["anomaly_detected"])
        self.assertEqual(result["ticker_id"], ticker)
        self.assertEqual(result["volume"], 0.0)

if __name__ == "__main__":
    unittest.main()