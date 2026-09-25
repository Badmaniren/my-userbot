import unittest
from unittest.mock import patch
import io
import uuid
import random
import string
import os

from skills.market_insider_activity_tracker import (
    MarketInsiderActivityTracker,
    MarketInsiderActivityTrackerModuleAPI,
    DBStorage
)


class TestMarketInsiderActivityTracker(unittest.TestCase):
    def setUp(self) -> None:
        self.rand_str = "".join(random.choices(string.ascii_letters, k=10))
        self.tracker = MarketInsiderActivityTracker()

    def test_analyze_activity_none_stream(self) -> None:
        with self.assertRaises(ValueError):
            self.tracker.analyze_activity(None)

    def test_analyze_activity_empty_stream(self) -> None:
        empty_stream = io.BytesIO(b"")
        with self.assertRaises(ValueError):
            self.tracker.analyze_activity(empty_stream)

    def test_analyze_activity_normal(self) -> None:
        normal_data = f"data_{self.rand_str}".encode("utf-8")
        stream = io.BytesIO(normal_data)
        result = self.tracker.analyze_activity(stream)
        self.assertEqual(result["status"], "NORMAL")
        self.assertIn("signature", result)
        self.assertEqual(len(result["signature"]), 32)

    def test_analyze_activity_anomaly(self) -> None:
        anomaly_data = f"anomaly_{self.rand_str}".encode("utf-8")
        stream = io.BytesIO(anomaly_data)
        result = self.tracker.analyze_activity(stream)
        self.assertEqual(result["status"], "ALERT")
        self.assertIn("signature", result)
        self.assertEqual(len(result["signature"]), 32)


class TestMarketInsiderActivityTrackerModuleAPI(unittest.TestCase):
    def setUp(self) -> None:
        self.ticker_id = f"TICKER_{uuid.uuid4().hex[:6].upper()}"

    def test_track_activity_invalid_payload_type(self) -> None:
        invalid_payload = f"not_a_dict_{uuid.uuid4().hex}"
        result = MarketInsiderActivityTrackerModuleAPI.track_activity(invalid_payload)
        self.assertFalse(result["anomaly_detected"])
        self.assertIsNone(result["ticker_id"])
        self.assertEqual(result["volume"], 0.0)
        self.assertIn("signature", result)

    def test_track_activity_normal_metrics(self) -> None:
        volume = float(random.randint(100, 400000))
        multiplier = round(random.uniform(1.0, 4.0), 2)
        payload = {
            "ticker_id": self.ticker_id,
            "volume": volume,
            "anomaly_multiplier": multiplier
        }
        result = MarketInsiderActivityTrackerModuleAPI.track_activity(payload)
        self.assertFalse(result["anomaly_detected"])
        self.assertEqual(result["ticker_id"], self.ticker_id)
        self.assertEqual(result["volume"], volume)
        self.assertIn("signature", result)

    def test_track_activity_anomaly_volume(self) -> None:
        volume = float(random.randint(500001, 1000000))
        multiplier = round(random.uniform(1.0, 4.0), 2)
        payload = {
            "ticker_id": self.ticker_id,
            "volume": volume,
            "anomaly_multiplier": multiplier
        }
        result = MarketInsiderActivityTrackerModuleAPI.track_activity(payload)
        self.assertTrue(result["anomaly_detected"])
        self.assertEqual(result["ticker_id"], self.ticker_id)
        self.assertEqual(result["volume"], volume)

    def test_track_activity_anomaly_multiplier(self) -> None:
        volume = float(random.randint(100, 400000))
        multiplier = round(random.uniform(5.1, 10.0), 2)
        payload = {
            "ticker_id": self.ticker_id,
            "volume": volume,
            "anomaly_multiplier": multiplier
        }
        result = MarketInsiderActivityTrackerModuleAPI.track_activity(payload)
        self.assertTrue(result["anomaly_detected"])
        self.assertEqual(result["ticker_id"], self.ticker_id)

    def test_track_activity_malformed_numeric_fields(self) -> None:
        payload = {
            "ticker_id": self.ticker_id,
            "volume": f"bad_vol_{uuid.uuid4().hex}",
            "anomaly_multiplier": f"bad_mult_{uuid.uuid4().hex}"
        }
        result = MarketInsiderActivityTrackerModuleAPI.track_activity(payload)
        self.assertFalse(result["anomaly_detected"])
        self.assertEqual(result["ticker_id"], self.ticker_id)
        self.assertEqual(result["volume"], 0.0)


class TestDBStorage(unittest.TestCase):
    def setUp(self) -> None:
        self.db_path = f"test_{uuid.uuid4().hex}.db"
        self.storage = DBStorage(db_path=self.db_path)
        self.ticker = f"T_{uuid.uuid4().hex[:5].upper()}"
        self.signature = uuid.uuid4().hex

    def tearDown(self) -> None:
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_save_and_get_last_activity_normal(self) -> None:
        is_anomaly = False
        self.storage.save_activity(self.ticker, is_anomaly, self.signature)
        
        last_activity = self.storage.get_last_activity(self.ticker)
        self.assertIsNotNone(last_activity)
        self.assertEqual(last_activity["ticker"], self.ticker)
        self.assertFalse(last_activity["is_anomaly"])
        self.assertEqual(last_activity["signature"], self.signature)

    def test_save_and_get_last_activity_anomaly(self) -> None:
        is_anomaly = True
        self.storage.save_activity(self.ticker, is_anomaly, self.signature)
        
        last_activity = self.storage.get_last_activity(self.ticker)
        self.assertIsNotNone(last_activity)
        self.assertEqual(last_activity["ticker"], self.ticker)
        self.assertTrue(last_activity["is_anomaly"])
        self.assertEqual(last_activity["signature"], self.signature)

    def test_get_nonexistent_activity(self) -> None:
        non_existent_ticker = f"NONE_{uuid.uuid4().hex[:5]}"
        last_activity = self.storage.get_last_activity(non_existent_ticker)
        self.assertIsNone(last_activity)


if __name__ == "__main__":
    unittest.main()