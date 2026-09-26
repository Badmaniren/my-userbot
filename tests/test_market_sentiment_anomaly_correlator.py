import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
from skills.market_sentiment_anomaly_correlator import (
    MarketSentimentAnomalyCorrelator,
    MarketSentimentAnomalyException,
    correlate_anomaly_with_sentiment,
    market_sentiment_anomaly_correlator
)

class TestMarketSentimentAnomalyCorrelator(unittest.TestCase):

    def setUp(self):
        self.correlator = MarketSentimentAnomalyCorrelator()
        self.rand_ticker = f"BTC-{uuid.uuid4().hex[:6].upper()}"
        self.rand_news = f"Market crash imminent due to random event {uuid.uuid4().hex}"
        self.rand_exchange = f"EXCHANGE-{uuid.uuid4().hex[:4].upper()}"
        self.rand_filename = f"{uuid.uuid4().hex}.bin"

    @patch('skills.market_sentiment_anomaly_correlator.MarketAnomalyDetector')
    @patch('skills.market_sentiment_anomaly_correlator.MarketNewsSentimentAnalyzer')
    def test_correlate_success(self, mock_analyzer_cls, mock_detector_cls):
        mock_detector_instance = mock_detector_cls.return_value
        rand_anomaly_score = round(random.uniform(0.5, 5.0), 2)
        mock_detector_instance.detect.return_value = {"anomaly_score": rand_anomaly_score, "ticker": self.rand_ticker}

        mock_analyzer_instance = mock_analyzer_cls.return_value
        rand_sentiment_score = round(random.uniform(-1.0, 1.0), 2)
        mock_analyzer_instance.analyze.return_value = {"sentiment": rand_sentiment_score, "text": self.rand_news}

        correlator = MarketSentimentAnomalyCorrelator()
        result = correlator.correlate(self.rand_ticker, self.rand_news)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["ticker"], self.rand_ticker)
        self.assertEqual(result["anomaly"]["anomaly_score"], rand_anomaly_score)
        self.assertEqual(result["sentiment"]["sentiment"], rand_sentiment_score)
        expected_index = round(float(rand_anomaly_score) * abs(float(rand_sentiment_score)), 4)
        self.assertEqual(result["correlation_index"], expected_index)

        mock_detector_instance.detect.assert_called_once_with(self.rand_ticker)
        mock_analyzer_instance.analyze.assert_called_once_with(self.rand_news)

    @patch('skills.market_sentiment_anomaly_correlator.MarketAnomalyDetector')
    def test_correlate_exception_handling(self, mock_detector_cls):
        mock_detector_instance = mock_detector_cls.return_value
        rand_error_msg = f"Critical anomaly engine failure {uuid.uuid4().hex}"
        mock_detector_instance.detect.side_effect = Exception(rand_error_msg)

        with self.assertRaises(MarketSentimentAnomalyException) as ctx:
            self.correlator.correlate(self.rand_ticker, self.rand_news)

        self.assertIn(rand_error_msg, str(ctx.exception))

    def test_analyze_correlation_stream(self):
        stream_source = [uuid.uuid4().hex, uuid.uuid4().hex]
        res = self.correlator.analyze_correlation_stream(stream_source)
        self.assertIsInstance(res, list)
        self.assertEqual(len(res), 0)

    @patch('skills.market_sentiment_anomaly_correlator.open')
    @patch('skills.market_sentiment_anomaly_correlator.MarketNewsSentimentAnalyzer')
    def test_process_audit_stream_success(self, mock_analyzer_cls, mock_open):
        rand_bytes = bytes(uuid.uuid4().hex, 'utf-8')
        mock_file = MagicMock()
        mock_file.read.return_value = rand_bytes
        mock_open.return_value.__enter__.return_value = mock_file

        mock_analyzer_instance = mock_analyzer_cls.return_value
        mock_analyzer_instance.process_and_store.return_value = True

        correlator = MarketSentimentAnomalyCorrelator()
        res = correlator.process_audit_stream(self.rand_filename)

        self.assertTrue(res)
        mock_open.assert_called_once_with(self.rand_filename, 'rb')
        mock_file.read.assert_called_once()
        mock_analyzer_instance.process_and_store.assert_called_once_with(rand_bytes)

    @patch('skills.market_sentiment_anomaly_correlator.open')
    @patch('skills.market_sentiment_anomaly_correlator.MarketNewsSentimentAnalyzer')
    def test_process_audit_stream_exception(self, mock_analyzer_cls, mock_open):
        rand_err = f"IO Error reading audit {uuid.uuid4().hex}"
        mock_open.side_effect = IOError(rand_err)

        correlator = MarketSentimentAnomalyCorrelator()
        with self.assertRaises(MarketSentimentAnomalyException) as ctx:
            correlator.process_audit_stream(self.rand_filename)

        self.assertIn(rand_err, str(ctx.exception))

    @patch('skills.market_sentiment_anomaly_correlator.MarketNewsSentimentAnalyzer')
    @patch('skills.market_sentiment_anomaly_correlator.MarketAnomalyDetector')
    def test_correlate_anomaly_with_sentiment_helper(self, mock_detector_cls, mock_analyzer_cls):
        mock_detector_instance = mock_detector_cls.return_value
        rand_anomalies = [{"id": uuid.uuid4().hex}, {"id": uuid.uuid4().hex}]
        mock_detector_instance.analyze_stream.return_value = rand_anomalies

        mock_analyzer_instance = mock_analyzer_cls.return_value
        rand_sentiments = [{"score": 0.5}, {"score": -0.8}]
        mock_analyzer_instance.batch_analyze_stream.return_value = rand_sentiments

        res = correlate_anomaly_with_sentiment(self.rand_exchange, self.rand_news)

        self.assertIsInstance(res, dict)
        self.assertEqual(res["exchange"], self.rand_exchange)
        self.assertEqual(res["matched_events"], list(zip(rand_anomalies, rand_sentiments)))

        mock_detector_instance.analyze_stream.assert_called_once_with(self.rand_exchange)
        mock_analyzer_instance.batch_analyze_stream.assert_called_once_with(self.rand_news)

    def test_market_sentiment_anomaly_correlator_func(self):
        rand_anomaly_score = round(random.uniform(1.0, 10.0), 2)
        rand_sentiment_score = round(random.uniform(-1.0, 1.0), 2)
        
        correlation_input = {
            "ticker": self.rand_ticker,
            "anomaly": {"anomaly_score": rand_anomaly_score, "details": uuid.uuid4().hex},
            "sentiment": {"sentiment": rand_sentiment_score, "source": uuid.uuid4().hex}
        }

        res = market_sentiment_anomaly_correlator(correlation_input)

        self.assertIsInstance(res, dict)
        self.assertEqual(res["ticker"], self.rand_ticker)
        self.assertEqual(res["status"], "CORRELATED")
        self.assertIn("correlation_id", res)
        self.assertEqual(len(res["correlation_id"]), 32)
        
        expected_index = round(float(rand_anomaly_score) * abs(float(rand_sentiment_score)), 4)
        self.assertEqual(res["correlation_index"], expected_index)
        self.assertEqual(res["anomaly"], correlation_input["anomaly"])
        self.assertEqual(res["sentiment"], correlation_input["sentiment"])

    def test_market_sentiment_anomaly_correlator_func_missing_fields(self):
        correlation_input = {
            "ticker": self.rand_ticker,
            "anomaly": None,
            "sentiment": None
        }

        res = market_sentiment_anomaly_correlator(correlation_input)

        self.assertIsInstance(res, dict)
        self.assertEqual(res["ticker"], self.rand_ticker)
        self.assertEqual(res["status"], "CORRELATED")
        self.assertEqual(res["correlation_index"], 1.0 * abs(0.0))
        self.assertIsNone(res["anomaly"])
        self.assertIsNone(res["sentiment"])