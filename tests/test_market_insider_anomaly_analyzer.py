import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import json
import io
import os

from skills.market_insider_anomaly_analyzer import (
    MarketInsiderAnomalyAnalyzer,
    market_insider_anomaly_analyzer,
    evaluate_exchange_anomalies,
    analyze_market_insider_anomalies
)


class TestMarketInsiderAnomalyAnalyzer(unittest.TestCase):

    def setUp(self):
        self.ticker = "".join(random.choices(string.ascii_uppercase, k=5))
        self.exchange = "".join(random.choices(string.ascii_uppercase, k=6))
        self.stream_data = {
            "stream_id": uuid.uuid4().hex,
            "volume": random.randint(1000, 1000000),
            "price": round(random.uniform(1.0, 500.0), 2)
        }

    def test_analyzer_init_and_coordination_logic(self):
        mock_detector = MagicMock()
        anomaly_id = uuid.uuid4().hex
        mock_detector.detect.return_value = {
            "has_anomaly": True,
            "score": round(random.uniform(0.5, 1.0), 2),
            "anomaly_id": anomaly_id
        }

        mock_pipeline = MagicMock()
        alert_id = uuid.uuid4().hex
        mock_pipeline.process_alert_stream.return_value = {
            "insider_detected": True,
            "alerts": [{"alert_id": alert_id, "severity": "HIGH"}]
        }

        analyzer = MarketInsiderAnomalyAnalyzer(anomaly_detector=mock_detector, alert_pipeline=mock_pipeline)
        result = analyzer.analyze_ticker(self.ticker, self.stream_data)

        self.assertTrue(result["is_coordinated"])
        self.assertTrue(result["suspicious"])
        self.assertTrue(result["coordinated_activity"])
        self.assertEqual(result["ticker"], self.ticker)
        self.assertEqual(result["anomaly_id"], anomaly_id)
        self.assertEqual(result["alert_id"], alert_id)
        self.assertIn("anomaly_data", result)
        self.assertIn("insider_alert_data", result)

    def test_analyzer_no_anomaly(self):
        mock_detector = MagicMock()
        mock_detector.detect.return_value = {"has_anomaly": False, "score": 0.0}

        mock_pipeline = MagicMock()
        mock_pipeline.process_alert_stream.return_value = {"insider_detected": False, "alerts": []}

        analyzer = MarketInsiderAnomalyAnalyzer(anomaly_detector=mock_detector, alert_pipeline=mock_pipeline)
        result = analyzer.analyze(self.ticker, self.stream_data)

        self.assertFalse(result["is_coordinated"])
        self.assertFalse(result["suspicious"])
        self.assertEqual(result["ticker"], self.ticker)
        self.assertNotIn("anomaly_id", result)
        self.assertNotIn("alert_id", result)

    def test_analyzer_fallback_methods(self):
        mock_detector = MagicMock()
        mock_detector.detect.side_effect = TypeError("Signature mismatch")
        mock_detector.detect.return_value = {"has_anomaly": True}

        mock_pipeline = MagicMock()
        mock_pipeline.process.return_value = {"insider_detected": True, "alerts": []}

        analyzer = MarketInsiderAnomalyAnalyzer(anomaly_detector=mock_detector, alert_pipeline=mock_pipeline)
        
        for alias_method in [analyzer.detect, analyzer.correlate, analyzer.process]:
            res = alias_method(self.ticker, self.stream_data)
            self.assertIsInstance(res, dict)
            self.assertEqual(res["ticker"], self.ticker)

    def test_analyze_stream_and_aliases(self):
        mock_detector = MagicMock()
        random_items = [uuid.uuid4().hex, random.randint(1, 100)]
        mock_detector.analyze_stream.return_value = random_items

        mock_pipeline = MagicMock()
        random_insider = {"status": uuid.uuid4().hex}
        mock_pipeline.evaluate_market_stream.return_value = random_insider

        analyzer = MarketInsiderAnomalyAnalyzer(anomaly_detector=mock_detector, alert_pipeline=mock_pipeline)

        for method in [
            analyzer.analyze_stream,
            analyzer.evaluate_exchange,
            analyzer.analyze_exchange,
            analyzer.evaluate_market_stream,
            analyzer.correlate_exchange
        ]:
            res = method(self.exchange)
            self.assertEqual(res["exchange"], self.exchange)
            self.assertEqual(res["anomaly_items"], random_items)
            self.assertEqual(res["insider_items"], random_insider)

    def test_helper_market_insider_anomaly_analyzer(self):
        dict_payload = {
            "ticker": self.ticker,
            "raw_stream_data": self.stream_data
        }
        with patch("skills.market_insider_anomaly_analyzer.MarketInsiderAnomalyAnalyzer") as MockAnalyzerClass:
            mock_instance = MockAnalyzerClass.return_value
            expected_dict = {"ticker": self.ticker, "status": uuid.uuid4().hex}
            mock_instance.analyze_ticker.return_value = expected_dict

            res1 = market_insider_anomaly_analyzer(dict_payload)
            self.assertEqual(res1, expected_dict)
            mock_instance.analyze_ticker.assert_called_once_with(self.ticker, self.stream_data)

            mock_instance.analyze_ticker.reset_mock()
            res2 = market_insider_anomaly_analyzer(ticker=self.ticker, raw_stream_data=self.stream_data)
            self.assertEqual(res2, expected_dict)
            mock_instance.analyze_ticker.assert_called_once_with(self.ticker, self.stream_data)

    def test_evaluate_exchange_anomalies_helper(self):
        with patch("skills.market_insider_anomaly_analyzer.MarketInsiderAnomalyAnalyzer") as MockAnalyzerClass:
            mock_instance = MockAnalyzerClass.return_value
            expected_res = {"exchange": self.exchange, "data": uuid.uuid4().hex}
            mock_instance.analyze_stream.return_value = expected_res

            res = evaluate_exchange_anomalies(self.exchange)
            self.assertEqual(res, expected_res)
            mock_instance.analyze_stream.assert_called_once_with(self.exchange)

    def test_analyze_market_insider_anomalies_report_generation(self):
        with patch("skills.market_insider_anomaly_analyzer.MarketAnomalyDetector") as MockDetectorClass, \
             patch("skills.market_insider_anomaly_analyzer.MarketInsiderAlertPipeline") as MockPipelineClass, \
             patch("builtins.open", create=True) as mock_open:

            mock_detector = MockDetectorClass.return_value
            mock_anomaly_data = {"has_anomaly": True, "anomaly_id": uuid.uuid4().hex}
            mock_detector.detect.return_value = mock_anomaly_data

            mock_pipeline = MockPipelineClass.return_value
            mock_alert_data = {"insider_detected": True, "alerts": [{"alert_id": uuid.uuid4().hex}]}
            mock_pipeline.process_alert_stream.return_value = mock_alert_data

            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file

            result = analyze_market_insider_anomalies(
                ticker=self.ticker,
                exchange=self.exchange,
                raw_stream_data=self.stream_data
            )

            self.assertEqual(result["ticker"], self.ticker)
            self.assertEqual(result["exchange"], self.exchange)
            self.assertTrue(result["coordinated_activity_detected"])
            self.assertIn("correlation_id", result)
            self.assertEqual(result["anomaly_data"], mock_anomaly_data)
            self.assertEqual(result["insider_alert_data"], mock_alert_data)

            mock_open.assert_called_once()
            called_filename = mock_open.call_args[0][0]
            self.assertTrue(called_filename.startswith("insider_anomaly_report_"))
            self.assertTrue(called_filename.endswith(".json"))
            mock_file.write.assert_called()