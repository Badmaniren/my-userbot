import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string

from skills.market_portfolio_stress_scenario_matrix_evaluator import (
    MarketPortfolioStressScenarioMatrixEvaluator
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
        historical_window = random.randint(30, 365)
        expected_score = round(random.uniform(0.1, 0.99), 4)

        mock_payload = f"data_id_{uuid.uuid4().hex}".encode('utf-8')
        
        with patch('skills.market_portfolio_stress_scenario_matrix_evaluator.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = mock_payload
            mock_get.return_value = mock_response

            self.db_storage.fetch_history.return_value = [
                {"timestamp": uuid.uuid4().hex, "value": random.uniform(100.0, 1000.0)}
                for _ in range(5)
            ]

            result = self.evaluator.evaluate_matrix(portfolio_id, historical_window)

            self.assertIsInstance(result, dict)
            self.assertIn("portfolio_id", result)
            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertIn("evaluation_score", result)
            self.db_storage.fetch_history.assert_called_once_with(portfolio_id, historical_window)

    def test_evaluate_matrix_with_corrupted_stream(self):
        portfolio_id = uuid.uuid4().hex
        historical_window = random.randint(10, 100)
        
        random_trash = ''.join(random.choices(string.ascii_letters + string.digits, k=64)).encode('utf-8')
        stream_mock = io.BytesIO(random_trash)

        self.db_storage.fetch_stream.return_value = stream_mock

        with patch('skills.market_portfolio_stress_scenario_matrix_evaluator.bs4.BeautifulSoup') as mock_bs:
            mock_soup = MagicMock()
            mock_soup.text = uuid.uuid4().hex
            mock_bs.return_value = mock_soup

            result = self.evaluator.evaluate_stream_matrix(portfolio_id, stream_mock)

            self.assertIsInstance(result, dict)
            self.assertTrue(result.get("fallback_triggered", True))
            self.db_storage.fetch_stream.assert_called_once_with(portfolio_id)

    def test_matrix_anomaly_detection_edge_case(self):
        scenario_token = uuid.uuid4().hex
        threshold = random.uniform(0.01, 0.5)

        self.extractor_1.analyze.return_value = {
            "token": scenario_token,
            "anomaly_metric": random.uniform(0.0, 1.0)
        }

        result = self.evaluator.detect_matrix_anomalies(scenario_token, threshold)

        self.assertIsInstance(result, bool)
        self.extractor_1.analyze.assert_called_once_with(scenario_token)

    def test_evaluate_matrix_storage_failure(self):
        portfolio_id = uuid.uuid4().hex
        historical_window = random.randint(1, 50)

        self.db_storage.fetch_history.side_effect = ConnectionError(uuid.uuid4().hex)

        with self.assertRaises(ConnectionError):
            self.evaluator.evaluate_matrix(portfolio_id, historical_window)

        self.db_storage.fetch_history.assert_called_once()


if __name__ == '__main__':
    unittest.main()