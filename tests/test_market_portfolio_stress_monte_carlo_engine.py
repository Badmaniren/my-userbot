import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import math

from skills.market_portfolio_stress_monte_carlo_engine import (
    MonteCarloStressEngine,
    run_monte_carlo_stress_test
)


class TestMonteCarloStressEngine(unittest.TestCase):

    def test_run_simulation_success(self):
        rand_portfolio_id = f"port_{uuid.uuid4().hex}"
        rand_initial_value = round(random.uniform(50000.0, 500000.0), 2)
        rand_volatility = round(random.uniform(0.1, 0.5), 2)
        rand_drift = round(random.uniform(-0.05, 0.05), 4)

        mock_portfolio = {
            "portfolio_id": rand_portfolio_id,
            "initial_value": rand_initial_value,
            "volatility": rand_volatility,
            "drift": rand_drift
        }

        with patch("skills.db_storage.fetch_portfolio", return_value=mock_portfolio, create=True) as mock_fetch, \
             patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", return_value=1.0, create=True) as mock_anomaly:

            engine = MonteCarloStressEngine()
            simulations_count = random.randint(10, 50)
            horizon = random.randint(5, 30)
            result = engine.run_simulation(rand_portfolio_id, simulations=simulations_count, horizon_days=horizon)

            mock_fetch.assert_called_once_with(rand_portfolio_id)
            self.assertEqual(result["portfolio_id"], rand_portfolio_id)
            self.assertIn("simulation_results", result)
            self.assertEqual(len(result["simulation_results"]), simulations_count)
            self.assertIn("var_95", result)
            self.assertIn("cvar_95", result)
            self.assertIsInstance(result["var_95"], float)
            self.assertIsInstance(result["cvar_95"], float)

    def test_export_report_calls_exporter(self):
        rand_report_id = f"rep_{uuid.uuid4().hex}"
        rand_loss_limit = round(random.uniform(1000.0, 50000.0), 2)
        expected_export_result = {
            "status": "success",
            "report_id": rand_report_id,
            "loss_limit": rand_loss_limit,
            "token": uuid.uuid4().hex
        }

        with patch("skills.market_portfolio_data_exporter.export", return_value=expected_export_result, create=True) as mock_export:
            engine = MonteCarloStressEngine()
            result = engine.export_report(rand_report_id, rand_loss_limit)

            mock_export.assert_called_once_with(rand_report_id, rand_loss_limit)
            self.assertEqual(result, expected_export_result)

    def test_consume_stream_calls_gateway(self):
        stream_data = {
            "stream_id": uuid.uuid4().hex,
            "payload": random.randint(100, 999),
            "status": "active"
        }

        with patch("skills.market_portfolio_api_gateway.stream_payload", return_value=stream_data, create=True) as mock_stream:
            engine = MonteCarloStressEngine()
            result = engine.consume_stream()

            mock_stream.assert_called_once()
            self.assertEqual(result, stream_data)

    def test_standalone_run_monte_carlo_stress_test(self):
        rand_portfolio_id = f"port_sa_{uuid.uuid4().hex}"
        rand_val = round(random.uniform(10000.0, 1000000.0), 2)
        rand_vol = round(random.uniform(0.1, 0.4), 2)
        rand_drift = round(random.uniform(-0.02, 0.02), 4)
        rand_horizon = random.randint(1, 10)
        rand_iterations = random.randint(20, 100)

        scenario_params = {
            "volatility": rand_vol,
            "drift": rand_drift,
            "horizon_days": rand_horizon
        }

        result = run_monte_carlo_stress_test(
            portfolio_id=rand_portfolio_id,
            portfolio_value=rand_val,
            scenario_params=scenario_params,
            iterations=rand_iterations
        )

        self.assertIn("simulation_id", result)
        self.assertTrue(result["simulation_id"].startswith("sim_"))
        self.assertEqual(result["portfolio_id"], rand_portfolio_id)
        self.assertEqual(result["initial_value"], rand_val)
        self.assertEqual(result["iterations"], rand_iterations)
        self.assertIsInstance(result["var_95"], float)
        self.assertIsInstance(result["expected_shortfall"], float)


if __name__ == "__main__":
    unittest.main()