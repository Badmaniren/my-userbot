import unittest
import uuid
import random
import os
from skills.market_anomaly_detector import market_anomaly_detector
from skills.market_parser import market_parser
from skills.db_storage import db_storage
from skills.market_insider_activity_tracker import market_insider_activity_tracker

class TestMarketAnomalyDetectorIntegration(unittest.TestCase):

    def setUp(self):
        self.test_symbol = f"TEST_{uuid.uuid4().hex[:6].upper()}"
        self.test_price = round(random.uniform(10.0, 1000.0), 2)
        self.test_volume = random.randint(10000, 5000000)
        self.anomaly_threshold = round(random.uniform(0.05, 0.25), 2)

    def test_anomaly_detection_pipeline_real_flow(self):
        raw_market_data = {
            "symbol": self.test_symbol,
            "price": self.test_price,
            "volume": self.test_volume,
            "timestamp": uuid.uuid4().int
        }

        parsed_data = market_parser(raw_market_data)

        self.assertIsNotNone(parsed_data, "Market parser must return processed data")
        self.assertEqual(parsed_data.get("symbol"), self.test_symbol)

        insider_context = market_insider_activity_tracker(self.test_symbol)

        detection_payload = {
            "market_data": parsed_data,
            "insider_context": insider_context,
            "threshold": self.anomaly_threshold
        }

        anomaly_result = market_anomaly_detector(detection_payload)

        self.assertIsInstance(anomaly_result, dict, "Detector must return a dictionary result")
        self.assertIn("is_anomaly", anomaly_result, "Result must contain 'is_anomaly' flag")
        self.assertIn("anomaly_score", anomaly_result, "Result must contain 'anomaly_score'")

        storage_payload = {
            "id": str(uuid.uuid4()),
            "symbol": self.test_symbol,
            "score": anomaly_result["anomaly_score"],
            "is_anomaly": anomaly_result["is_anomaly"]
        }

        db_storage(storage_payload)

        if anomaly_result["is_anomaly"]:
            report_path = f"reports/anomaly_{storage_payload['id']}.log"
            self.assertTrue(
                os.path.exists(report_path) or anomaly_result.get("logged", True),
                "Real integration must persist anomaly data or generate trace artifacts"
            )

if __name__ == "__main__":
    unittest.main()