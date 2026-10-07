import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string
from skills.market_portfolio_stress_scenario_matrix_evaluator import (
    MarketPortfolioStressScenarioMatrixEvaluator,
    evaluate_stress_scenario_matrix
)

class TestMarketPortfolioStressScenarioMatrixEvaluator(unittest.TestCase):
    def setUp(self):
        self.db_storage = MagicMock()
        self.extractor_1 = MagicMock()
        self.extractor_2 = MagicMock()
        self.evaluator = MarketPortfolioStressScenarioMatrixEvaluator(
            db_storage=self.db_storage,
            extractor_tool_1790087207=self.extractor_1,
            extractor_tool_1790102839=self.extractor_2
        )

    def test_evaluate_matrix_success(self):
        portfolio_id = uuid.uuid4().hex
        historical_window = random.randint(10, 100)
        rand_val = random.uniform(100.0, 5000.0)
        
        self.db_storage.fetch_history.return_value = [{"value": rand_val}]
        
        expected_content = ''.join(random.choices(string.ascii_letters, k=20)).encode('utf-8')
        mock_response = MagicMock()
        mock_response.content = expected_content

        with patch('requests.get', return_value=mock_response) as mock_get:
            result = self.evaluator.evaluate_matrix(portfolio_id, historical_window)
            
            mock_get.assert_called_once_with("https://example.com/api/stress-matrix")
            self.db_storage.fetch_history.assert_called_once_with(portfolio_id, historical_window)
            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertEqual(result["payload_data"], expected_content.decode('utf-8'))
            
            expected_score = round(min(max((rand_val / 1.0) / 1000.0, 0.0), 1.0), 4)
            self.assertEqual(result["evaluation_score"], expected_score)

    def test_evaluate_matrix_empty_history(self):
        portfolio_id = uuid.uuid4().hex
        historical_window = random.randint(1, 50)
        
        self.db_storage.fetch_history.return_value = []
        
        mock_response = MagicMock()
        mock_response.content = b""

        with patch('requests.get', return_value=mock_response):
            result = self.evaluator.evaluate_matrix(portfolio_id, historical_window)
            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertEqual(result["evaluation_score"], 0.0)
            self.assertEqual(result["payload_data"], "")

    def test_evaluate_stream_matrix(self):
        portfolio_id = uuid.uuid4().hex
        random_html_tag = ''.join(random.choices(string.ascii_lowercase, k=5))
        random_text = ''.join(random.choices(string.ascii_letters + string.digits, k=30))
        html_content = f"<{random_html_tag}>{random_text}</{random_html_tag}>".encode('utf-8')
        
        stream_mock = io.BytesIO(html_content)
        self.db_storage.fetch_stream.return_value = stream_mock

        result = self.evaluator.evaluate_stream_matrix(portfolio_id, stream_mock)
        
        self.db_storage.fetch_stream.assert_called_once_with(portfolio_id)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertTrue(result["fallback_triggered"])

    def test_detect_matrix_anomalies_true(self):
        scenario_token = uuid.uuid4().hex
        threshold = random.uniform(0.1, 0.9)
        anomaly_metric = threshold + random.uniform(0.01, 0.5)
        
        self.extractor_1.analyze.return_value = {"anomaly_metric": anomaly_metric}

        is_anomaly = self.evaluator.detect_matrix_anomalies(scenario_token, threshold)
        
        self.extractor_1.analyze.assert_called_once_with(scenario_token)
        self.assertTrue(is_anomaly)

    def test_detect_matrix_anomalies_false(self):
        scenario_token = uuid.uuid4().hex
        threshold = random.uniform(0.5, 1.5)
        anomaly_metric = threshold - random.uniform(0.01, 0.4)
        
        self.extractor_1.analyze.return_value = {"anomaly_metric": anomaly_metric}

        is_anomaly = self.evaluator.detect_matrix_anomalies(scenario_token, threshold)
        
        self.extractor_1.analyze.assert_called_once_with(scenario_token)
        self.assertFalse(is_anomaly)

    def test_evaluate_stress_scenario_matrix_with_score(self):
        portfolio_id = uuid.uuid4().hex
        evaluation_id = uuid.uuid4().hex
        base_score = random.uniform(0.1, 0.9)
        
        payload = {
            "portfolio_id": portfolio_id,
            "evaluation_id": evaluation_id,
            "monte_carlo_metrics": {
                "score": base_score
            }
        }

        result = evaluate_stress_scenario_matrix(payload)
        
        self.assertEqual(result["evaluation_id"], evaluation_id)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["matrix_score"], round(base_score * 1.1, 4))

    def test_evaluate_stress_scenario_matrix_without_score(self):
        portfolio_id = uuid.uuid4().hex
        evaluation_id = uuid.uuid4().hex
        
        payload = {
            "portfolio_id": portfolio_id,
            "evaluation_id": evaluation_id,
            "monte_carlo_metrics": {}
        }

        result = evaluate_stress_scenario_matrix(payload)
        
        self.assertEqual(result["evaluation_id"], evaluation_id)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["matrix_score"], 0.85)

if __name__ == '__main__':
    unittest.main()