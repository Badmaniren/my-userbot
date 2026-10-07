import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import io
try:
    import bs4
except ImportError:
    bs4 = None

from skills.market_portfolio_stress_scenario_matrix_evaluator import (
    MarketPortfolioStressScenarioMatrixEvaluator,
    evaluate_stress_scenario_matrix
)

class TestMarketPortfolioStressScenarioMatrixEvaluator(unittest.TestCase):

    def setUp(self):
        self.db_storage = MagicMock()
        self.tool_1 = MagicMock()
        self.tool_2 = MagicMock()
        self.evaluator = MarketPortfolioStressScenarioMatrixEvaluator(
            db_storage=self.db_storage,
            extractor_tool_1790087207=self.tool_1,
            extractor_tool_1790102839=self.tool_2
        )

    def test_evaluate_matrix_success(self):
        portfolio_id = uuid.uuid4().hex
        window = random.randint(1, 100)
        random_values = [{"value": random.uniform(100.0, 5000.0)} for _ in range(3)]
        self.db_storage.fetch_history.return_value = random_values

        random_content = uuid.uuid4().bytes

        with patch('skills.market_portfolio_stress_scenario_matrix_evaluator.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.content = random_content
            mock_get.return_value = mock_response

            result = self.evaluator.evaluate_matrix(portfolio_id, window)

            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertIn("evaluation_score", result)
            self.assertIn("payload_data", result)
            self.db_storage.fetch_history.assert_called_once_with(portfolio_id, window)
            mock_get.assert_called_once()

    def test_evaluate_matrix_empty_history(self):
        portfolio_id = uuid.uuid4().hex
        window = random.randint(1, 50)
        self.db_storage.fetch_history.return_value = []

        with patch('skills.market_portfolio_stress_scenario_matrix_evaluator.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.content = uuid.uuid4().bytes
            mock_get.return_value = mock_response

            result = self.evaluator.evaluate_matrix(portfolio_id, window)

            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertEqual(result["evaluation_score"], 0.0)

    def test_evaluate_stream_matrix(self):
        portfolio_id = uuid.uuid4().hex
        random_text = f"<html><body>{uuid.uuid4().hex}</body></html>".encode('utf-8')
        stream_mock = io.BytesIO(random_text)
        self.db_storage.fetch_stream.return_value = stream_mock

        result = self.evaluator.evaluate_stream_matrix(portfolio_id, stream_mock)

        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertTrue(result["fallback_triggered"])
        self.db_storage.fetch_stream.assert_called_once_with(portfolio_id)

    def test_detect_matrix_anomalies_true(self):
        token = uuid.uuid4().hex
        threshold = random.uniform(0.1, 0.9)
        metric = threshold + random.uniform(0.01, 1.0)
        self.tool_1.analyze.return_value = {"anomaly_metric": metric}

        is_anomaly = self.evaluator.detect_matrix_anomalies(token, threshold)

        self.assertTrue(is_anomaly)
        self.tool_1.analyze.assert_called_once_with(token)

    def test_detect_matrix_anomalies_false(self):
        token = uuid.uuid4().hex
        threshold = random.uniform(0.5, 1.5)
        metric = threshold - random.uniform(0.01, 0.5)
        self.tool_1.analyze.return_value = {"anomaly_metric": metric}

        is_anomaly = self.evaluator.detect_matrix_anomalies(token, threshold)

        self.assertIsInstance(is_anomaly, bool)
        self.assertFalse(is_anomaly)
        self.tool_1.analyze.assert_called_once_with(token)

    def test_evaluate_stress_scenario_matrix_with_score(self):
        portfolio_id = uuid.uuid4().hex
        evaluation_id = uuid.uuid4().hex
        base_score = random.uniform(0.1, 0.9)
        payload = {
            "portfolio_id": portfolio_id,
            "evaluation_id": evaluation_id,
            "monte_carlo_metrics": {"score": base_score}
        }

        res = evaluate_stress_scenario_matrix(payload)

        self.assertEqual(res["portfolio_id"], portfolio_id)
        self.assertEqual(res["evaluation_id"], evaluation_id)
        expected_score = round(float(base_score) * 1.1, 4)
        self.assertEqual(res["matrix_score"], expected_score)

    def test_evaluate_stress_scenario_matrix_without_score(self):
        portfolio_id = uuid.uuid4().hex
        evaluation_id = uuid.uuid4().hex
        payload = {
            "portfolio_id": portfolio_id,
            "evaluation_id": evaluation_id,
            "monte_carlo_metrics": {}
        }

        res = evaluate_stress_scenario_matrix(payload)

        self.assertEqual(res["portfolio_id"], portfolio_id)
        self.assertEqual(res["evaluation_id"], evaluation_id)
        self.assertEqual(res["matrix_score"], 0.85)

if __name__ == '__main__':
    unittest.main()