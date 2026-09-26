import unittest
import uuid
import random
import os
import json
from skills.market_anomaly_detector import market_anomaly_detector

class TestMarketAnomalyDetectorIntegration(unittest.TestCase):
    def setUp(self):
        self.run_id = str(uuid.uuid4())
        self.price_factor = round(random.uniform(10.0, 100.0), 2)
        self.volume = random.randint(10000, 1000000)
        self.marker_file = f"anomaly_{self.run_id}.log"

    def tearDown(self):
        if os.path.exists(self.marker_file):
            try:
                os.remove(self.marker_file)
            except OSError:
                pass

    def test_market_anomaly_detector_integration_flow(self):
        test_data = {
            "run_id": self.run_id,
            "price_factor": self.price_factor,
            "volume": self.volume
        }

        result = market_anomaly_detector(test_data)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("run_id"), self.run_id)
        self.assertEqual(result.get("price_factor"), self.price_factor)
        self.assertEqual(result.get("volume"), self.volume)

        expected_anomaly = self.price_factor > 50.0 or self.volume > 500000
        self.assertEqual(result.get("anomaly_detected"), expected_anomaly)

        self.assertTrue(os.path.exists(self.marker_file), f"Marker file {self.marker_file} was not created.")

        with open(self.marker_file, "r") as f:
            file_content = f.read()
            stored_data = json.loads(file_content)
            self.assertEqual(stored_data.get("run_id"), self.run_id)
            self.assertEqual(stored_data.get("anomaly_detected"), expected_anomaly)

if __name__ == "__main__":
    unittest.main()
