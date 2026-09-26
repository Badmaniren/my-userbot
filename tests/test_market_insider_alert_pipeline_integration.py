import unittest
import uuid
import random
import io
from skills.market_insider_alert_pipeline import MarketInsiderAlertPipeline, market_insider_alert_pipeline
from skills.market_insider_activity_tracker import MarketInsiderActivityTracker
from skills.market_anomaly_detector import MarketAnomalyDetector


class TestMarketInsiderAlertPipelineIntegration(unittest.TestCase):

    def setUp(self):
        self.pipeline = MarketInsiderAlertPipeline()
        self.random_ticker = f"TICKER_{uuid.uuid4().hex[:6].upper()}"
        self.random_score = round(random.uniform(0.1, 0.9), 4)

    def test_pipeline_integration_flow(self):
        raw_stream_data = io.BytesIO(f"Volume spike detected for {self.random_ticker} with score {self.random_score}".encode('utf-8'))
        
        alert = self.pipeline.process_alert_stream(self.random_ticker, raw_stream_data)
        
        if alert is not None:
            self.assertIn("ticker", alert)
            self.assertEqual(alert["ticker"], self.random_ticker)
            self.assertIn("is_anomaly", alert)
            self.assertIn("anomaly_score", alert)
            self.assertIsInstance(alert["anomaly_score"], (int, float))

    def test_market_insider_alert_pipeline_wrapper(self):
        payload = {
            "ticker": self.random_ticker,
            "stream": io.BytesIO(uuid.uuid4().bytes),
            "signature": uuid.uuid4().hex
        }
        
        result = market_insider_alert_pipeline(payload)
        
        self.assertIsInstance(result, dict)
        self.assertIn("alert_id", result)
        self.assertEqual(result["ticker"], self.random_ticker)
        self.assertEqual(result["signature"], payload["signature"])
        self.assertIn("analysis", result)
        self.assertIn("anomaly", result)


if __name__ == "__main__":
    unittest.main()