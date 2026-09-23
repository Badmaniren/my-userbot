import unittest
from unittest.mock import patch
import io
import uuid
import random
from skills.market_insider_activity_tracker import (
    MarketInsiderActivityTracker,
    MarketInsiderActivityTrackerModuleAPI,
    MarketInsiderActivityTrackerModuleIdempotentProxy
)

class TestMarketInsiderActivityTracker(unittest.TestCase):
    def setUp(self):
        self.dep_key_1 = uuid.uuid4().hex
        self.dep_val_1 = uuid.uuid4().hex
        self.tracker = MarketInsiderActivityTracker(**{self.dep_key_1: self.dep_val_1})

    def test_analyze_activity_normal(self):
        rand_word = uuid.uuid4().hex
        stream_content = f"market data payload {rand_word}".encode('utf-8')
        mock_stream = io.BytesIO(stream_content)
        
        result = self.tracker.analyze_activity(mock_stream)
        
        self.assertEqual(result["status"], "NORMAL")
        self.assertIn("signature", result)
        self.assertTrue(isinstance(result["signature"], str))
        self.assertEqual(len(result["signature"]), 32)

    def test_analyze_activity_anomaly(self):
        rand_anomaly_word = uuid.uuid4().hex
        stream_content = f"critical anomaly detected {rand_anomaly_word}".encode('utf-8')
        mock_stream = io.BytesIO(stream_content)
        
        result = self.tracker.analyze_activity(mock_stream)
        
        self.assertEqual(result["status"], "ALERT")
        self.assertIn("signature", result)
        self.assertTrue(isinstance(result["signature"], str))

    def test_analyze_activity_empty_stream(self):
        mock_stream = io.BytesIO(b"")
        
        with self.assertRaises(ValueError) as ctx:
            self.tracker.analyze_activity(mock_stream)
        
        self.assertEqual(str(ctx.exception), "Empty stream")

    def test_track_activity_normal(self):
        ticker = uuid.uuid4().hex[:8].upper()
        volume = float(random.randint(100, 499999))
        multiplier = round(random.uniform(0.1, 4.9), 2)
        
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

    def test_track_activity_anomaly_by_volume(self):
        ticker = uuid.uuid4().hex[:8].upper()
        volume = float(random.randint(500001, 2000000))
        multiplier = round(random.uniform(0.1, 4.9), 2)
        
        payload = {
            "ticker_id": ticker,
            "volume": volume,
            "anomaly_multiplier": multiplier
        }
        
        result = MarketInsiderActivityTrackerModuleAPI.track_activity(payload)
        
        self.assertTrue(result["anomaly_detected"])
        self.assertEqual(result["ticker_id"], ticker)
        self.assertEqual(result["volume"], volume)

    def test_track_activity_anomaly_by_multiplier(self):
        ticker = uuid.uuid4().hex[:8].upper()
        volume = float(random.randint(100, 499999))
        multiplier = round(random.uniform(5.1, 20.0), 2)
        
        payload = {
            "ticker_id": ticker,
            "volume": volume,
            "anomaly_multiplier": multiplier
        }
        
        result = MarketInsiderActivityTrackerModuleAPI.track_activity(payload)
        
        self.assertTrue(result["anomaly_detected"])
        self.assertEqual(result["ticker_id"], ticker)
        self.assertEqual(result["volume"], volume)

    def test_proxy_reference(self):
        self.assertIs(MarketInsiderActivityTrackerModuleIdempotentProxy, MarketInsiderActivityTrackerModuleAPI)