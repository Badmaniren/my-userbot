import unittest
import uuid
import random
import os
from skills.market_anomaly_detector import MarketAnomalyDetector
from skills.market_insider_alert_pipeline import MarketInsiderAlertPipeline
from skills.market_insider_anomaly_analyzer import analyze_market_insider_anomalies

class TestMarketInsiderAnomalyAnalyzerIntegration(unittest.TestCase):
    def setUp(self):
        self.ticker = f"TICKER_{uuid.uuid4().hex[:6].upper()}"
        self.exchange = f"EXCHANGE_{uuid.uuid4().hex[:6].upper()}"
        self.raw_stream_data = {
            "transaction_id": str(uuid.uuid4()),
            "volume": random.randint(10000, 500000),
            "price_delta": random.uniform(0.01, 0.15),
            "timestamp": random.randint(1600000000, 1700000000)
        }

    def test_real_composition_and_execution(self):
        detector = MarketAnomalyDetector()
        pipeline = MarketInsiderAlertPipeline()
        
        self.assertIsNotNone(detector)
        self.assertIsNotNone(pipeline)

        analysis_result = analyze_market_insider_anomalies(
            ticker=self.ticker,
            exchange=self.exchange,
            raw_stream_data=self.raw_stream_data
        )

        self.assertIsInstance(analysis_result, dict)
        self.assertIn("correlation_id", analysis_result)
        self.assertIn("coordinated_activity_detected", analysis_result)
        
        expected_keys = ["ticker", "exchange", "anomaly_data", "insider_alert_data"]
        for key in expected_keys:
            self.assertIn(key, analysis_result)

        self.assertEqual(analysis_result["ticker"], self.ticker)
        self.assertEqual(analysis_result["exchange"], self.exchange)

        report_filename = f"insider_anomaly_report_{analysis_result['correlation_id']}.json"
        if os.path.exists(report_filename):
            os.remove(report_filename)

if __name__ == "__main__":
    unittest.main()