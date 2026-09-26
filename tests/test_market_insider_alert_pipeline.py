import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
from skills.market_insider_alert_pipeline import MarketInsiderAlertPipeline, market_insider_alert_pipeline

class TestMarketInsiderAlertPipeline(unittest.TestCase):

    def setUp(self):
        self.pipeline = MarketInsiderAlertPipeline()
        self.random_ticker = f"TICK_{uuid.uuid4().hex[:6].upper()}"
        self.random_signature = uuid.uuid4().hex
        self.random_exchange = f"EXCH_{uuid.uuid4().hex[:4].upper()}"
        self.random_score = round(random.uniform(1.0, 100.0), 2)

    def test_process_alert_stream_suspicious_and_anomaly(self):
        raw_stream_data = io.BytesIO(f"data_{uuid.uuid4().hex}".encode('utf-8'))
        
        with patch.object(self.pipeline.tracker, 'analyze_activity') as mock_analyze, \
             patch.object(self.pipeline.detector, 'detect') as mock_detect:
            
            mock_analyze.return_value = {
                "status": "suspicious",
                "ticker": self.random_ticker,
                "signature": self.random_signature
            }
            mock_detect.return_value = {
                "is_anomaly": True,
                "anomaly_score": self.random_score
            }

            alert = self.pipeline.process_alert_stream(self.random_ticker, raw_stream_data)

            self.assertIsNotNone(alert)
            self.assertEqual(alert.get("ticker"), self.random_ticker)
            self.assertEqual(alert.get("signature"), self.random_signature)
            self.assertTrue(alert.get("is_anomaly"))
            self.assertEqual(alert.get("anomaly_score"), self.random_score)
            mock_analyze.assert_called_once_with(raw_stream_data)
            mock_detect.assert_called_once_with(self.random_ticker)

    def test_process_alert_stream_not_suspicious(self):
        raw_stream_data = io.BytesIO(f"data_{uuid.uuid4().hex}".encode('utf-8'))
        
        with patch.object(self.pipeline.tracker, 'analyze_activity') as mock_analyze, \
             patch.object(self.pipeline.detector, 'detect') as mock_detect:
            
            mock_analyze.return_value = {
                "status": "normal",
                "ticker": self.random_ticker,
                "signature": self.random_signature
            }
            mock_detect.return_value = {
                "is_anomaly": True,
                "anomaly_score": self.random_score
            }

            alert = self.pipeline.process_alert_stream(self.random_ticker, raw_stream_data)

            self.assertIsNone(alert)
            mock_analyze.assert_called_once_with(raw_stream_data)
            mock_detect.assert_not_called()

    def test_process_alert_stream_not_anomaly(self):
        raw_stream_data = io.BytesIO(f"data_{uuid.uuid4().hex}".encode('utf-8'))
        
        with patch.object(self.pipeline.tracker, 'analyze_activity') as mock_analyze, \
             patch.object(self.pipeline.detector, 'detect') as mock_detect:
            
            mock_analyze.return_value = {
                "status": "suspicious",
                "ticker": self.random_ticker,
                "signature": self.random_signature
            }
            mock_detect.return_value = {
                "is_anomaly": False,
                "anomaly_score": 0.0
            }

            alert = self.pipeline.process_alert_stream(self.random_ticker, raw_stream_data)

            self.assertIsNone(alert)
            mock_analyze.assert_called_once_with(raw_stream_data)
            mock_detect.assert_called_once_with(self.random_ticker)

    def test_evaluate_market_stream(self):
        expected_result = {
            "exchange": self.random_exchange,
            "status": "evaluated",
            "metrics": random.randint(100, 500)
        }

        with patch('skills.market_insider_alert_pipeline.MarketAnomalyDetector') as MockDetector:
            instance = MockDetector.return_value
            instance.analyze_stream.return_value = expected_result
            
            pipeline_instance = MarketInsiderAlertPipeline()
            result = pipeline_instance.evaluate_market_stream(self.random_exchange)

            self.assertEqual(result, expected_result)
            instance.analyze_stream.assert_called_once_with(self.random_exchange)

    def test_market_insider_alert_pipeline_helper_with_dict(self):
        raw_data_dict = {
            "ticker": self.random_ticker,
            "signature": self.random_signature,
            "payload": uuid.uuid4().hex
        }

        analysis_mock_result = {"analyzed": True, "id": uuid.uuid4().hex}
        anomaly_mock_result = {"is_anomaly": True, "score": random.random()}

        with patch('skills.market_insider_alert_pipeline.MarketInsiderActivityTracker') as MockTracker, \
             patch('skills.market_insider_alert_pipeline.MarketAnomalyDetector') as MockDetector:
            
            tracker_instance = MockTracker.return_value
            tracker_instance.analyze_activity.return_value = analysis_mock_result

            detector_instance = MockDetector.return_value
            detector_instance.detect.return_value = anomaly_mock_result

            result = market_insider_alert_pipeline(raw_data_dict)

            self.assertIn("alert_id", result)
            self.assertEqual(result["ticker"], self.random_ticker)
            self.assertEqual(result["signature"], self.random_signature)
            self.assertEqual(result["analysis"], analysis_mock_result)
            self.assertEqual(result["anomaly"], anomaly_mock_result)
            
            tracker_instance.analyze_activity.assert_called_once()
            called_arg = tracker_instance.analyze_activity.call_args[0][0]
            self.assertIsInstance(called_arg, io.BytesIO)

    def test_market_insider_alert_pipeline_helper_with_stream(self):
        raw_stream = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))
        
        analysis_mock_result = {"analyzed": True, "id": uuid.uuid4().hex}
        anomaly_mock_result = {"is_anomaly": False, "score": 0.1}

        with patch('skills.market_insider_alert_pipeline.MarketInsiderActivityTracker') as MockTracker, \
             patch('skills.market_insider_alert_pipeline.MarketAnomalyDetector') as MockDetector:
            
            tracker_instance = MockTracker.return_value
            tracker_instance.analyze_activity.return_value = analysis_mock_result

            detector_instance = MockDetector.return_value
            detector_instance.detect.return_value = anomaly_mock_result

            raw_data_arg = {
                "ticker": self.random_ticker,
                "stream": raw_stream
            }

            result = market_insider_alert_pipeline(raw_data_arg)

            self.assertIn("alert_id", result)
            self.assertEqual(result["ticker"], self.random_ticker)
            self.assertIsNone(result["signature"])
            self.assertEqual(result["analysis"], analysis_mock_result)
            self.assertEqual(result["anomaly"], anomaly_mock_result)