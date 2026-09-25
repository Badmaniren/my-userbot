import unittest
import uuid
import random
import os
from skills.market_insider_activity_tracker import MarketInsiderActivityTracker, MarketInsiderActivityTrackerModuleAPI, DBStorage

class TestMarketInsiderActivityTrackerIntegration(unittest.TestCase):
    def setUp(self):
        self.db_path = f"test_integration_{uuid.uuid4().hex}.db"
        self.storage = DBStorage(db_path=self.db_path)
        self.tracker = MarketInsiderActivityTracker(db_storage=self.storage)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_end_to_end_activity_tracking_and_persistence(self):
        random_ticker = f"TICK_{uuid.uuid4().hex[:6].upper()}"
        random_volume = float(random.randint(100000, 1000000))
        random_multiplier = round(random.uniform(1.0, 10.0), 2)
        
        payload = {
            "ticker_id": random_ticker,
            "volume": random_volume,
            "anomaly_multiplier": random_multiplier
        }
        
        api_result = MarketInsiderActivityTrackerModuleAPI.track_activity(payload)
        
        self.assertIn("anomaly_detected", api_result)
        self.assertEqual(api_result["ticker_id"], random_ticker)
        self.assertEqual(api_result["volume"], random_volume)
        self.assertIsInstance(api_result["signature"], str)
        self.assertTrue(len(api_result["signature"]) > 0)

        self.storage.save_activity(
            ticker=random_ticker,
            is_anomaly=api_result["anomaly_detected"],
            signature=api_result["signature"]
        )

        last_activity = self.storage.get_last_activity(random_ticker)
        
        self.assertIsNotNone(last_activity)
        self.assertEqual(last_activity["ticker"], random_ticker)
        self.assertEqual(last_activity["is_anomaly"], api_result["anomaly_detected"])
        self.assertEqual(last_activity["signature"], api_result["signature"])

    def test_stream_analysis_integration(self):
        from io import BytesIO
        
        random_suffix = uuid.uuid4().bytes
        is_anomaly_case = random.choice([True, False])
        
        if is_anomaly_case:
            stream_content = b"data stream anomaly " + random_suffix
        else:
            stream_content = b"normal data stream " + random_suffix
            
        stream = BytesIO(stream_content)
        analysis_result = self.tracker.analyze_activity(stream)
        
        self.assertIn("status", analysis_result)
        self.assertIn("signature", analysis_result)
        
        if is_anomaly_case:
            self.assertEqual(analysis_result["status"], "ALERT")
        else:
            self.assertEqual(analysis_result["status"], "NORMAL")
            
        self.assertIsInstance(analysis_result["signature"], str)

if __name__ == "__main__":
    unittest.main()