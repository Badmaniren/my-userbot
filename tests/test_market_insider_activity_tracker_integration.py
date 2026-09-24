import io
import random
import unittest
import uuid

from skills.market_insider_activity_tracker import (
    MarketInsiderActivityTracker,
    MarketInsiderActivityTrackerModuleAPI,
    market_insider_activity_tracker
)

class TestMarketInsiderActivityTrackerIntegration(unittest.TestCase):
    def setUp(self):
        self.tracker = MarketInsiderActivityTracker()

    def test_analyze_activity_normal_stream(self):
        random_bytes = f"normal_data_{uuid.uuid4().hex}".encode('utf-8')
        stream = io.BytesIO(random_bytes)
        result = self.tracker.analyze_activity(stream)
        
        self.assertEqual(result["status"], "NORMAL")
        self.assertEqual(len(result["signature"]), 32)

    def test_analyze_activity_anomaly_stream(self):
        random_bytes = f"some_prefix_anomaly_{uuid.uuid4().hex}".encode('utf-8')
        stream = io.BytesIO(random_bytes)
        result = self.tracker.analyze_activity(stream)
        
        self.assertEqual(result["status"], "ALERT")
        self.assertEqual(len(result["signature"]), 32)

    def test_analyze_activity_empty_stream_raises_value_error(self):
        stream = io.BytesIO(b"")
        with self.assertRaises(ValueError):
            self.tracker.analyze_activity(stream)

    def test_track_activity_api_normal(self):
        ticker_id = f"TICKER_{uuid.uuid4().hex[:8].upper()}"
        volume = random.uniform(1000.0, 499999.0)
        multiplier = random.uniform(0.1, 4.9)
        
        payload = {
            "ticker_id": ticker_id,
            "volume": volume,
            "anomaly_multiplier": multiplier
        }
        
        result = MarketInsiderActivityTrackerModuleAPI.track_activity(payload)
        
        self.assertFalse(result["anomaly_detected"])
        self.assertEqual(result["ticker_id"], ticker_id)
        self.assertEqual(result["volume"], volume)
        self.assertEqual(len(result["signature"]), 32)

    def test_track_activity_api_anomaly_by_volume(self):
        ticker_id = f"TICKER_{uuid.uuid4().hex[:8].upper()}"
        volume = random.uniform(500001.0, 1000000.0)
        multiplier = random.uniform(0.1, 4.9)
        
        payload = {
            "ticker_id": ticker_id,
            "volume": volume,
            "anomaly_multiplier": multiplier
        }
        
        result = MarketInsiderActivityTrackerModuleAPI.track_activity(payload)
        
        self.assertTrue(result["anomaly_detected"])
        self.assertEqual(result["ticker_id"], ticker_id)
        self.assertEqual(result["volume"], volume)
        self.assertEqual(len(result["signature"]), 32)

    def test_track_activity_api_anomaly_by_multiplier(self):
        ticker_id = f"TICKER_{uuid.uuid4().hex[:8].upper()}"
        volume = random.uniform(1000.0, 499999.0)
        multiplier = random.uniform(5.1, 15.0)
        
        payload = {
            "ticker_id": ticker_id,
            "volume": volume,
            "anomaly_multiplier": multiplier
        }
        
        result = market_insider_activity_tracker.track_activity(payload)
        
        self.assertTrue(result["anomaly_detected"])
        self.assertEqual(result["ticker_id"], ticker_id)
        self.assertEqual(result["volume"], volume)
        self.assertEqual(len(result["signature"]), 32)

if __name__ == "__main__":
    unittest.main()