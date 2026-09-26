import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import sys
import types

from skills.market_insider_alert_pipeline import MarketInsiderAlertPipeline

class TestMarketInsiderAlertPipeline(unittest.TestCase):

    def setUp(self):
        self.ticker = "".join(random.choices(string.ascii_uppercase, k=5))
        self.exchange = "".join(random.choices(string.ascii_uppercase, k=4))
        self.raw_stream_data = f"DATA_{uuid.uuid4().hex}"
        self.anomaly_score = random.uniform(0.1, 0.99)
        self.signature_val = uuid.uuid4().hex

    @patch('skills.market_insider_alert_pipeline.MarketInsiderActivityTracker')
    @patch('skills.market_insider_alert_pipeline.MarketAnomalyDetector')
    def test_pipeline_execution_success(self, mock_anomaly_detector_cls, mock_tracker_cls):
        mock_tracker_instance = mock_tracker_cls.return_value
        mock_tracker_instance.analyze_activity.return_value = {
            "ticker": self.ticker,
            "signature": self.signature_val,
            "status": "suspicious"
        }

        mock_detector_instance = mock_anomaly_detector_cls.return_value
        mock_detector_instance.detect.return_value = {
            "anomaly_score": self.anomaly_score,
            "is_anomaly": True
        }

        pipeline = MarketInsiderAlertPipeline()
        alert = pipeline.process_alert_stream(self.ticker, self.raw_stream_data)

        self.assertIsNotNone(alert)
        self.assertEqual(alert["ticker"], self.ticker)
        self.assertEqual(alert["signature"], self.signature_val)
        self.assertTrue(alert["is_anomaly"])
        
        mock_tracker_instance.analyze_activity.assert_called_once_with(self.raw_stream_data)
        mock_detector_instance.detect.assert_called_once_with(self.ticker)

    @patch('skills.market_insider_alert_pipeline.MarketInsiderActivityTracker')
    @patch('skills.market_insider_alert_pipeline.MarketAnomalyDetector')
    def test_pipeline_no_anomaly(self, mock_anomaly_detector_cls, mock_tracker_cls):
        mock_tracker_instance = mock_tracker_cls.return_value
        mock_tracker_instance.analyze_activity.return_value = {
            "ticker": self.ticker,
            "signature": self.signature_val,
            "status": "normal"
        }

        mock_detector_instance = mock_anomaly_detector_cls.return_value
        mock_detector_instance.detect.return_value = {
            "anomaly_score": 0.01,
            "is_anomaly": False
        }

        pipeline = MarketInsiderAlertPipeline()
        alert = pipeline.process_alert_stream(self.ticker, io.BytesIO(self.raw_stream_data.encode('utf-8')))

        self.assertIsNone(alert)
        mock_tracker_instance.analyze_activity.assert_called_once()
        mock_detector_instance.detect.assert_called_once_with(self.ticker)

    @patch('skills.market_insider_alert_pipeline.MarketInsiderActivityTracker')
    @patch('skills.market_insider_alert_pipeline.MarketAnomalyDetector')
    def test_stream_analysis_integration(self, mock_anomaly_detector_cls, mock_tracker_cls):
        mock_detector_instance = mock_anomaly_detector_cls.return_value
        mock_detector_instance.analyze_stream.return_value = [
            {"ticker": self.ticker, "score": self.anomaly_score}
        ]

        pipeline = MarketInsiderAlertPipeline()
        stream_results = pipeline.evaluate_market_stream(self.exchange)

        self.assertIsInstance(stream_results, list)
        self.assertEqual(len(stream_results), 1)
        self.assertEqual(stream_results[0]["ticker"], self.ticker)
        self.assertEqual(stream_results[0]["score"], self.anomaly_score)
        mock_detector_instance.analyze_stream.assert_called_once_with(self.exchange)

if __name__ == '__main__':
    unittest.main()