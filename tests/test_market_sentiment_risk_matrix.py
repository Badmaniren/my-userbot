import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import sys
import types

from skills.market_sentiment_risk_matrix import MarketSentimentRiskMatrix

class TestMarketSentimentRiskMatrix(unittest.TestCase):

    def setUp(self):
        self.risk_matrix = MarketSentimentRiskMatrix()

    def test_calculate_risk_matrix_success(self):
        rand_sentiment_score = round(random.uniform(-1.0, 1.0), 4)
        rand_anomaly_factor = round(random.uniform(0.0, 10.0), 4)
        rand_portfolio_id = uuid.uuid4().hex

        mock_sentiment_analyzer = MagicMock()
        mock_sentiment_analyzer.analyze.return_value = rand_sentiment_score

        mock_anomaly_detector = MagicMock()
        mock_anomaly_detector.detect.return_value = rand_anomaly_factor

        with patch('skills.market_sentiment_risk_matrix.market_news_sentiment_analyzer', mock_sentiment_analyzer), \
             patch('skills.market_sentiment_risk_matrix.market_anomaly_detector', mock_anomaly_detector):

            result = self.risk_matrix.calculate_matrix(rand_portfolio_id)

            self.assertIsInstance(result, dict)
            self.assertIn("portfolio_id", result)
            self.assertEqual(result["portfolio_id"], rand_portfolio_id)
            self.assertIn("sentiment_score", result)
            self.assertEqual(result["sentiment_score"], rand_sentiment_score)
            self.assertIn("anomaly_factor", result)
            self.assertEqual(result["anomaly_factor"], rand_anomaly_factor)
            self.assertIn("drawdown_probability", result)
            self.assertIsInstance(result["drawdown_probability"], float)

    def test_calculate_risk_matrix_with_empty_stream(self):
        rand_portfolio_id = uuid.uuid4().hex
        random_bytes = ''.join(random.choices(string.ascii_letters + string.digits, k=32)).encode('utf-8')
        mock_stream = io.BytesIO(random_bytes)

        mock_storage = MagicMock()
        mock_storage.fetch_stream.return_value = mock_stream

        with patch('skills.market_sentiment_risk_matrix.db_storage', mock_storage):
            result = self.risk_matrix.evaluate_from_stream(rand_portfolio_id)
            self.assertIsInstance(result, dict)
            self.assertTrue(result.get("processed"))
            self.assertEqual(result.get("stream_len"), len(random_bytes))

    def test_evaluate_drawdown_probability_edge_cases(self):
        extreme_sentiment = -1.0
        extreme_anomaly = 99.99

        score = self.risk_matrix._compute_drawdown_prob(extreme_sentiment, extreme_anomaly)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_matrix_generation_failure_handling(self):
        rand_portfolio_id = uuid.uuid4().hex
        mock_sentiment_analyzer = MagicMock()
        mock_sentiment_analyzer.analyze.side_effect = Exception("Random sentiment failure: " + uuid.uuid4().hex)

        with patch('skills.market_sentiment_risk_matrix.market_news_sentiment_analyzer', mock_sentiment_analyzer):
            with self.assertRaises(Exception):
                self.risk_matrix.calculate_matrix(rand_portfolio_id)

    def test_risk_matrix_export_data(self):
        rand_export_target = uuid.uuid4().hex + ".csv"
        mock_exporter = MagicMock()
        mock_exporter.export.return_value = True

        with patch('skills.market_sentiment_risk_matrix.market_portfolio_data_exporter', mock_exporter):
            res = self.risk_matrix.export_matrix(rand_export_target, {"status": "ok"})
            self.assertTrue(res)
            mock_exporter.export.assert_called_once()
            called_args = mock_exporter.export.call_args[0]
            self.assertEqual(called_args[0], rand_export_target)

if __name__ == '__main__':
    unittest.main()