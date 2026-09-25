import unittest
import uuid
import random
import io
import os
from skills.market_insider_activity_tracker import (
    MarketInsiderActivityTracker,
    MarketInsiderActivityTrackerModuleAPI,
    DBStorage
)

class TestMarketInsiderActivityTrackerIntegration(unittest.TestCase):
    
    def setUp(self):
        self.db_path = f"test_integration_{uuid.uuid4().hex}.db"
        self.db_storage = DBStorage(db_path=self.db_path)
        self.tracker = MarketInsiderActivityTracker(db_storage=self.db_storage)
        
    def tearDown(self):
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except OSError:
                pass

    def test_full_insider_tracking_pipeline_normal(self):
        random_ticker = f"TICKER_{uuid.uuid4().hex[:6].upper()}"
        random_volume = round(random.uniform(1000.0, 499999.0), 2)
        random_multiplier = round(random.uniform(1.0, 4.9), 2)
        
        payload = {
            "ticker_id": random_ticker,
            "volume": random_volume,
            "anomaly_multiplier": random_multiplier
        }
        
        api_result = MarketInsiderActivityTrackerModuleAPI.track_activity(payload)
        
        self.assertFalse(api_result["anomaly_detected"])
        self.assertEqual(api_result["ticker_id"], random_ticker)
        self.assertEqual(api_result["volume"], random_volume)
        self.assertIn("signature", api_result)
        
        self.db_storage.save_activity(
            ticker=api_result["ticker_id"],
            is_anomaly=api_result["anomaly_detected"],
            signature=api_result["signature"]
        )
        
        stored_activity = self.db_storage.get_last_activity(random_ticker)
        self.assertIsNotNone(stored_activity)
        self.assertEqual(stored_activity["ticker"], random_ticker)
        self.assertFalse(stored_activity["is_anomaly"])
        self.assertEqual(stored_activity["signature"], api_result["signature"])

    def test_full_insider_tracking_pipeline_anomaly(self):
        random_ticker = f"TICKER_{uuid.uuid4().hex[:6].upper()}"
        random_volume = round(random.uniform(500001.0, 2000000.0), 2)
        random_multiplier = round(random.uniform(5.1, 10.0), 2)
        
        payload = {
            "ticker_id": random_ticker,
            "volume": random_volume,
            "anomaly_multiplier": random_multiplier
        }
        
        api_result = MarketInsiderActivityTrackerModuleAPI.track_activity(payload)
        
        self.assertTrue(api_result["anomaly_detected"])
        self.assertEqual(api_result["ticker_id"], random_ticker)
        
        stream_data = f"data_stream_{uuid.uuid4().hex} anomaly".encode('utf-8')
        stream = io.BytesIO(stream_data)
        stream_analysis = self.tracker.analyze_activity(stream)
        
        self.assertEqual(stream_analysis["status"], "ALERT")
        self.assertIn("signature", stream_analysis)
        
        self.db_storage.save_activity(
            ticker=api_result["ticker_id"],
            is_anomaly=api_result["anomaly_detected"],
            signature=stream_analysis["signature"]
        )
        
        stored_activity = self.db_storage.get_last_activity(random_ticker)
        self.assertIsNotNone(stored_activity)
        self.assertEqual(stored_activity["ticker"], random_ticker)
        self.assertTrue(stored_activity["is_anomaly"])
        self.assertEqual(stored_activity["signature"], stream_analysis["signature"])

    def test_invalid_stream_handling(self):
        with self.assertRaises(ValueError):
            self.tracker.analyze_activity(None)
            
        empty_stream = io.BytesIO(b"")
        with self.assertRaises(ValueError):
            self.tracker.analyze_activity(empty_stream)

    def test_malformed_payload_resilience(self):
        random_ticker = f"TICKER_{uuid.uuid4().hex[:6].upper()}"
        bad_payload = {
            "ticker_id": random_ticker,
            "volume": "not_a_number",
            "anomaly_multiplier": "also_bad"
        }
        
        api_result = MarketInsiderActivityTrackerModuleAPI.track_activity(bad_payload)
        self.assertFalse(api_result["anomaly_detected"])
        self.assertEqual(api_result["volume"], 0.0)
        self.assertEqual(api_result["ticker_id"], random_ticker)

if __name__ == "__main__":
    unittest.main()