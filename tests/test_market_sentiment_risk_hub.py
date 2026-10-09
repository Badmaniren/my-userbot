import unittest
from unittest.mock import patch, MagicMock
import io
import os
import random
import uuid
from skills.market_sentiment_risk_hub import (
    MarketSentimentRiskHub,
    compute_market_risk_index,
    process_risk_stream
)

class TestMarketSentimentRiskHub(unittest.TestCase):

    def setUp(self):
        self.hub = MarketSentimentRiskHub()
        self.rand_ticker = f"TICKER_{uuid.uuid4().hex[:6].upper()}"
        self.rand_exchange = f"EXCH_{uuid.uuid4().hex[:6].upper()}"
        self.rand_snippet = f"Breaking news on {uuid.uuid4().hex}"
        self.rand_filename = f"report_{uuid.uuid4().hex}.txt"

    def tearDown(self):
        if os.path.exists(self.rand_filename):
            try:
                os.remove(self.rand_filename)
            except OSError:
                pass

    def test_evaluate_risk_with_news_snippet(self):
        rand_sentiment = round(random.uniform(-1.0, 1.0), 2)
        rand_anomaly = round(random.uniform(0.0, 100.0), 2)

        with patch.object(self.hub.sentiment_analyzer, 'analyze') as mock_sentiment, \
             patch.object(self.hub.anomaly_detector, 'detect') as mock_anomaly:

            mock_sentiment.return_value = {"sentiment_score": rand_sentiment}
            mock_anomaly.return_value = {"anomaly_score": rand_anomaly}

            result = self.hub.evaluate_risk(news_snippet=self.rand_snippet, exchange=self.rand_exchange)

            mock_sentiment.assert_called_once_with(self.rand_snippet)
            mock_anomaly.assert_called_once_with(self.rand_exchange if hasattr(self, 'rand_exchange') else "DEFAULT")

            expected_risk = abs(float(rand_sentiment)) * 50.0 + float(rand_anomaly) * 0.5
            self.assertEqual(result["sentiment_score"], rand_sentiment)
            self.assertEqual(result["anomaly_score"], rand_anomaly)
            self.assertEqual(result["risk_score"], expected_risk)
            self.assertEqual(result["risk_index"], expected_risk)

    def test_evaluate_risk_with_ticker(self):
        rand_sentiment = round(random.uniform(-1.0, 1.0), 2)
        rand_anomaly_val = round(random.uniform(10.0, 50.0), 2)

        with patch.object(self.hub.sentiment_analyzer, 'analyze') as mock_sentiment, \
             patch.object(self.hub.anomaly_detector, 'detect') as mock_anomaly:

            mock_sentiment.return_value = {"sentiment_score": rand_sentiment}
            mock_anomaly.return_value = rand_anomaly_val

            result = self.hub.evaluate_risk(ticker=self.rand_ticker, exchange=self.rand_exchange)

            mock_sentiment.assert_called_once_with(self.rand_ticker)
            mock_anomaly.assert_called_once_with(self.rand_exchange)

            expected_risk = abs(float(rand_sentiment)) * 50.0 + float(rand_anomaly_val) * 0.5
            self.assertEqual(result["sentiment_score"], rand_sentiment)
            self.assertEqual(result["anomaly_score"], rand_anomaly_val)
            self.assertEqual(result["risk_score"], expected_risk)

    def test_process_stream_with_batch_analyze(self):
        rand_bytes = f"stream_data_{uuid.uuid4().hex}".encode('utf-8')
        stream_source = io.BytesIO(rand_bytes)

        with patch.object(self.hub.sentiment_analyzer, 'batch_analyze_stream', side_effect=TypeError("No batch")), \
             patch.object(self.hub.sentiment_analyzer, 'analyze') as mock_analyze, \
             patch.object(self.hub.anomaly_detector, 'analyze_stream') as mock_anomaly_stream:

            result = self.hub.process_stream(stream_source)

            mock_analyze.assert_called_once()
            mock_anomaly_stream.assert_called_once_with(stream_source)
            self.assertEqual(result["stream_status"], "PROCESSED")

    def test_export_report(self):
        success = self.hub.export_report(self.rand_ticker, self.rand_filename)

        self.assertTrue(success)
        self.assertTrue(os.path.exists(self.rand_filename))

        with open(self.rand_filename, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn(self.rand_ticker, content)

    def test_compute_market_risk_index_wrapper(self):
        rand_sentiment = round(random.uniform(-0.5, 0.5), 2)
        rand_anomaly = round(random.uniform(1.0, 10.0), 2)

        with patch('skills.market_sentiment_risk_hub.MarketSentimentRiskHub.evaluate_risk') as mock_eval:
            expected_dict = {
                "risk_index": 42.0,
                "risk_score": 42.0,
                "sentiment_score": rand_sentiment,
                "anomaly_score": rand_anomaly
            }
            mock_eval.return_value = expected_dict

            res = compute_market_risk_index(ticker=self.rand_ticker, exchange=self.rand_exchange)
            mock_eval.assert_called_once_with(ticker=self.rand_ticker, exchange=self.rand_exchange)
            self.assertEqual(res, expected_dict)

    def test_process_risk_stream_wrapper(self):
        rand_bytes = uuid.uuid4().hex.encode('utf-8')
        stream_source = io.BytesIO(rand_bytes)

        with patch('skills.market_sentiment_risk_hub.MarketSentimentRiskHub.process_stream') as mock_proc:
            expected_dict = {"stream_status": "PROCESSED", "risk_index": 0.0, "risk_score": 0.0}
            mock_proc.return_value = expected_dict

            res = process_risk_stream(stream_source)
            mock_proc.assert_called_once_with(stream_source)
            self.assertEqual(res, expected_dict)

if __name__ == '__main__':
    unittest.main()