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
    def setUp(self) -> None:
        self.db_path = f"test_integration_{uuid.uuid4().hex}.db"
        self.db_storage = DBStorage(db_path=self.db_path)
        self.tracker = MarketInsiderActivityTracker(db_storage=self.db_storage)

    def tearDown(self) -> None:
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_end_to_end_activity_tracking_flow(self) -> None:
        random_ticker = f"TICKER_{uuid.uuid4().hex[:6].upper()}"
        random_volume = round(random.uniform(100000.0, 1000000.0), 2)
        random_multiplier = round(random.uniform(1.0, 10.0), 2)

        payload = {
            "ticker_id": random_ticker,
            "volume": random_volume,
            "anomaly_multiplier": random_multiplier
        }

        api_result = MarketInsiderActivityTrackerModuleAPI.track_activity(payload)

        self.assertEqual(api_result["ticker_id"], random_ticker)
        self.assertIsInstance(api_result["anomaly_detected"], bool)
        self.assertIsInstance(api_result["signature"], str)

        self.db_storage.save_activity(
            ticker=api_result["ticker_id"],
            is_anomaly=api_result["anomaly_detected"],
            signature=api_result["signature"]
        )

        stored_activity = self.db_storage.get_last_activity(random_ticker)
        
        self.assertIsNotNone(stored_activity)
        self.assertEqual(stored_activity["ticker"], random_ticker)
        self.assertEqual(stored_activity["is_anomaly"], api_result["anomaly_detected"])
        self.assertEqual(stored_activity["signature"], api_result["signature"])

if __name__ == "__main__":
    unittest.main()