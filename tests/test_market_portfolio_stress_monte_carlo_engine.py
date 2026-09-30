import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import math
import io

from skills.market_portfolio_stress_monte_carlo_engine import (
    MonteCarloStressEngine,
    run_monte_carlo_stress_test
)


class TestMonteCarloStressEngine(unittest.TestCase):

    def setUp(self):
        self.engine = MonteCarloStressEngine()
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.simulations = random.randint(10, 50)
        self.horizon_days = random.randint(1, 10)
        self.initial_value = random.uniform(50000.0, 150000.0)
        self.volatility = random.uniform(0.1, 0.4)
        self.drift = random.uniform(-0.05, 0.05)

    def test_run_simulation_execution(self):
        mock_portfolio = {
            "portfolio_id": self.portfolio_id,
            "initial_value": self.initial_value,
            "volatility": self.volatility,
            "drift": self.drift
        }

        with patch("skills.db_storage.fetch_portfolio", return_value=mock_portfolio) as mock_fetch:
            result = self.engine.run_simulation(self.portfolio_id, self.simulations, self.horizon_days)

            mock_fetch.assert_called_once_with(self.portfolio_id)
            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertIn("simulation_results", result)
            self.assertIn("var_95", result)
            self.assertIn("cvar_95", result)
            self.assertEqual(len(result["simulation_results"]), self.simulations)

            for path in result["simulation_results"]:
                self.assertEqual(len(path), self.horizon_days)

    def test_get_anomaly_adjustment_with_detector(self):
        expected_multiplier = random.uniform(1.1, 2.5)
        with patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", return_value=expected_multiplier):
            mult = self.engine._get_anomaly_adjustment()
            self.assertEqual(mult, expected_multiplier)

    def test_get_anomaly_adjustment_fallback(self):
        with patch("skills.market_anomaly_detector", spec=[]):
            mult = self.engine._get_anomaly_adjustment()
            self.assertEqual(mult, 1.0)

    def test_export_report_delegation(self):
        report_id = f"rep_{uuid.uuid4().hex[:8]}"
        loss_limit = random.uniform(1000.0, 10000.0)
        expected_export_result = {"status": f"exported_{uuid.uuid4().hex[:6]}"}

        with patch("skills.market_portfolio_data_exporter.export", return_value=expected_export_result) as mock_export:
            res = self.engine.export_report(report_id, loss_limit)
            mock_export.assert_called_once_with(report_id, loss_limit)
            self.assertEqual(res, expected_export_result)

    def test_consume_stream_delegation(self):
        stream_data = f"stream_payload_{uuid.uuid4().hex[:6]}"
        with patch("skills.market_portfolio_api_gateway.stream_payload", return_value=stream_data) as mock_gateway:
            res = self.engine.consume_stream()
            mock_gateway.assert_called_once()
            self.assertEqual(res, stream_data)


class TestRunMonteCarloStressTestFunction(unittest.TestCase):

    def test_run_monte_carlo_stress_test_output(self):
        portfolio_id = f"port_func_{uuid.uuid4().hex[:8]}"
        portfolio_value = random.uniform(10000.0, 500000.0)
        iterations = random.randint(20, 100)
        scenario_params = {
            "volatility": random.uniform(0.15, 0.35),
            "drift": random.uniform(-0.02, 0.02),
            "horizon_days": random.randint(1, 5)
        }

        result = run_monte_carlo_stress_test(portfolio_id, portfolio_value, scenario_params, iterations)

        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["initial_value"], portfolio_value)
        self.assertEqual(result["iterations"], iterations)
        self.assertIn("simulation_id", result)
        self.assertTrue(result["simulation_id"].startswith("sim_"))
        self.assertIsInstance(result["var_95"], float)
        self.assertIsInstance(result["expected_shortfall"], float)


if __name__ == "__main__":
    unittest.main()