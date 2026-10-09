import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string

from skills.market_portfolio_stress_ml_var_estimator import (
    MarketPortfolioStressMLVaREstimator,
    VaREstimatorError
)

class TestMarketPortfolioStressMLVaREstimator(unittest.TestCase):

    def setUp(self):
        self.random_portfolio_id = str(uuid.uuid4())
        self.random_db_url = f"sqlite:///{uuid.uuid4().hex}.db"
        self.random_confidence = round(random.uniform(0.90, 0.99), 4)
        self.random_horizon = random.randint(1, 30)
        self.random_volatility = round(random.uniform(0.01, 0.50), 4)
        self.random_stress_factor = round(random.uniform(1.1, 3.5), 2)

        self.mock_db = MagicMock()
        self.mock_vol_forecaster = MagicMock()
        self.mock_scenario_evaluator = MagicMock()

        self.estimator = MarketPortfolioStressMLVaREstimator(
            db_storage=self.mock_db,
            market_portfolio_stress_ml_volatility_forecaster_v2=self.mock_vol_forecaster,
            market_portfolio_stress_scenario_matrix_evaluator=self.mock_scenario_evaluator
        )

    def test_estimate_var_success(self):
        raw_bytes = f"portfolio_data_{uuid.uuid4().hex}".encode('utf-8')
        mock_stream = io.BytesIO(raw_bytes)

        self.mock_vol_forecaster.predict_volatility.return_value = self.random_volatility
        self.mock_scenario_evaluator.evaluate_matrix.return_value = {
            "stress_factor": self.random_stress_factor,
            "impact": random.choice([-50000.0, -120000.5, -3400.2])
        }

        with patch('skills.market_portfolio_stress_ml_var_estimator.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raw = mock_stream
            mock_response.iter_content = lambda chunk_size: [raw_bytes]
            mock_get.return_value = mock_response

            result = self.estimator.calculate_ml_var(
                portfolio_id=self.random_portfolio_id,
                confidence_level=self.random_confidence,
                time_horizon_days=self.random_horizon
            )

        self.assertIn("var_value", result)
        self.assertIn("volatility", result)
        self.assertEqual(result["volatility"], self.random_volatility)
        self.assertEqual(result["portfolio_id"], self.random_portfolio_id)
        self.assertGreater(result["var_value"], 0.0)

    def test_estimate_var_forecaster_failure_raises_exception(self):
        self.mock_vol_forecaster.predict_volatility.side_effect = RuntimeError(uuid.uuid4().hex)

        with self.assertRaises(VaREstimatorError) as context:
            self.estimator.calculate_ml_var(
                portfolio_id=self.random_portfolio_id,
                confidence_level=self.random_confidence,
                time_horizon_days=self.random_horizon
            )

        self.assertIn(self.random_portfolio_id, str(context.exception))

    def test_estimate_var_invalid_confidence_raises_value_error(self):
        invalid_confidence = random.choice([-0.5, 1.2, 5.0])

        with self.assertRaises(ValueError):
            self.estimator.calculate_ml_var(
                portfolio_id=self.random_portfolio_id,
                confidence_level=invalid_confidence,
                time_horizon_days=self.random_horizon
            )

    def test_stress_var_computation_with_corrupted_io_stream(self):
        corrupted_stream = io.BytesIO(b"")
        self.mock_vol_forecaster.predict_volatility.return_value = self.random_volatility

        with patch('skills.market_portfolio_stress_ml_var_estimator.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_get.return_value = mock_response

            with self.assertRaises(VaREstimatorError):
                self.estimator.calculate_ml_var(
                    portfolio_id=self.random_portfolio_id,
                    confidence_level=self.random_confidence,
                    time_horizon_days=self.random_horizon
                )

    def test_audit_logging_on_successful_estimation(self):
        raw_bytes = uuid.uuid4().hex.encode('ascii')
        self.mock_vol_forecaster.predict_volatility.return_value = self.random_volatility
        self.mock_scenario_evaluator.evaluate_matrix.return_value = {
            "stress_factor": self.random_stress_factor,
            "impact": -9999.99
        }

        with patch('skills.market_portfolio_stress_ml_var_estimator.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.iter_content = lambda chunk_size: [raw_bytes]
            mock_get.return_value = mock_response

            self.estimator.calculate_ml_var(
                portfolio_id=self.random_portfolio_id,
                confidence_level=self.random_confidence,
                time_horizon_days=self.random_horizon
            )

        self.mock_db.log_event.assert_called_once()
        logged_args = self.mock_db.log_event.call_args[0][0]
        self.assertEqual(logged_args["portfolio_id"], self.random_portfolio_id)

    def test_randomized_stress_multiplier_logic(self):
        custom_impact = -abs(round(random.uniform(1000.0, 1000000.0), 2))
        self.mock_vol_forecaster.predict_volatility.return_value = self.random_volatility
        self.mock_scenario_evaluator.evaluate_matrix.return_value = {
            "stress_factor": self.random_stress_factor,
            "impact": custom_impact
        }

        with patch('skills.market_portfolio_stress_ml_var_estimator.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.iter_content = lambda chunk_size: [b"random_chunk"]
            mock_get.return_value = mock_response

            res = self.estimator.calculate_ml_var(
                portfolio_id=self.random_portfolio_id,
                confidence_level=self.random_confidence,
                time_horizon_days=self.random_horizon
            )

        self.assertEqual(res["stress_impact"], custom_impact)
        self.assertEqual(res["applied_stress_factor"], self.random_stress_factor)

if __name__ == '__main__':
    unittest.main()