import unittest
import uuid
import random
from skills.market_insider_activity_tracker import MarketInsiderActivityTracker, DBStorage
from skills.market_anomaly_detector import MarketAnomalyDetector
from skills.market_insider_alert_pipeline import market_insider_alert_pipeline


class TestMarketInsiderAlertPipelineIntegration(unittest.TestCase):

    def setUp(self):
        self.ticker = f"TICK_{uuid.uuid4().hex[:6].upper()}"
        self.exchange = f"EXCH_{random.choice(['NYSE', 'NASDAQ', 'LSE', 'HKEX'])}"
        self.volume = round(random.uniform(10000.0, 5000000.0), 2)
        self.price = round(random.uniform(10.0, 1000.0), 2)
        self.db_path = f"test_market_{uuid.uuid4().hex}.db"
        
        self.raw_data = {
            "ticker": self.ticker,
            "exchange": self.exchange,
            "volume": self.volume,
            "price": self.price,
            "signature": uuid.uuid4().hex
        }

    def test_market_insider_alert_pipeline_composition(self):
        tracker = MarketInsiderActivityTracker()
        detector = MarketAnomalyDetector()
        storage = DBStorage(db_path=self.db_path)

        analysis_result = tracker.analyze_activity(self.raw_data)
        self.assertIsInstance(analysis_result, dict)

        anomaly_result = detector.detect(self.ticker)
        
        storage.save_activity(
            ticker=self.ticker,
            is_anomaly=bool(anomaly_result),
            signature=self.raw_data["signature"]
        )

        last_activity = storage.get_last_activity(self.ticker)
        self.assertIsNotNone(last_activity)
        self.assertEqual(last_activity.get("ticker"), self.ticker)

        pipeline_result = market_insider_alert_pipeline(self.raw_data)
        
        self.assertIsNotNone(pipeline_result)
        self.assertIsInstance(pipeline_result, dict)
        self.assertIn("alert_id", pipeline_result)
        self.assertEqual(pipeline_result.get("ticker"), self.ticker)


if __name__ == "__main__":
    unittest.main()