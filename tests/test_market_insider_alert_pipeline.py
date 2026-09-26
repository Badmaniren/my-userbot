import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.market_insider_alert_pipeline import (
    MarketInsiderAlertPipeline,
    market_insider_alert_pipeline
)


class TestMarketInsiderAlertPipeline(unittest.TestCase):

    def setUp(self):
        self.pipeline = MarketInsiderAlertPipeline()
        self.random_ticker = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.random_signature = uuid.uuid4().hex
        self.random_exchange = uuid.uuid4().hex
        self.random_score = random.uniform(0.1, 0.9)

    def test_process_alert_stream_suspicious_and_anomaly(self):
        stream_data = io.BytesIO(uuid.uuid4().bytes)
        
        with patch('skills.market_insider_activity_tracker.MarketInsiderActivityTracker.analyze_activity') as mock_analyze, \
             patch('skills.market_anomaly_detector.MarketAnomalyDetector.detect') as mock_detect:
            
            mock_analyze.return_value = {
                "status": "suspicious",
                "ticker": self.random_ticker,
                "signature": self.random_signature
            }
            mock_detect.return_value = {
                "is_anomaly": True,
                "anomaly_score": self.random_score
            }

            result = self.pipeline.process_alert_stream(self.random_ticker, stream_data)

            self.assertIsNotNone(result)
            self.assertEqual(result["ticker"], self.random_ticker)
            self.assertEqual(result["signature"], self.random_signature)
            self.assertTrue(result["is_anomaly"])
            self.assertEqual(result["anomaly_score"], self.random_score)
            
            mock_analyze.assert_called_once_with(stream_data)
            mock_detect.assert_called_once_with(self.random_ticker)

    def test_process_alert_stream_not_suspicious(self):
        stream_data = io.BytesIO(uuid.uuid4().bytes)
        
        with patch('skills.market_insider_activity_tracker.MarketInsiderActivityTracker.analyze_activity') as mock_analyze, \
             patch('skills.market_anomaly_detector.MarketAnomalyDetector.detect') as mock_detect:
            
            mock_analyze.return_value = {
                "status": "normal",
                "ticker": self.random_ticker
            }

            result = self.pipeline.process_alert_stream(self.random_ticker, stream_data)

            self.assertIsNone(result)
            mock_analyze.assert_called_once_with(stream_data)
            mock_detect.assert_not_called()

    def test_process_alert_stream_no_anomaly(self):
        stream_data = io.BytesIO(uuid.uuid4().bytes)
        
        with patch('skills.market_insider_activity_tracker.MarketInsiderActivityTracker.analyze_activity') as mock_analyze, \
             patch('skills.market_anomaly_detector.MarketAnomalyDetector.detect') as mock_detect:
            
            mock_analyze.return_value = {
                "status": "suspicious",
                "ticker": self.random_ticker,
                "signature": self.random_signature
            }
            mock_detect.return_value = {
                "is_anomaly": False,
                "anomaly_score": 0.0
            }

            result = self.pipeline.process_alert_stream(self.random_ticker, stream_data)

            self.assertIsNone(result)
            mock_analyze.assert_called_once_with(stream_data)
            mock_detect.assert_called_once_with(self.random_ticker)

    def test_evaluate_market_stream(self):
        expected_result = {uuid.uuid4().hex: random.choice([True, False])}
        
        with patch('skills.market_anomaly_detector.MarketAnomalyDetector.analyze_stream') as mock_analyze_stream:
            mock_analyze_stream.return_value = expected_result

            result = self.pipeline.evaluate_market_stream(self.random_exchange)

            self.assertEqual(result, expected_result)
            mock_analyze_stream.assert_called_once_with(self.random_exchange)

    def test_functional_market_insider_alert_pipeline_with_dict(self):
        raw_data = {
            "ticker": self.random_ticker,
            "signature": self.random_signature,
            "stream": io.BytesIO(uuid.uuid4().bytes)
        }
        
        mock_analysis_output = {"status": "analyzed", "id": uuid.uuid4().hex}
        mock_anomaly_output = {"is_anomaly": True, "score": random.random()}

        with patch('skills.market_insider_activity_tracker.MarketInsiderActivityTracker.analyze_activity') as mock_analyze, \
             patch('skills.market_anomaly_detector.MarketAnomalyDetector.detect') as mock_detect:
            
            mock_analyze.return_value = mock_analysis_output
            mock_detect.return_value = mock_anomaly_output

            result = market_insider_alert_pipeline(raw_data)

            self.assertIsInstance(result, dict)
            self.assertIn("alert_id", result)
            self.assertEqual(result["ticker"], self.random_ticker)
            self.assertEqual(result["signature"], self.random_signature)
            self.assertEqual(result["analysis"], mock_analysis_output)
            self.assertEqual(result["anomaly"], mock_anomaly_output)

            mock_analyze.assert_called_once_with(raw_data["stream"])
            mock_detect.assert_called_once_with(self.random_ticker)

    def test_functional_market_insider_alert_pipeline_with_bytes_stream(self):
        raw_stream = io.BytesIO(uuid.uuid4().bytes)
        
        mock_analysis_output = {"status": "processed"}
        mock_anomaly_output = {"is_anomaly": False}

        with patch('skills.market_insider_activity_tracker.MarketInsiderActivityTracker.analyze_activity') as mock_analyze, \
             patch('skills.market_anomaly_detector.MarketAnomalyDetector.detect') as mock_detect:
            
            mock_analyze.return_value = mock_analysis_output
            mock_detect.return_value = mock_anomaly_output

            result = market_insider_alert_pipeline(raw_stream)

            self.assertIsInstance(result, dict)
            self.assertIn("alert_id", result)
            self.assertIsNone(result["ticker"])
            self.assertIsNone(result["signature"])
            self.assertEqual(result["analysis"], mock_analysis_output)
            self.assertEqual(result["anomaly"], mock_anomaly_output)

            mock_analyze.assert_called_once_with(raw_stream)
            mock_detect.assert_called_once_with(None)


if __name__ == '__main__':
    unittest.main()