import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.market_portfolio_ml_stress_evaluator import (
    MarketPortfolioMLStressEvaluator,
    StressEvaluationError,
    InsufficientFeatureDataError
)


class TestMarketPortfolioMLStressEvaluator(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.scenario_code = str(uuid.uuid4())
        self.asset_id = str(uuid.uuid4())
        self.target_url = f"https://{uuid.uuid4().hex}.internal/market/data"
        self.mock_db = MagicMock()
        self.mock_extractor = MagicMock()
        self.mock_anomaly_detector = MagicMock()
        self.window_size = random.randint(10, 50)
        self.confidence = round(random.uniform(0.90, 0.99), 2)

        self.evaluator = MarketPortfolioMLStressEvaluator(
            db_storage=self.mock_db,
            extractor_tool=self.mock_extractor,
            market_anomaly_detector=self.mock_anomaly_detector,
            window_size=self.window_size
        )

    def test_composition_and_initialization(self):
        self.assertEqual(self.evaluator.window_size, self.window_size)
        self.assertEqual(self.evaluator.db_storage, self.mock_db)
        self.assertIsNotNone(self.evaluator.feature_builder)
        self.assertIsNotNone(self.evaluator.volatility_forecaster)

    def test_evaluate_stress_resilience_success(self):
        random_prices = [random.uniform(100.0, 200.0) for _ in range(self.window_size + 10)]
        expected_volatility = random.uniform(0.15, 0.45)
        expected_var = random.uniform(0.01, 0.08)
        expected_score = round(random.uniform(50.0, 99.9), 2)

        feature_vector_mock = {
            "asset_id": self.asset_id,
            "volatility": expected_volatility,
            "tail_risk": {"var": expected_var}
        }

        forecast_mock = {
            "portfolio_id": self.portfolio_id,
            "scenario_code": self.scenario_code,
            "predicted_volatility": expected_volatility * 1.5,
            "stress_score": expected_score
        }

        with patch('skills.market_portfolio_ml_stress_evaluator.MarketPortfolioMLFeatureBuilder') as mock_fb_cls, \
             patch('skills.market_portfolio_ml_stress_evaluator.MarketPortfolioStressMLVolatilityForecasterV2') as mock_vf_cls:
            
            mock_fb_instance = mock_fb_cls.return_value
            mock_fb_instance.build_full_feature_vector_from_source.return_value = feature_vector_mock
            
            mock_vf_instance = mock_vf_cls.return_value
            mock_vf_instance.forecast_volatility.return_value = forecast_mock

            result = self.evaluator.evaluate_portfolio_stress_resilience(
                portfolio_id=self.portfolio_id,
                scenario_code=self.scenario_code,
                source_url=self.target_url
            )

            self.assertIsInstance(result, dict)
            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertEqual(result["scenario_code"], self.scenario_code)
            self.assertEqual(result["stress_score"], expected_score)
            self.assertIn("features", result)
            self.assertIn("forecast", result)

    def test_evaluate_stress_resilience_insufficient_data(self):
        with patch('skills.market_portfolio_ml_stress_evaluator.MarketPortfolioMLFeatureBuilder') as mock_fb_cls:
            mock_fb_instance = mock_fb_cls.return_value
            from skills.market_portfolio_ml_feature_builder import InsufficientDataError
            mock_fb_instance.build_full_feature_vector_from_source.side_effect = InsufficientDataError(uuid.uuid4().hex)

            with self.assertRaises(InsufficientFeatureDataError):
                self.evaluator.evaluate_portfolio_stress_resilience(
                    portfolio_id=self.portfolio_id,
                    scenario_code=self.scenario_code,
                    source_url=self.target_url
                )

    def test_run_deep_drawdown_probability_monte_carlo(self):
        base_vol = random.uniform(0.1, 0.3)
        matrix_size = random.randint(5, 15)
        matrix_data = [[random.uniform(-0.05, 0.05) for _ in range(matrix_size)] for _ in range(matrix_size)]
        expected_drawdown_prob = round(random.uniform(0.0, 1.0), 4)

        monte_carlo_result = {
            "base_volatility": base_vol,
            "deep_drawdown_probability": expected_drawdown_prob,
            "simulations": matrix_size * 100
        }

        with patch.object(self.evaluator.volatility_forecaster, 'run_monte_carlo_simulation', return_value=monte_carlo_result) as mock_mc:
            res = self.evaluator.calculate_deep_drawdown_probability(
                base_volatility=base_vol,
                matrix_data=matrix_data
            )

            mock_mc.assert_called_once_with(base_vol, matrix_data)
            self.assertEqual(res["deep_drawdown_probability"], expected_drawdown_prob)
            self.assertEqual(res["base_volatility"], base_vol)

    def test_parse_stream_payload_handling(self):
        random_payload = uuid.uuid4().hex.encode('utf-8')
        stream = io.BytesIO(random_payload)
        expected_parsed_str = random_payload.decode('utf-8')

        with patch.object(self.evaluator.volatility_forecaster, 'parse_stream_payload', return_value=expected_parsed_str) as mock_parse:
            output = self.evaluator.parse_external_stream(stream)
            mock_parse.assert_called_once_with(stream)
            self.assertEqual(output, expected_parsed_str)

    def test_forecast_external_ml_metrics_integration(self):
        external_metrics = {
            "metric_id": uuid.uuid4().hex,
            "ml_score": random.uniform(10.0, 90.0)
        }

        with patch.object(self.evaluator.volatility_forecaster, 'fetch_external_ml_metrics', return_value=external_metrics) as mock_fetch:
            res = self.evaluator.get_external_metrics(
                target_url=self.target_url,
                portfolio_id=self.portfolio_id,
                scenario_code=self.scenario_code
            )
            mock_fetch.assert_called_once_with(self.target_url, self.portfolio_id, self.scenario_code)
            self.assertEqual(res, external_metrics)


if __name__ == '__main__':
    unittest.main()