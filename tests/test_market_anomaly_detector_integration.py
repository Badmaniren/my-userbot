import unittest
import uuid
import random
from skills.market_anomaly_detector import MarketAnomalyDetector, market_anomaly_detector_main

class RealMarketParser:
    def parse(self, ticker):
        return {
            "ticker": ticker,
            "volume": random.randint(1000, 10000000),
            "anomaly_id": str(uuid.uuid4())
        }

class RealDbStorage:
    def __init__(self):
        self.saved_records = []
    def save(self, record):
        self.saved_records.append(record)

class RealAlertDispatcher:
    def __init__(self):
        self.dispatched = []
    def dispatch(self, record):
        self.dispatched.append(record)

class TestMarketAnomalyDetectorIntegration(unittest.TestCase):
    def test_end_to_end_anomaly_detection_pipeline(self):
        unique_ticker = f"TICK_{uuid.uuid4().hex[:6].upper()}"
        unique_run_id = str(uuid.uuid4())

        parser = RealMarketParser()
        db = RealDbStorage()
        dispatcher = RealAlertDispatcher()

        detector = MarketAnomalyDetector(
            db_storage=db,
            market_parser=parser,
            market_portfolio_alert_dispatcher=dispatcher
        )

        analysis_result = detector.analyze_market_stream(unique_ticker)

        self.assertEqual(analysis_result.get("ticker"), unique_ticker)
        self.assertIn("volume", analysis_result)
        self.assertIn("anomaly_id", analysis_result)

        self.assertEqual(len(db.saved_records), 1)
        self.assertEqual(db.saved_records[0]["ticker"], unique_ticker)
        self.assertEqual(db.saved_records[0]["anomaly_id"], analysis_result["anomaly_id"])

        self.assertEqual(len(dispatcher.dispatched), 1)
        self.assertEqual(dispatcher.dispatched[0]["anomaly_id"], analysis_result["anomaly_id"])

        random_price = round(random.uniform(500.0, 2000.0), 2)
        random_volume = random.randint(100, 10000000)
        random_activity = round(random.uniform(0.0, 1.0), 2)

        payload = {
            "run_id": unique_run_id,
            "market_data": {
                "price": random_price,
                "volume": random_volume
            },
            "insider_metrics": {
                "activity_index": random_activity
            },
            "threshold": 0.5
        }

        main_result = market_anomaly_detector_main(payload)

        self.assertEqual(main_result["run_id"], unique_run_id)
        self.assertEqual(main_result["price"], random_price)
        self.assertEqual(main_result["volume"], random_volume)
        self.assertEqual(main_result["activity_index"], random_activity)

        expected_anomaly = (random_price > 1000.0 and random_volume > 5000000) or (random_activity > 0.5)
        self.assertEqual(main_result["anomaly_detected"], expected_anomaly)

if __name__ == "__main__":
    unittest.main()