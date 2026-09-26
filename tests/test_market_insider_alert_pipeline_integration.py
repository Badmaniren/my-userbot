import unittest
import uuid
import random
import io
from skills.market_insider_alert_pipeline import MarketInsiderAlertPipeline, market_insider_alert_pipeline
from skills.market_insider_activity_tracker import MarketInsiderActivityTracker, DBStorage
from skills.market_anomaly_detector import MarketAnomalyDetector


class TestMarketInsiderAlertPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.pipeline = MarketInsiderAlertPipeline()
        self.random_ticker = f"TICKER_{uuid.uuid4().hex[:6].upper()}"
        self.random_signature = f"SIG_{uuid.uuid4().hex}"
        self.random_exchange = f"EXCH_{random.randint(100, 999)}"

    def test_pipeline_class_alert_processing(self):
        raw_data = {
            "ticker": self.random_ticker,
            "signature": self.random_signature,
            "volume": random.randint(10000, 500000),
            "price": round(random.uniform(10.0, 1000.0), 2)
        }
        
        stream_data = io.BytesIO(str(raw_data).encode('utf-8'))
        result = self.pipeline.process_alert_stream(self.random_ticker, stream_data)
        
        if result is not None:
            self.assertIn("ticker", result)
            self.assertEqual(result["ticker"], self.random_ticker)
            self.assertIn("is_anomaly", result)
            self.assertIn("anomaly_score", result)

    def test_pipeline_functional_wrapper(self):
        raw_data = {
            "ticker": self.random_ticker,
            "signature": self.random_signature,
            "payload_id": uuid.uuid4().hex,
            "metric": random.random()
        }
        
        result = market_insider_alert_pipeline(raw_data)
        
        self.assertIsInstance(result, dict)
        self.assertIn("alert_id", result)
        self.assertTrue(len(result["alert_id"]) > 0)
        self.assertEqual(result["ticker"], self.random_ticker)
        self.assertEqual(result["signature"], self.random_signature)
        self.assertIn("analysis", result)
        self.assertIn("anomaly", result)

    def test_evaluate_market_stream_integration(self):
        stream_analysis = self.pipeline.evaluate_market_stream(self.random_exchange)
        self.assertIsNotNone(stream_analysis)


if __name__ == "__main__":
    unittest.main()