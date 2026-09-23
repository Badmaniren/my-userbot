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
        self.proxy = MarketInsiderActivityTrackerModuleIdempotentProxy

    def test_market_insider_activity_tracker_stream_normal(self):
        random_seed = str(uuid.uuid4()).encode('utf-8')
        stream = io.BytesIO(b"normal market data flow " + random_seed)
        
        result = self.tracker.analyze_activity(stream)
        
        self.assertEqual(result["status"], "NORMAL")
        self.assertIn("signature", result)
        self.assertTrue(len(result["signature"]) > 0)

    def test_market_insider_activity_tracker_stream_anomaly(self):
        random_suffix = str(uuid.uuid4()).encode('utf-8')
        stream = io.BytesIO(b"anomaly detected in block " + random_suffix)
        
        result = self.tracker.analyze_activity(stream)
        
        self.assertEqual(result["status"], "ALERT")
        self.assertIn("signature", result)

    def test_market_insider_activity_tracker_stream_empty_raises(self):
        stream = io.BytesIO(b"")
        with self.assertRaises(ValueError):
            self.tracker.analyze_activity(stream)

    def test_market_insider_activity_tracker_api_payload_handling(self):
        random_ticker = f"TICK_{random.randint(1000, 9999)}"
        random_volume = float(random.randint(100, 400000))
        
        payload = {
            "ticker_id": random_ticker,
            "volume": random_volume,
            "anomaly_multiplier": 1.1
        }
        
        result = self.api.track_activity(payload)
        
        self.assertFalse(result["anomaly_detected"])
        self.assertEqual(result["ticker_id"], random_ticker)
        self.assertEqual(result["volume"], random_volume)
        self.assertIn("signature", result)

    def test_market_insider_activity_tracker_api_anomaly_detection(self):
        random_ticker = f"TICK_{random.randint(10000, 99999)}"
        high_volume = float(random.randint(600000, 1000000))
        
        payload = {
            "ticker_id": random_ticker,
            "volume": high_volume,
            "anomaly_multiplier": 6.5
        }
        
        result = self.proxy.track_activity(payload)
        
        self.assertTrue(result["anomaly_detected"])
        self.assertEqual(result["ticker_id"], random_ticker)
        self.assertEqual(result["volume"], high_volume)
        self.assertIsInstance(result["signature"], str)

if __name__ == "__main__":
    unittest.main()