import unittest
import uuid
import random
import os
from skills.market_anomaly_detector import market_anomaly_detector
from skills.market_parser import market_parser
from skills.db_storage import db_storage

class TestMarketAnomalyDetectorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_symbol = f"TEST_{uuid.uuid4().hex[:6].upper()}"
        self.random_volume = random.randint(100000, 9999999)
        self.random_price = round(random.uniform(10.0, 500.0), 2)
        self.storage_path = f"data_anomaly_{uuid.uuid4().hex}.json"

    def tearDown(self):
        if os.path.exists(self.storage_path):
            try:
                os.remove(self.storage_path)
            except OSError:
                pass

    def test_detect_anomaly_with_real_parser_and_storage(self):
        parser_payload = {
            "symbol": self.test_symbol,
            "volume": self.random_volume,
            "price": self.random_price,
            "timestamp": uuid.uuid4().int
        }
        
        parsed_data = market_parser(parser_payload)
        self.assertIsNotNone(parsed_data, "Market parser returned None")

        anomaly_result = market_anomaly_detector(parsed_data)
        
        self.assertIsInstance(anomaly_result, dict, "Anomaly detector must return a dictionary")
        self.assertIn("is_anomaly", anomaly_result)
        self.assertIn("anomaly_score", anomaly_result)
        
        db_payload = {
            "id": str(uuid.uuid4()),
            "symbol": self.test_symbol,
            "anomaly_data": anomaly_result,
            "storage_file": self.storage_path
        }
        
        storage_status = db_storage(db_payload)
        self.assertTrue(storage_status, "DB storage failed to persist real anomaly data")
        self.assertTrue(os.path.exists(self.storage_path), "Integration failed: Storage file was not created")

if __name__ == "__main__":
    unittest.main()