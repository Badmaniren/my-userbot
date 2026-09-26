import unittest
import io
import os
import uuid
import random
from unittest.mock import patch, MagicMock

from skills.market_insider_activity_tracker import (
    MarketInsiderActivityTracker,
    MarketInsiderActivityTrackerModuleAPI,
    DBStorage
)


class TestMarketInsiderActivityTracker(unittest.TestCase):

    def setUp(self) -> None:
        self.tracker = MarketInsiderActivityTracker()

    def test_analyze_activity_none_stream_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            self.tracker.analyze_activity(None)

    def test_analyze_activity_empty_stream_raises_value_error(self) -> None:
        empty_stream = io.BytesIO(b"")
        with self.assertRaises(ValueError):
            self.tracker.analyze_activity(empty_stream)

    def test_analyze_activity_anomaly_detected(self) -> None:
        anomaly_keyword = uuid.uuid4().hex.encode('utf-8')
        payload = b"data " + anomaly_keyword + b" anomaly extra"
        stream = io.BytesIO(payload)
        
        result = self.tracker.analyze_activity(stream)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "ALERT")
        self.assertIn("signature", result)
        self.assertEqual(len(result["signature"]), 32)

    def test_analyze_activity_normal(self) -> None:
        random_bytes = uuid.uuid4().hex.encode('utf-8')
        stream = io.BytesIO(random_bytes)
        
        result = self.tracker.analyze_activity(stream)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "NORMAL")
        self.assertIn("signature", result)
        self.assertEqual(len(result["signature"]), 32)


class TestMarketInsiderActivityTrackerModuleAPI(unittest.TestCase):

    def test_track_activity_invalid_payload_type(self) -> None:
        invalid_payload = uuid.uuid4().hex
        result = MarketInsiderActivityTrackerModuleAPI.track_activity(invalid_payload)
        
        self.assertIsInstance(result, dict)
        self.assertFalse(result["anomaly_detected"])
        self.assertIsNone(result["ticker_id"])
        self.assertEqual(result["volume"], 0.0)
        self.assertIn("signature", result)

    def test_track_activity_normal_volume_and_multiplier(self) -> None:
        ticker = uuid.uuid4().hex[:8].upper()
        volume = float(random.randint(100, 400000))
        multiplier = round(random.uniform(1.0, 4.0), 2)
        
        payload = {
            "ticker_id": ticker,
            "volume": volume,
            "anomaly_multiplier": multiplier
        }
        
        result = MarketInsiderActivityTrackerModuleAPI.track_activity(payload)
        
        self.assertIsInstance(result, dict)
        self.assertFalse(result["anomaly_detected"])
        self.assertEqual(result["ticker_id"], ticker)
        self.assertEqual(result["volume"], volume)
        self.assertIn("signature", result)

    def test_track_activity_anomaly_high_volume(self) -> None:
        ticker = uuid.uuid4().hex[:8].upper()
        volume = float(random.randint(500001, 2000000))
        multiplier = round(random.uniform(1.0, 3.0), 2)
        
        payload = {
            "ticker_id": ticker,
            "volume": volume,
            "anomaly_multiplier": multiplier
        }
        
        result = MarketInsiderActivityTrackerModuleAPI.track_activity(payload)
        
        self.assertIsInstance(result, dict)
        self.assertTrue(result["anomaly_detected"])
        self.assertEqual(result["ticker_id"], ticker)
        self.assertEqual(result["volume"], volume)

    def test_track_activity_anomaly_high_multiplier(self) -> None:
        ticker = uuid.uuid4().hex[:8].upper()
        volume = float(random.randint(100, 400000))
        multiplier = round(random.uniform(5.1, 20.0), 2)
        
        payload = {
            "ticker_id": ticker,
            "volume": volume,
            "anomaly_multiplier": multiplier
        }
        
        result = MarketInsiderActivityTrackerModuleAPI.track_activity(payload)
        
        self.assertIsInstance(result, dict)
        self.assertTrue(result["anomaly_detected"])
        self.assertEqual(result["ticker_id"], ticker)

    def test_track_activity_malformed_numeric_inputs(self) -> None:
        ticker = uuid.uuid4().hex[:8].upper()
        payload = {
            "ticker_id": ticker,
            "volume": uuid.uuid4().hex,
            "anomaly_multiplier": uuid.uuid4().hex
        }
        
        result = MarketInsiderActivityTrackerModuleAPI.track_activity(payload)
        
        self.assertIsInstance(result, dict)
        self.assertFalse(result["anomaly_detected"])
        self.assertEqual(result["ticker_id"], ticker)
        self.assertEqual(result["volume"], 0.0)


class TestDBStorage(unittest.TestCase):

    def setUp(self) -> None:
        self.db_path = f"test_db_{uuid.uuid4().hex}.db"
        self.storage = DBStorage(db_path=self.db_path)

    def tearDown(self) -> None:
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except OSError:
                pass

    def test_save_and_get_last_activity(self) -> None:
        ticker = uuid.uuid4().hex[:6].upper()
        is_anomaly = random.choice([True, False])
        signature = uuid.uuid4().hex

        self.storage.save_activity(ticker, is_anomaly, signature)
        
        activity = self.storage.get_last_activity(ticker)
        
        self.assertIsNotNone(activity)
        self.assertEqual(activity["ticker"], ticker)
        self.assertEqual(activity["is_anomaly"], is_anomaly)
        self.assertEqual(activity["signature"], signature)

    def test_get_last_activity_nonexistent(self) -> None:
        nonexistent_ticker = uuid.uuid4().hex[:6].upper()
        activity = self.storage.get_last_activity(nonexistent_ticker)
        self.assertIsNone(activity)

    def test_get_last_activity_returns_most_recent(self) -> None:
        ticker = uuid.uuid4().hex[:6].upper()
        first_signature = uuid.uuid4().hex
        second_signature = uuid.uuid4().hex

        self.storage.save_activity(ticker, False, first_signature)
        self.storage.save_activity(ticker, True, second_signature)

        activity = self.storage.get_last_activity(ticker)
        
        self.assertIsNotNone(activity)
        self.assertEqual(activity["ticker"], ticker)
        self.assertTrue(activity["is_anomaly"])
        self.assertEqual(activity["signature"], second_signature)


if __name__ == "__main__":
    unittest.main()