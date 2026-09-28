import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import math

from skills.market_portfolio_monte_carlo_engine import MonteCarloEngine, market_portfolio_monte_carlo_engine


class TestMarketPortfolioMonteCarloEngine(unittest.TestCase):

    def test_run_simulation_success(self):
        portfolio_id = uuid.uuid4().hex
        iterations = random.randint(5, 50)
        horizon_days = random.randint(5, 20)
        initial_capital = round(random.uniform(1000.0, 50000.0), 2)

        asset_symbol = uuid.uuid4().hex
        weight = 1.0
        mean_return = round(random.uniform(0.01, 0.15), 4)
        volatility = round(random.uniform(0.1, 0.4), 4)

        input_data = {
            "portfolio_id": portfolio_id,
            "iterations": iterations,
            "horizon_days": horizon_days,
            "initial_capital": initial_capital,
            "assets": [
                {
                    "symbol": asset_symbol,
                    "weight": weight,
                    "mean_return": mean_return,
                    "volatility": volatility
                }
            ]
        }

        with patch("skills.db_storage.fetch_historical_matrix") as mock_fetch, \
             patch("skills.market_portfolio_visualizer_v2.render_distribution_curve") as mock_render:

            engine = MonteCarloEngine()
            result = engine.run_simulation(input_data)

            mock_fetch.assert_called_once_with(portfolio_id)
            mock_render.assert_called_once()

            self.assertIn("simulation_id", result)
            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertEqual(result["iterations_executed"], iterations)
            self.assertEqual(result["horizon_days"], horizon_days)
            self.assertIsInstance(result["expected_final_value"], float)
            self.assertIsInstance(result["percentile_5"], float)
            self.assertIsInstance(result["percentile_95"], float)
            self.assertGreater(result["expected_final_value"], 0.0)

    def test_calculate_value_at_risk(self):
        simulated_returns = [round(random.uniform(-0.1, 0.1), 4) for _ in range(20)]
        confidence_level = round(random.uniform(0.90, 0.99), 2)
        expected_var = round(random.uniform(0.01, 0.05), 4)

        with patch("skills.market_portfolio_performance_analytics.compute_var", return_value=expected_var) as mock_var:
            engine = MonteCarloEngine()
            var_result = engine.calculate_value_at_risk(simulated_returns, confidence_level)

            mock_var.assert_called_once_with(simulated_returns, confidence_level=confidence_level)
            self.assertEqual(var_result, expected_var)

    def test_apply_stress_test(self):
        payload_key = uuid.uuid4().hex
        payload_value = uuid.uuid4().hex
        payload = {payload_key: payload_value}
        expected_response = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch("skills.market_portfolio_stress_scenario_pipeline.execute_stress_test", return_value=expected_response) as mock_stress:
            engine = MonteCarloEngine()
            response = engine.apply_stress_test(payload)

            mock_stress.assert_called_once_with(payload)
            self.assertEqual(response, expected_response)

    def test_market_portfolio_monte_carlo_engine_wrapper(self):
        portfolio_id = uuid.uuid4().hex
        simulations = random.randint(10, 30)
        horizon_days = random.randint(5, 15)
        volatility = round(random.uniform(0.15, 0.35), 4)

        simulation_config = {
            "portfolio_id": portfolio_id,
            "simulations": simulations,
            "horizon_days": horizon_days,
            "volatility": volatility
        }

        with patch("skills.db_storage.fetch_historical_matrix") as mock_fetch, \
             patch("skills.market_portfolio_visualizer_v2.render_distribution_curve") as mock_render:

            wrapper_result = market_portfolio_monte_carlo_engine(simulation_config)

            mock_fetch.assert_called_once_with(portfolio_id)
            mock_render.assert_called_once()

            self.assertEqual(wrapper_result["portfolio_id"], portfolio_id)
            self.assertIn("results", wrapper_result)
            results = wrapper_result["results"]
            self.assertIn("simulation_id", results)
            self.assertIsInstance(results["expected_final_value"], float)
            self.assertIsInstance(results["percentile_5"], float)
            self.assertIsInstance(results["percentile_95"], float)


if __name__ == "__main__":
    unittest.main()