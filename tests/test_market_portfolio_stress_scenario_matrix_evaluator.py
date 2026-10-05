import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import io
from skills.market_portfolio_stress_scenario_matrix_evaluator import (
    MarketPortfolioStressScenarioMatrixEvaluator,
    evaluate_stress_scenario_matrix
)

class TestMarketPortfolioStressScenarioMatrixEvaluator(unittest.TestCase):
    def setUp(self):
        self.db_storage = MagicMock()
        self.extractor_tool_1 = MagicMock()
        self.extractor_tool_2 = MagicMock()
        self.evaluator = MarketPortfolioStressScenarioMatrixEvaluator(
            db_storage=self.db_storage,
            extractor_tool_1790087207=self.extractor_tool_1,
            extractor_tool_1790102839=self.extractor_tool_2
        )

    def test_evaluate_matrix_success(self):
        portfolio_id = uuid.uuid4().hex
        historical_window = random.randint(10, 100)
        rand_value = round(random.uniform(100.0, 5000.0), 2)
        
        self.db_storage.fetch_history.return_value = [{"value": rand_value}]
        
        expected_content = uuid.uuid4().hex.encode('utf-8')
        
        with patch('skills.market_portfolio_stress_scenario_matrix_evaluator.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.content = expected_content
            mock_get.return_value = mock_response
            
            result = self.evaluator.evaluate_matrix(portfolio_id, historical_window)
            
            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertIn("evaluation_score", result)
            self.assertEqual(result["payload_data"], expected_content.decode('utf-8'))
            self.db_storage.fetch_history.assert_called_once_with(portfolio_id, historical_window)
            mock_get.assert_called_once()

    def test_evaluate_matrix_empty_history(self):
        portfolio_id = uuid.uuid4().hex
        historical_window = random.randint(1, 10)
        self.db_storage.fetch_history.return_value = []
        
        payload_bytes = uuid.uuid4().hex.encode('utf-8')
        
        with patch('skills.market_portfolio_stress_scenario_matrix_evaluator.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.content = payload_bytes
            mock_get.return_value = mock_response
            
            result = self.evaluator.evaluate_matrix(portfolio_id, historical_window)
            
            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertEqual(result["evaluation_score"], 0.0)
            self.assertEqual(result["payload_data"], payload_bytes.decode('utf-8'))

    def test_evaluate_stream_matrix(self):
        portfolio_id = uuid.uuid4().hex
        random_html_tag = uuid.uuid4().hex
        stream_content = f"<html><body><div>{random_html_tag}</div></body></html>".encode('utf-8')
        stream_mock = io.BytesIO(stream_content)
        
        self.db_storage.fetch_stream.return_value = stream_mock
        
        result = self.evaluator.evaluate_stream_matrix(portfolio_id, stream_mock)
        
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertTrue(result["fallback_triggered"])
        self.db_storage.fetch_stream.assert_called_once_with(portfolio_id)

    def test_detect_matrix_anomalies_true(self):
        scenario_token = uuid.uuid4().hex
        threshold = random.uniform(0.1, 0.5)
        anomaly_metric = threshold + random.uniform(0.01, 0.5)
        
        self.extractor_tool_1.analyze.return_value = {"anomaly_metric": anomaly_metric}
        
        is_anomaly = self.evaluator.detect_matrix_anomalies(scenario_token, threshold)
        
        self.assertTrue(is_anomaly)
        self.extractor_tool_1.analyze.assert_called_once_with(scenario_token)

    def test_detect_matrix_anomalies_false(self):
        scenario_token = uuid.uuid4().hex
        threshold = random.uniform(0.5, 1.0)
        anomaly_metric = threshold - random.uniform(0.01, 0.4)
        
        self.extractor_tool_1.analyze.return_value = {"anomaly_metric": anomaly_metric}
        
        is_anomaly = self.evaluator.detect_matrix_anomalies(scenario_token, threshold)
        
        self.assertFalse(is_anomaly)
        self.extractor_tool_1.analyze.assert_called_once_with(scenario_token)

    def test_evaluate_stress_scenario_matrix_with_score(self):
        portfolio_id = uuid.uuid4().hex
        evaluation_id = uuid.uuid4().hex
        base_score = round(random.uniform(0.1, 0.9), 2)
        
        payload = {
            "portfolio_id": portfolio_id,
            "evaluation_id": evaluation_id,
            "monte_carlo_metrics": {
                "score": base_score
            }
        }
        
        result = evaluate_stress_scenario_matrix(payload)
        
        expected_score = round(float(base_score) * 1.1, 4)
        self.assertEqual(result["evaluation_id"], evaluation_id)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["matrix_score"], expected_score)

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

if __name__ == "__main__":
    unittest.main()