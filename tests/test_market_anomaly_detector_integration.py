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
        self.random_price = round(random.uniform(10.0, 1000.0), 2)
        self.random_volume = random.randint(10000, 1000000)
        self.anomaly_report_path = f"anomaly_report_{uuid.uuid4().hex}.json"

    def tearDown(self):
        if os.path.exists(self.anomaly_report_path):
            try:
                os.remove(self.anomaly_report_path)
            except OSError:
                pass

    def test_market_anomaly_detector_integration_with_parser(self):
        raw_market_data = market_parser(
            symbol=self.test_symbol,
            price=self.random_price,
            volume=self.random_volume
        )

        self.assertIsNotNone(raw_market_data, "Market parser must return valid market data structure.")

        detection_result = market_anomaly_detector(
            market_data=raw_market_data,
            output_file=self.anomaly_report_path,
            threshold=random.uniform(1.1, 5.0)
        )

        self.assertIsInstance(detection_result, dict, "Anomaly detector must return a dictionary result.")
        self.assertIn("anomaly_id", detection_result, "Result must contain a generated anomaly identifier.")
        self.assertEqual(detection_result.get("symbol"), self.test_symbol, "Anomaly symbol must match the input symbol.")

        self.assertTrue(
            os.path.exists(self.anomaly_report_path),
            "Integration failure: The anomaly detector must generate a physical report file."
        )

        stored_record = db_storage(
            query_id=detection_result["anomaly_id"],
            payload=detection_result
        )
        self.assertIsNotNone(stored_record, "Database storage must persist the anomaly event without failing.")

if __name__ == "__main__":
    unittest.main()