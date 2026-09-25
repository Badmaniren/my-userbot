import unittest
from unittest.mock import patch
import io
import uuid
import random
import os
from skills.market_insider_activity_tracker import (
    MarketInsiderActivityTracker,
    MarketInsiderActivityTrackerModuleAPI,
    DBStorage
)

class TestMarketInsiderActivityTracker(unittest.TestCase):
    def setUp(self):
        self.db_filename = f"{uuid.uuid4().hex}.db"
        self.tracker = MarketInsiderActivityTracker(db_storage=None)

    def tearDown(self):
        if os.path.exists(self.db_filename):
            try:
                os.remove(self.db_filename)
            except OSError:
                pass

    def test_analyze_activity_none_stream(self):
        with self.assertRaises(ValueError):
            self.tracker.analyze_activity(None)

    def test_analyze_activity_empty_stream(self):
        empty_stream = io.BytesIO(b"")
        with self.assertRaises(ValueError):
            self.tracker.analyze_activity(empty_stream)

    def test_analyze_activity_normal(self):
        random_bytes = uuid.uuid4().bytes
        stream = io.BytesIO(random_bytes)
        result = self.tracker.analyze_activity(stream)
        self.assertEqual(result["status"], "NORMAL")
        self.assertIn("signature", result)
        self.assertTrue(isinstance(result["signature"], str))
        self.assertTrue(len(result["signature"]) > 0)

    def test_analyze_activity_anomaly(self):
        anomaly_prefix = uuid.uuid4().bytes
        anomaly_payload = anomaly_prefix + b"anomaly" + uuid.uuid4().bytes
        stream = io.BytesIO(anomaly_payload)
        result = self.tracker.analyze_activity(stream)
        self.assertEqual(result["status"], "ALERT")
        self.assertIn("signature", result)
        self.assertTrue(isinstance(result["signature"], str))

    def test_market_insider_activity_tracker_module_api_invalid_payload(self):
        rand_str = uuid.uuid4().hex
        result = MarketInsiderActivityTrackerModuleAPI.track_activity(rand_str)
        self.assertIsInstance(result, dict)
        self.assertFalse(result["anomaly_detected"])
        self.assertIsNone(result["ticker_id"])
        self.assertEqual(result["volume"], 0.0)
        self.assertIn("signature", result)

    def test_market_insider_activity_tracker_module_api_normal_payload(self):
        ticker = f"TICK_{uuid.uuid4().hex[:6]}"
        volume = float(random.randint(100, 400000))
        multiplier = float(random.randint(1, 4))
        payload = {
            "ticker_id": ticker,
            "volume": volume,
            "anomaly_multiplier": multiplier
        }
        result = MarketInsiderActivityTrackerModuleAPI.track_activity(payload)
        self.assertFalse(result["anomaly_detected"])
        self.assertEqual(result["ticker_id"], ticker)
        self.assertEqual(result["volume"], volume)
        self.assertIn("signature", result)

    def test_market_insider_activity_tracker_module_api_volume_anomaly(self):
        ticker = f"TICK_{uuid.uuid4().hex[:6]}"
        volume = float(random.randint(500001, 1000000))
        multiplier = float(random.randint(1, 3))
        payload = {
            "ticker_id": ticker,
            "volume": volume,
            "anomaly_multiplier": multiplier
        }
        result = MarketInsiderActivityTrackerModuleAPI.track_activity(payload)
        self.assertTrue(result["anomaly_detected"])
        self.assertEqual(result["ticker_id"], ticker)
        self.assertEqual(result["volume"], volume)

    def test_market_insider_activity_tracker_module_api_multiplier_anomaly(self):
        ticker = f"TICK_{uuid.uuid4().hex[:6]}"
        volume = float(random.randint(100, 10000))
        multiplier = float(random.randint(6, 20))
        payload = {
            "ticker_id": ticker,
            "volume": volume,
            "anomaly_multiplier": multiplier
        }
        result = MarketInsiderActivityTrackerModuleAPI.track_activity(payload)
        self.assertTrue(result["anomaly_detected"])
        self.assertEqual(result["ticker_id"], ticker)
        self.assertEqual(result["volume"], volume)

    def test_market_insider_activity_tracker_module_api_malformed_values(self):
        ticker = f"TICK_{uuid.uuid4().hex[:6]}"
        payload = {
            "ticker_id": ticker,
            "volume": uuid.uuid4().hex,
            "anomaly_multiplier": uuid.uuid4().hex
        }
        result = MarketInsiderActivityTrackerModuleAPI.track_activity(payload)
        self.assertFalse(result["anomaly_detected"])
        self.assertEqual(result["ticker_id"], ticker)
        self.assertEqual(result["volume"], 0.0)

    def test_db_storage_save_and_get_last_activity(self):
        storage = DBStorage(db_path=self.db_filename)
        ticker = f"TICK_{uuid.uuid4().hex[:6]}"
        is_anomaly = random.choice([True, False])
        signature = uuid.uuid4().hex

        storage.save_activity(ticker, is_anomaly, signature)
        retrieved = storage.get_last_activity(ticker)

        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["ticker"], ticker)
        self.assertEqual(retrieved["is_anomaly"], is_anomaly)
        self.assertEqual(retrieved["signature"], signature)

    def test_db_storage_get_last_activity_nonexistent(self):
        storage = DBStorage(db_path=self.db_filename)
        non_existent_ticker = f"NON_{uuid.uuid4().hex[:6]}"
        retrieved = storage.get_last_activity(non_existent_ticker)
        self.assertIsNone(retrieved)

if __name__ == "__main__":
    unittest.main()