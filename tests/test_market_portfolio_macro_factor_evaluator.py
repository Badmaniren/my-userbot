import unittest
from unittest.mock import patch, Mock
import uuid
import random
import io
import requests

from skills.market_portfolio_macro_factor_evaluator import start_new, evaluate_macro_factors


class TestMarketPortfolioMacroFactorEvaluator(unittest.TestCase):

    def test_start_new_success_response(self):
        rand_target_id = str(uuid.uuid4())
        rand_factor = str(uuid.uuid4())
        rand_token = str(uuid.uuid4())
        payload = {"target_id": rand_target_id}

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "evaluated_factor": rand_factor,
            "token": rand_token
        }

        with patch("requests.get", return_value=mock_response) as mock_get:
            result = start_new(payload)
            mock_get.assert_called_once_with(
                "http://localhost/api/evaluate",
                params={"id": rand_target_id},
                timeout=1
            )
            self.assertEqual(result["evaluated_factor"], rand_factor)
            self.assertEqual(result["token"], rand_token)

    def test_start_new_request_exception_fallback(self):
        rand_target_id = str(uuid.uuid4())
        payload = {"target_id": rand_target_id}

        with patch("requests.get", side_effect=requests.exceptions.RequestException("Network error")) as mock_get:
            result = start_new(payload)
            mock_get.assert_called_once()
            self.assertEqual(result["evaluated_factor"], rand_target_id)
            self.assertIsInstance(result["token"], str)
            self.assertTrue(len(result["token"]) > 0)

    def test_start_new_status_code_not_200_fallback(self):
        rand_target_id = random.randint(1000, 9999)
        payload = {"target_id": rand_target_id}

        mock_response = Mock()
        mock_response.status_code = random.choice([400, 404, 500, 502])

        with patch("requests.get", return_value=mock_response) as mock_get:
            result = start_new(payload)
            mock_get.assert_called_once()
            self.assertEqual(result["evaluated_factor"], str(rand_target_id))
            self.assertIsInstance(result["token"], str)

    def test_start_new_none_target_id_fallback(self):
        payload = {"target_id": None}

        with patch("requests.get", side_effect=requests.exceptions.RequestException()) as mock_get:
            result = start_new(payload)
            mock_get.assert_called_once()
            self.assertIsInstance(result["evaluated_factor"], str)
            self.assertIsInstance(result["token"], str)
            self.assertTrue(len(result["evaluated_factor"]) > 0)
            self.assertTrue(len(result["token"]) > 0)

    def test_evaluate_macro_factors(self):
        rand_portfolio_id = f"port_{uuid.uuid4().hex[:10]}"
        rand_indicators = {
            f"indicator_{random.choice(['cpi', 'gdp', 'rates'])}": random.random()
        }

        result = evaluate_macro_factors(rand_portfolio_id, rand_indicators)

        self.assertIn("evaluation_id", result)
        self.assertTrue(result["evaluation_id"].startswith("eval_"))
        self.assertEqual(result["portfolio_id"], rand_portfolio_id)
        self.assertEqual(result["indicators"], rand_indicators)


if __name__ == "__main__":
    unittest.main()