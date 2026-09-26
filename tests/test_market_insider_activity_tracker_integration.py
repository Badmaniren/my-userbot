import unittest
import uuid
import random
import os
from skills.market_insider_activity_tracker import (
    MarketInsiderActivityTracker,
    MarketInsiderActivityTrackerModuleAPI,
    DBStorage
)

class TestMarketInsiderActivityTrackerIntegration(unittest.TestCase):
    def setUp(self):
        self.db_path = f"test_market_{uuid.uuid4().hex}.db"
        self.db_storage = DBStorage(db_path=self.db_path)
        self.tracker = MarketInsiderActivityTracker(db_storage=self.db_storage)
        self.api = MarketInsiderActivityTrackerModuleAPI()

    def tearDown(self):
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except OSError:
                pass

    def test_integration_full_flow(self):
        random_ticker = f"TICK_{uuid.uuid4().hex[:6].upper()}"
        random_volume = round(random.uniform(600000.0, 1000000.0), 2)
        random_multiplier = round(random.uniform(6.0, 10.0), 2)

        payload = {
            "ticker_id": random_ticker,
            "volume": random_volume,
            "anomaly_multiplier": random_multiplier
        }

        api_result = self.api.track_activity(payload)
        self.assertTrue(api_result["anomaly_detected"])
        self.assertEqual(api_result["ticker_id"], random_ticker)
        self.assertEqual(api_result["volume"], random_volume)
        
        signature = api_result["signature"]
        self.assertIsInstance(signature, str)
        self.assertTrue(len(signature) > 0)

        self.db_storage.save_activity(
            ticker=random_ticker,
            is_anomaly=api_result["anomaly_detected"],
            signature=signature
        )

        stored_record = self.db_storage.get_last_activity(random_ticker)
        self.assertIsNotNone(stored_record)
        self.assertEqual(stored_record["ticker"], random_ticker)
        self.assertTrue(stored_record["is_anomaly"])
        self.assertEqual(stored_record["signature"], signature)

    def test_integration_stream_analysis(self):
        random_anomaly_marker = uuid.uuid4().bytes
        stream_content = b"data stream prefix " + random_anomaly_marker + b" anomaly suffix"
        
        class MockStream:
            def __init__(self, content):
                self.content = content
            def read(self):
                return self.content

        stream = MockStream(stream_content)
        analysis_result = self.tracker.analyze_activity(stream)
        
        self.assertEqual(analysis_result["status"], "ALERT")
        self.assertIn("signature", analysis_result)
        self.assertIsInstance(analysis_result["signature"], str)

if __name__ == "__main__":
    unittest.main()