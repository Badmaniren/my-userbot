import unittest
import uuid
import random
import os
from skills.market_anomaly_detector import market_anomaly_detector
from skills.db_storage import db_storage

class TestMarketAnomalyDetectorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_market_id = f"MARKET_{uuid.uuid4().hex[:8]}"
        self.test_anomaly_value = round(random.uniform(100.5, 9999.9), 2)
        self.session_id = str(uuid.uuid4())

    def test_anomaly_detection_and_db_persistence_integration(self):
        raw_payload = {
            "session_id": self.session_id,
            "market_id": self.test_market_id,
            "metric": "volatility_spike",
            "value": self.test_anomaly_value,
            "timestamp": random.randint(1600000000, 1700000000)
        }

        detection_result = market_anomaly_detector(raw_payload)

        self.assertIsInstance(detection_result, dict)
        self.assertIn("anomaly_id", detection_result)
        self.assertEqual(detection_result.get("market_id"), self.test_market_id)
        self.assertTrue(detection_result.get("is_anomaly"))

        stored_record = db_storage({
            "action": "get",
            "table": "market_anomalies",
            "anomaly_id": detection_result["anomaly_id"]
        })

        self.assertIsNotNone(stored_record)
        self.assertEqual(stored_record.get("market_id"), self.test_market_id)
        self.assertEqual(float(stored_record.get("value")), self.test_anomaly_value)

    def test_error_handling_no_silent_passes(self):
        invalid_payload = {
            "session_id": self.session_id,
            "market_id": None,
            "value": "CORRUPTED_DATA_BYPASS"
        }

        with self.assertRaises((ValueError, TypeError, KeyError)):
            market_anomaly_detector(invalid_payload)

if __name__ == "__main__":
    unittest.main()