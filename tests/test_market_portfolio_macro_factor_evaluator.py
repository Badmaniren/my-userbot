import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
from skills.market_portfolio_macro_factor_evaluator import start_new, evaluate_macro_factors

class TestMarketPortfolioMacroFactorEvaluator(unittest.TestCase):

    def test_start_new_with_collector_and_db(self):
        rand_fetched_data = uuid.uuid4().hex

        mock_collector = MagicMock()
        mock_collector.fetch.return_value = rand_fetched_data

        mock_db = MagicMock()

        dependencies = {
            "market_portfolio_collector_agent": mock_collector,
            "db_storage": mock_db
        }

        result = start_new(dependencies)

        mock_collector.fetch.assert_called_once()
        mock_db.store.assert_called_once_with(rand_fetched_data)
        self.assertEqual(result, rand_fetched_data)

    def test_start_new_with_anomaly_detector(self):
        rand_anomaly_result = uuid.uuid4().hex

        mock_anomaly_detector = MagicMock()
        mock_anomaly_detector.detect.return_value = rand_anomaly_result

        dependencies = {
            "market_anomaly_detector": mock_anomaly_detector
        }

        result = start_new(dependencies)

        mock_anomaly_detector.detect.assert_called_once()
        self.assertEqual(result, rand_anomaly_result)

    def test_start_new_requests_success(self):
        rand_text = uuid.uuid4().hex

        mock_response = MagicMock()
        mock_response.status_code = random.choice([200, 201, 204, 400, 404])
        mock_response.text = rand_text

        mock_db = MagicMock()

        dependencies = {
            "db_storage": mock_db
        }

        with patch("requests.get", return_value=mock_response) as mock_get:
            result = start_new(dependencies)
            mock_get.assert_called_once_with("http://localhost")
            mock_db.store.assert_called_once_with(rand_text)
            self.assertEqual(result, rand_text)

    def test_start_new_requests_server_error(self):
        mock_response = MagicMock()
        mock_response.status_code = 500

        dependencies = {}

        with patch("requests.get", return_value=mock_response) as mock_get:
            with self.assertRaises(Exception) as ctx:
                start_new(dependencies)
            self.assertIn("Stream processing failed", str(ctx.exception))
            mock_get.assert_called_once_with("http://localhost")

    def test_evaluate_macro_factors(self):
        rand_portfolio_id = uuid.uuid4().hex
        rand_portfolio_data = {uuid.uuid4().hex: random.randint(100, 1000)}
        rand_macro_indicators = {uuid.uuid4().hex: random.random()}

        result = evaluate_macro_factors(rand_portfolio_id, rand_portfolio_data, rand_macro_indicators)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], rand_portfolio_id)
        self.assertEqual(result["portfolio_data"], rand_portfolio_data)
        self.assertEqual(result["macro_indicators"], rand_macro_indicators)
        self.assertIn("impact_score", result)

if __name__ == "__main__":
    unittest.main()