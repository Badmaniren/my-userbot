import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import os
from skills.market_portfolio_sentiment_stress_correlator import (
    MarketPortfolioSentimentStressCorrelator,
    correlate_sentiment_with_stress
)

class TestMarketPortfolioSentimentStressCorrelator(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.news_text = ''.join(random.choices(string.ascii_letters + string.digits, k=64))
        self.window = random.randint(10, 100)
        self.filename = f"{uuid.uuid4().hex}.log"
        self.stream_bytes = io.BytesIO(uuid.uuid4().bytes)
        self.token = uuid.uuid4().hex
        self.threshold = random.uniform(0.1, 0.9)
        self.correlator = MarketPortfolioSentimentStressCorrelator()

    @patch('skills.market_portfolio_sentiment_stress_correlator.MarketNewsSentimentAnalyzer')
    @patch('skills.market_portfolio_sentiment_stress_correlator.MarketPortfolioStressScenarioMatrixEvaluator')
    def test_correlate_success(self, mock_stress_eval_cls, mock_sentiment_analyzer_cls):
        mock_sentiment_instance = mock_sentiment_analyzer_cls.return_value
        mock_stress_instance = mock_stress_eval_cls.return_value

        expected_score = random.uniform(-1.0, 1.0)
        expected_drawdown = random.uniform(1.0, 50.0)

        mock_sentiment_instance.analyze.return_value = {"sentiment_score": expected_score}
        mock_stress_instance.evaluate_matrix.return_value = {"max_drawdown": expected_drawdown}

        correlator = MarketPortfolioSentimentStressCorrelator()
        result = correlator.correlate(self.portfolio_id, self.news_text, self.window)

        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertIn("correlation_coefficient", result)
        self.assertIn("panic_sensitivity_index", result)
        self.assertEqual(result["sentiment_data"]["sentiment_score"], expected_score)
        self.assertEqual(result["stress_data"]["max_drawdown"], expected_drawdown)

    @patch('skills.market_portfolio_sentiment_stress_correlator.MarketNewsSentimentAnalyzer')
    @patch('skills.market_portfolio_sentiment_stress_correlator.MarketPortfolioStressScenarioMatrixEvaluator')
    def test_correlate_stream_success(self, mock_stress_eval_cls, mock_sentiment_analyzer_cls):
        mock_sentiment_instance = mock_sentiment_analyzer_cls.return_value
        mock_stress_instance = mock_stress_eval_cls.return_value

        batch_output = [{"id": uuid.uuid4().hex, "score": random.random()}]
        stream_matrix_output = {"status": uuid.uuid4().hex, "matrix": [random.randint(1, 10)]}

        mock_sentiment_instance.batch_analyze_stream.return_value = batch_output
        mock_stress_instance.evaluate_stream_matrix.return_value = stream_matrix_output

        correlator = MarketPortfolioSentimentStressCorrelator()
        result = correlator.correlate_stream(self.portfolio_id, self.filename, self.stream_bytes)

        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["aggregated_sentiment"], batch_output)
        self.assertEqual(result["stream_stress_matrix"], stream_matrix_output)

    @patch('skills.market_portfolio_sentiment_stress_correlator.MarketPortfolioStressScenarioMatrixEvaluator')
    def test_detect_panic_anomalies(self, mock_stress_eval_cls):
        mock_stress_instance = mock_stress_eval_cls.return_value
        expected_anomaly_flag = random.choice([True, False])
        mock_stress_instance.detect_matrix_anomalies.return_value = expected_anomaly_flag

        correlator = MarketPortfolioSentimentStressCorrelator()
        result = correlator.detect_panic_anomalies(self.token, self.threshold)

        self.assertEqual(result, expected_anomaly_flag)
        mock_stress_instance.detect_matrix_anomalies.assert_called_once_with(self.token, self.threshold)

    def test_correlate_sentiment_with_stress_function(self):
        sentiment_score = random.uniform(-1.0, 1.0)
        drawdown_val = random.uniform(5.0, 45.0)
        correlation_factor = random.uniform(0.5, 2.0)

        payload = {
            "portfolio_id": self.portfolio_id,
            "sentiment_data": {"sentiment_score": sentiment_score},
            "stress_matrix": {"max_drawdown": drawdown_val},
            "correlation_factor": correlation_factor
        }

        result = correlate_sentiment_with_stress(payload)

        expected_sensitivity = float(abs(sentiment_score * drawdown_val) * correlation_factor)

        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["sensitivity_index"], expected_sensitivity)

        expected_path = f"reports/sentiment_stress_{self.portfolio_id}.json"
        self.assertTrue(os.path.exists(expected_path))

        if os.path.exists(expected_path):
            os.remove(expected_path)

if __name__ == "__main__":
    unittest.main()