import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io

from skills.market_sentiment_anomaly_correlator import MarketSentimentAnomalyCorrelator


class TestMarketSentimentAnomalyCorrelator(unittest.TestCase):

    def setUp(self):
        self.correlator = MarketSentimentAnomalyCorrelator()
        self.rand_ticker = f"TICK_{uuid.uuid4().hex[:4].upper()}"
        self.rand_text = f"Market surge due to {uuid.uuid4().hex[:8]}"
        self.rand_filename = f"{uuid.uuid4().hex}.log"

    def test_correlate_with_string_input_and_anomaly_dict(self):
        rand_score = round(random.uniform(0.6, 1.0), 2)
        anomaly_payload = {
            "ticker": self.rand_ticker,
            "anomaly_detected": True,
            "status": "anomaly_active",
            "magnitude": random.randint(5, 20)
        }

        with patch.object(self.correlator.sentiment_analyzer, 'analyze', return_value={"sentiment_score": rand_score, "entities": [self.rand_ticker]}):
            result = self.correlator.correlate(self.rand_text, anomaly_payload)

        self.assertIn("correlation_id", result)
        self.assertEqual(result["ticker"], self.rand_ticker)
        self.assertTrue(result["correlation_found"])
        self.assertEqual(result["sentiment_score"], rand_score)
        self.assertEqual(result["anomaly_data"], anomaly_payload)

    def test_correlate_with_dict_news_input(self):
        rand_score = round(random.uniform(-1.0, -0.6), 2)
        news_payload = {
            "ticker": self.rand_ticker,
            "text": self.rand_text,
            "score": rand_score
        }
        anomaly_payload = {
            "ticker": self.rand_ticker,
            "anomaly_detected": True,
            "status": "anomaly_active"
        }

        with patch.object(self.correlator.sentiment_analyzer, 'analyze', return_value={"sentiment_score": rand_score, "entities": [self.rand_ticker]}):
            with patch.object(self.correlator.anomaly_detector, 'detect', return_value=anomaly_payload):
                result = self.correlator.correlate(news_payload)

        self.assertIn("correlation_id", result)
        self.assertEqual(result["ticker"], self.rand_ticker)
        self.assertTrue(result["correlation_found"])
        self.assertEqual(result["sentiment_score"], rand_score)

    def test_correlate_no_correlation_due_to_low_sentiment(self):
        rand_score = round(random.uniform(-0.4, 0.4), 2)
        anomaly_payload = {
            "ticker": self.rand_ticker,
            "anomaly_detected": True,
            "status": "anomaly_active"
        }

        with patch.object(self.correlator.sentiment_analyzer, 'analyze', return_value={"sentiment_score": rand_score, "entities": [self.rand_ticker]}):
            with patch.object(self.correlator.anomaly_detector, 'detect', return_value=anomaly_payload):
                result = self.correlator.correlate(self.rand_text, self.rand_ticker)

        self.assertFalse(result["correlation_found"])
        self.assertEqual(result["sentiment_score"], rand_score)

    def test_correlate_no_anomaly_detected(self):
        rand_score = round(random.uniform(0.7, 1.0), 2)
        anomaly_payload = {
            "ticker": self.rand_ticker,
            "anomaly_detected": False,
            "status": "normal"
        }

        with patch.object(self.correlator.sentiment_analyzer, 'analyze', return_value={"sentiment_score": rand_score, "entities": [self.rand_ticker]}):
            with patch.object(self.correlator.anomaly_detector, 'detect', return_value=anomaly_payload):
                result = self.correlator.correlate(self.rand_text, self.rand_ticker)

        self.assertFalse(result["correlation_found"])

    def test_correlate_attribute_error_fallback(self):
        rand_score = round(random.uniform(0.6, 0.9), 2)

        class FaultyAnalyzer:
            def analyze(self, raw):
                if isinstance(raw, str):
                    raise AttributeError("Mocked analyzer expects non-string or fails on .lower()")
                return {"sentiment_score": rand_score, "entities": []}

        self.correlator.sentiment_analyzer = FaultyAnalyzer()
        anomaly_payload = {
            "ticker": self.rand_ticker,
            "anomaly_detected": True,
            "status": "anomaly_active"
        }

        result = self.correlator.correlate(self.rand_text, anomaly_payload)
        self.assertTrue(result["correlation_found"])
        self.assertEqual(result["sentiment_score"], rand_score)

    def test_process_stream_correlation(self):
        rand_stream_info = {"stream_id": uuid.uuid4().hex, "metric": random.randint(100, 500)}
        mock_batch = [{"item": uuid.uuid4().hex} for _ in range(random.randint(1, 5))]

        with patch.object(self.correlator.sentiment_analyzer, 'batch_analyze_stream', return_value=mock_batch):
            result = self.correlator.process_stream_correlation(self.rand_filename, stream_anomaly=rand_stream_info)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["processed_items_count"], len(mock_batch))
        self.assertEqual(result["stream_anomaly_info"], rand_stream_info)

    def test_process_stream_correlation_no_batch_method(self):
        class DummyAnalyzerWithoutBatch:
            def analyze(self, text):
                return {"score": 0.5}

        self.correlator.sentiment_analyzer = DummyAnalyzerWithoutBatch()

        result = self.correlator.process_stream_correlation(self.rand_filename)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["processed_items_count"], 1)


if __name__ == '__main__':
    unittest.main()