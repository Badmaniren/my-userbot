import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from skills.market_sentiment_anomaly_correlator import (
    MarketSentimentAnomalyCorrelator,
    correlate_anomaly_with_sentiment,
    MarketSentimentAnomalyException
)


class TestMarketSentimentAnomalyCorrelator(unittest.TestCase):

    def setUp(self):
        self.ticker = "".join(random.choices(string.ascii_uppercase, k=random.randint(3, 5)))
        self.exchange = "".join(random.choices(string.ascii_uppercase, k=random.randint(4, 8)))
        self.news_snippet = "".join(random.choices(string.ascii_letters + string.punctuation + " ", k=random.randint(20, 50)))
        self.anomaly_score = random.uniform(1.1, 9.9)
        self.sentiment_score = random.uniform(-1.0, 1.0)
        self.correlation_id = uuid.uuid4().hex

    @patch('skills.market_sentiment_anomaly_correlator.MarketAnomalyDetector')
    @patch('skills.market_sentiment_anomaly_correlator.MarketNewsSentimentAnalyzer')
    def test_correlator_initialization_and_methods(self, mock_sentiment_cls, mock_anomaly_cls):
        mock_anomaly_instance = mock_anomaly_cls.return_value
        mock_sentiment_instance = mock_sentiment_cls.return_value

        mock_anomaly_instance.detect.return_value = {
            "ticker": self.ticker,
            "anomaly_score": self.anomaly_score,
            "status": "DETECTED"
        }
        mock_sentiment_instance.analyze.return_value = {
            "sentiment": self.sentiment_score,
            "raw_text": self.news_snippet
        }

        correlator = MarketSentimentAnomalyCorrelator()
        self.assertTrue(hasattr(correlator, 'correlate'))
        self.assertTrue(hasattr(correlator, 'analyze_correlation_stream'))

        result = correlator.correlate(self.ticker, self.news_snippet)

        self.assertIn("ticker", result)
        self.assertEqual(result["ticker"], self.ticker)
        self.assertIn("anomaly", result)
        self.assertIn("sentiment", result)
        self.assertIn("correlation_index", result)
        self.assertEqual(result["anomaly"]["anomaly_score"], self.anomaly_score)
        self.assertEqual(result["sentiment"]["sentiment"], self.sentiment_score)

        mock_anomaly_instance.detect.assert_called_once_with(self.ticker)
        mock_sentiment_instance.analyze.assert_called_once_with(self.news_snippet)

    @patch('skills.market_sentiment_anomaly_correlator.MarketAnomalyDetector')
    @patch('skills.market_sentiment_anomaly_correlator.MarketNewsSentimentAnalyzer')
    def test_functional_correlate_helper(self, mock_sentiment_cls, mock_anomaly_cls):
        mock_anomaly_instance = mock_anomaly_cls.return_value
        mock_sentiment_instance = mock_sentiment_cls.return_value

        mock_anomaly_instance.analyze_stream.return_value = [
            {"ticker": self.ticker, "score": self.anomaly_score}
        ]
        mock_sentiment_instance.batch_analyze_stream.return_value = [
            {"sentiment": self.sentiment_score, "text": self.news_snippet}
        ]

        correlation_result = correlate_anomaly_with_sentiment(self.exchange, self.news_snippet)

        self.assertIsInstance(correlation_result, dict)
        self.assertIn("exchange", correlation_result)
        self.assertEqual(correlation_result["exchange"], self.exchange)
        self.assertIn("matched_events", correlation_result)
        self.assertIsInstance(correlation_result["matched_events"], list)

    @patch('skills.market_sentiment_anomaly_correlator.MarketAnomalyDetector')
    @patch('skills.market_sentiment_anomaly_correlator.MarketNewsSentimentAnalyzer')
    def test_correlator_stream_handling(self, mock_sentiment_cls, mock_anomaly_cls):
        mock_anomaly_instance = mock_anomaly_cls.return_value
        mock_sentiment_instance = mock_sentiment_cls.return_value

        random_filename = f"{uuid.uuid4().hex}.dat"
        mock_anomaly_instance.detect.return_value = {"id": self.correlation_id, "score": self.anomaly_score}
        mock_sentiment_instance.process_and_store.return_value = True

        correlator = MarketSentimentAnomalyCorrelator()
        
        mock_file_stream = io.BytesIO(bytes(self.news_snippet, 'utf-8'))
        
        with patch('builtins.open', return_value=mock_file_stream):
            processing_status = correlator.process_audit_stream(random_filename)
            self.assertTrue(processing_status)

    @patch('skills.market_sentiment_anomaly_correlator.MarketAnomalyDetector')
    @patch('skills.market_sentiment_anomaly_correlator.MarketNewsSentimentAnalyzer')
    def test_correlator_exception_handling(self, mock_sentiment_cls, mock_anomaly_cls):
        mock_anomaly_instance = mock_anomaly_cls.return_value
        mock_anomaly_instance.detect.side_effect = Exception("Anomaly Engine Failure")

        correlator = MarketSentimentAnomalyCorrelator()

        with self.assertRaises(MarketSentimentAnomalyException):
            correlator.correlate(self.ticker, self.news_snippet)


if __name__ == '__main__':
    unittest.main()