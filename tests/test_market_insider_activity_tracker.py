import io
import random
import unittest
import uuid
from unittest.mock import patch

from skills.market_insider_activity_tracker import (
    MarketInsiderActivityTracker,
    MarketInsiderActivityTrackerModuleAPI,
    market_insider_activity_tracker,
    MarketInsiderActivityTrackerModuleIdempotentProxy
)

class TestMarketInsiderActivityTracker(unittest.TestCase):

    def setUp(self):
        self.random_dep_key_1 = f"dep_{uuid.uuid4().hex}"
        self.random_dep_val_1 = uuid.uuid4().hex
        self.random_dep_key_2 = f"dep_{uuid.uuid4().hex}"
        self.random_dep_val_2 = uuid.uuid4().hex
        
        self.tracker = MarketInsiderActivityTracker(**{
            self.random_dep_key_1: self.random_dep_val_1,
            self.random_dep_key_2: self.random_dep_val_2
        })

    def test_initialization_dependencies(self):
        self.assertEqual(self.tracker.deps[self.random_dep_key_1], self.random_dep_val_1)
        self.assertEqual(self.tracker.deps[self.random_dep_key_2], self.random_dep_val_2)

    def test_analyze_activity_empty_stream_raises_value_error(self):
        empty_stream = io.BytesIO(b"")
        with self.assertRaises(ValueError) as context:
            self.tracker.analyze_activity(empty_stream)
        self.assertEqual(str(context.exception), "Empty stream")

    def test_analyze_activity_normal_stream(self):
        random_normal_bytes = bytes(random.choices(range(65, 90), k=random.randint(10, 50)))
        stream = io.BytesIO(random_normal_bytes)
        
        random_uuid = uuid.uuid4()
        with patch('uuid.uuid4', return_value=random_uuid):
            result = self.tracker.analyze_activity(stream)
            
        self.assertEqual(result["status"], "NORMAL")
        self.assertEqual(result["signature"], random_uuid.hex)

    def test_analyze_activity_anomaly_stream(self):
        prefix = bytes(random.choices(range(65, 90), k=random.randint(5, 20)))
        suffix = bytes(random.choices(range(65, 90), k=random.randint(5, 20)))
        anomaly_bytes = prefix + b"anomaly" + suffix
        stream = io.BytesIO(anomaly_bytes)
        
        random_uuid = uuid.uuid4()
        with patch('uuid.uuid4', return_value=random_uuid):
            result = self.tracker.analyze_activity(stream)
            
        self.assertEqual(result["status"], "ALERT")
        self.assertEqual(result["signature"], random_uuid.hex)


class TestMarketInsiderActivityTrackerModuleAPI(unittest.TestCase):

    def test_track_activity_normal_case(self):
        random_ticker = f"TICKER_{uuid.uuid4().hex[:6].upper()}"
        random_volume = random.uniform(0.0, 500000.0)
        random_multiplier = random.uniform(0.0, 5.0)
        
        payload = {
            "ticker_id": random_ticker,
            "volume": random_volume,
            "anomaly_multiplier": random_multiplier
        }
        
        random_uuid = uuid.uuid4()
        with patch('uuid.uuid4', return_value=random_uuid):
            result = MarketInsiderActivityTrackerModuleAPI.track_activity(payload)
            
        self.assertFalse(result["anomaly_detected"])
        self.assertEqual(result["ticker_id"], random_ticker)
        self.assertEqual(result["volume"], random_volume)
        self.assertEqual(result["signature"], random_uuid.hex)

    def test_track_activity_anomaly_by_volume(self):
        random_ticker = f"TICKER_{uuid.uuid4().hex[:6].upper()}"
        random_volume = random.uniform(500000.01, 10000000.0)
        random_multiplier = random.uniform(0.0, 5.0)
        
        payload = {
            "ticker_id": random_ticker,
            "volume": random_volume,
            "anomaly_multiplier": random_multiplier
        }
        
        random_uuid = uuid.uuid4()
        with patch('uuid.uuid4', return_value=random_uuid):
            result = MarketInsiderActivityTrackerModuleAPI.track_activity(payload)
            
        self.assertTrue(result["anomaly_detected"])
        self.assertEqual(result["ticker_id"], random_ticker)
        self.assertEqual(result["volume"], random_volume)
        self.assertEqual(result["signature"], random_uuid.hex)

    def test_track_activity_anomaly_by_multiplier(self):
        random_ticker = f"TICKER_{uuid.uuid4().hex[:6].upper()}"
        random_volume = random.uniform(0.0, 500000.0)
        random_multiplier = random.uniform(5.01, 100.0)
        
        payload = {
            "ticker_id": random_ticker,
            "volume": random_volume,
            "anomaly_multiplier": random_multiplier
        }
        
        random_uuid = uuid.uuid4()
        with patch('uuid.uuid4', return_value=random_uuid):
            result = MarketInsiderActivityTrackerModuleAPI.track_activity(payload)
            
        self.assertTrue(result["anomaly_detected"])
        self.assertEqual(result["ticker_id"], random_ticker)
        self.assertEqual(result["volume"], random_volume)
        self.assertEqual(result["signature"], random_uuid.hex)

    def test_track_activity_defaults(self):
        random_ticker = f"TICKER_{uuid.uuid4().hex[:6].upper()}"
        payload = {
            "ticker_id": random_ticker
        }
        
        random_uuid = uuid.uuid4()
        with patch('uuid.uuid4', return_value=random_uuid):
            result = MarketInsiderActivityTrackerModuleAPI.track_activity(payload)
            
        self.assertFalse(result["anomaly_detected"])
        self.assertEqual(result["ticker_id"], random_ticker)
        self.assertEqual(result["volume"], 0)
        self.assertEqual(result["signature"], random_uuid.hex)


class TestModuleAliases(unittest.TestCase):

    def test_aliases_point_to_correct_api_class(self):
        self.assertIs(market_insider_activity_tracker, MarketInsiderActivityTrackerModuleAPI)
        self.assertIs(MarketInsiderActivityTrackerModuleIdempotentProxy, MarketInsiderActivityTrackerModuleAPI)


if __name__ == "__main__":
    unittest.main()