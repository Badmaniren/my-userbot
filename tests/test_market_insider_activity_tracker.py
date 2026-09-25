import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string
import tempfile
import os
import sqlite3

from skills.market_insider_activity_tracker import (
    MarketInsiderActivityTracker,
    MarketInsiderActivityTrackerModuleAPI,
    DBStorage,
    MarketInsiderActivityTrackerModuleIdempotentProxy
)

class TestMarketInsiderActivityTrackerIntegration(unittest.TestCase):

    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        os.close(self.db_fd)
        self.db_storage = DBStorage(db_path=self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_market_insider_tracker_analyze_normal(self):
        tracker = MarketInsiderActivityTracker(db_storage=self.db_storage)
        random_payload = ''.join(random.choices(string.ascii_letters + string.digits, k=32)).encode('utf-8')
        stream = io.BytesIO(random_payload)
        
        result = tracker.analyze_activity(stream)
        self.assertEqual(result["status"], "NORMAL")
        self.assertIn("signature", result)

    def test_market_insider_tracker_analyze_anomaly(self):
        tracker = MarketInsiderActivityTracker(db_storage=self.db_storage)
        prefix = ''.join(random.choices(string.ascii_letters, k=10))
        anomaly_payload = f"{prefix}_anomaly_suffix".encode('utf-8')
        stream = io.BytesIO(anomaly_payload)
        
        result = tracker.analyze_activity(stream)
        self.assertEqual(result["status"], "ALERT")
        self.assertIn("signature", result)

    def test_market_insider_tracker_analyze_empty_stream(self):
        tracker = MarketInsiderActivityTracker(db_storage=self.db_storage)
        
        with self.assertRaises(ValueError):
            tracker.analyze_activity(None)
            
        with self.assertRaises(ValueError):
            tracker.analyze_activity(io.BytesIO(b""))

    def test_market_insider_module_api_track_activity_normal(self):
        ticker = uuid.uuid4().hex[:6].upper()
        volume = float(random.randint(100, 499999))
        multiplier = float(round(random.uniform(0.1, 4.9), 2))
        
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

    def test_market_insider_module_api_track_activity_anomaly(self):
        ticker = uuid.uuid4().hex[:6].upper()
        if random.choice([True, False]):
            volume = float(random.randint(500001, 1000000))
            multiplier = float(round(random.uniform(0.1, 4.9), 2))
        else:
            volume = float(random.randint(100, 499999))
            multiplier = float(round(random.uniform(5.1, 10.0), 2))
            
        payload = {
            "ticker_id": ticker,
            "volume": volume,
            "anomaly_multiplier": multiplier
        }
        
        result = MarketInsiderActivityTrackerModuleAPI.track_activity(payload)
        self.assertTrue(result["anomaly_detected"])
        self.assertEqual(result["ticker_id"], ticker)

    def test_market_insider_module_api_track_activity_invalid_payload(self):
        invalid_payloads = [
            uuid.uuid4().hex,
            random.randint(1, 100),
            None,
            [random.randint(1, 100), uuid.uuid4().hex]
        ]
        
        for payload in invalid_payloads:
            result = MarketInsiderActivityTrackerModuleAPI.track_activity(payload)
            self.assertIsInstance(result, dict)
            self.assertIn("anomaly_detected", result)
            self.assertIn("signature", result)

    def test_db_storage_save_and_get_activity(self):
        ticker = uuid.uuid4().hex[:6].upper()
        is_anomaly = random.choice([True, False])
        signature = uuid.uuid4().hex
        
        self.db_storage.save_activity(ticker, is_anomaly, signature)
        
        last_activity = self.db_storage.get_last_activity(ticker)
        self.assertIsNotNone(last_activity)
        self.assertEqual(last_activity["ticker"], ticker)
        self.assertEqual(last_activity["is_anomaly"], is_anomaly)
        self.assertEqual(last_activity["signature"], signature)

    def test_db_storage_get_nonexistent_activity(self):
        nonexistent_ticker = uuid.uuid4().hex[:6].upper()
        last_activity = self.db_storage.get_last_activity(nonexistent_ticker)
        self.assertIsNone(last_activity)

    def test_idempotent_proxy_alias(self):
        self.assertEqual(MarketInsiderActivityTrackerModuleIdempotentProxy, MarketInsiderActivityTrackerModuleAPI)

if __name__ == "__main__":
    unittest.main()