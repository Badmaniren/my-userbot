import unittest
from unittest.mock import patch
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
        self.db_storage = unittest.mock.MagicMock()
        self.extractor_tool_1 = unittest.mock.MagicMock()
        self.extractor_tool_2 = unittest.mock.MagicMock()
        self.evaluator = MarketPortfolioStressScenarioMatrixEvaluator(
            db_storage=self.db_storage,
            extractor_tool_1790087207=self.extractor_tool_1,
            extractor_tool_102839=self.extractor_tool_2
        )

    def test_evaluate_matrix_success(self):
        portfolio_id = uuid.uuid4().hex
        historical_window = random.randint(10, 100)
        rand_val = random.uniform(100.0, 5000.0)
        self.db_storage.fetch_history.return_value = [{"value": rand_val}]
        
        rand_payload = uuid.uuid4().hex.encode('utf-8')
        with patch('requests.get') as mock_get:
            mock_response = unittest.mock.MagicMock()
            mock_response.content = rand_payload
            mock_get.return_value = mock_response
            
            result = self.evaluator.evaluate_matrix(portfolio_id, historical_window)
            
            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertIn("evaluation_score", result)
            self.assertEqual(result["payload_data"], rand_payload.decode('utf-8'))
            self.db_storage.fetch_history.assert_called_once_with(portfolio_id, historical_window)

    def test_evaluate_matrix_empty_history(self):
        portfolio_id = uuid.uuid4().hex
        historical_window = random.randint(1, 10)
        self.db_storage.fetch_history.return_value = []
        
        rand_payload = ''.join(random.choices(string.ascii_letters, k=15)).encode('utf-8')
        with patch('requests.get') as mock_get:
            mock_response = unittest.mock.MagicMock()
            mock_response.content = rand_payload
            mock_get.return_value = mock_response
            
            result = self.evaluator.evaluate_matrix(portfolio_id, historical_window)
            
            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertEqual(result["evaluation_score"], 0.0)
            self.assertEqual(result["payload_data"], rand_payload.decode('utf-8'))

    def test_evaluate_stream_matrix(self):
        portfolio_id = uuid.uuid4().hex
        rand_tag = uuid.uuid4().hex
        stream_content = f"<html><body><div>{rand_tag}</div></body></html>".encode('utf-8')
        mock_stream = io.BytesIO(stream_content)
        self.db_storage.fetch_stream.return_value = mock_stream
        
        result = self.evaluator.evaluate_stream_matrix(portfolio_id, mock_stream)
        
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertTrue(result["fallback_triggered"])
        self.db_storage.fetch_stream.assert_called_once_with(portfolio_id)

    def test_detect_matrix_anomalies_true(self):
        scenario_token = uuid.uuid4().hex
        threshold = random.uniform(0.1, 0.5)
        anomaly_metric = threshold + random.uniform(0.1, 1.0)
        
        self.extractor_tool_1.analyze.return_value = {"anomaly_metric": anomaly_metric}
        
        res = self.evaluator.detect_matrix_anomalies(scenario_token, threshold)
        
        self.assertTrue(res)
        self.extractor_tool_1.analyze.assert_called_once_with(scenario_token)

    def test_detect_matrix_anomalies_false(self):
        scenario_token = uuid.uuid4().hex
        threshold = random.uniform(0.5, 1.0)
        anomaly_metric = threshold - random.uniform(0.01, 0.4)
        
        self.extractor_tool_1.analyze.return_value = {"anomaly_metric": anomaly_metric}
        
        res = self.evaluator.detect_matrix_anomalies(scenario_token, threshold)
        
        self.assertIsInstance(res, bool)
        self.assertFalse(res)
        self.extractor_tool_1.analyze.assert_called_once_with(scenario_token)

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
        self.assertEqual(res["matrix_score"], round(base_score * 1.1, 4))

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

if __name__ == "__main__":
    unittest.main()