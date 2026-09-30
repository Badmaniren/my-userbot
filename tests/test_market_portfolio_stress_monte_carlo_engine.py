import unittest
from unittest.mock import patch
import uuid
import random
import math
import io

from skills.market_portfolio_stress_monte_carlo_engine import (
    MonteCarloStressEngine,
    run_monte_carlo_stress_test
)
from skills import db_storage
from skills import market_anomaly_detector
from skills import market_portfolio_data_exporter
from skills import market_portfolio_api_gateway


class TestMonteCarloStressEngine(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.simulation_id = f"sim_{uuid.uuid4().hex[:8]}"
        self.initial_value = round(random.uniform(50000.0, 500000.0), 2)
        self.volatility = round(random.uniform(0.1, 0.5), 4)
        self.drift = round(random.uniform(-0.05, 0.05), 4)
        self.simulations = random.randint(10, 50)
        self.horizon_days = random.randint(1, 10)
        self.engine = MonteCarloStressEngine()

    def test_run_simulation_success(self):
        mock_portfolio = {
            "portfolio_id": self.portfolio_id,
            "initial_value": self.initial_value,
            "volatility": self.volatility,
            "drift": self.drift
        }

        with patch("skills.db_storage.fetch_portfolio", return_value=mock_portfolio) as mock_fetch, \
             patch.object(self.engine, "_get_anomaly_adjustment", return_value=1.0):

            result = self.engine.run_simulation(
                portfolio_id=self.portfolio_id,
                simulations=self.simulations,
                horizon_days=self.horizon_days
            )

            mock_fetch.assert_called_once_with(self.portfolio_id)

            self.assertIn("portfolio_id", result)
            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertIn("simulation_results", result)
            self.assertEqual(len(result["simulation_results"]), self.simulations)
            self.assertIn("var_95", result)
            self.assertIn("cvar_95", result)
            self.assertIsInstance(result["var_95"], float)
            self.assertIsInstance(result["cvar_95"], float)

    def test_get_anomaly_adjustment_with_detector(self):
        random_multiplier = round(random.uniform(1.1, 3.0), 2)
        with patch.object(market_anomaly_detector, "get_current_anomaly_multiplier", return_value=random_multiplier, create=True):
            mult = self.engine._get_anomaly_adjustment()
            self.assertEqual(mult, random_multiplier)

    def test_get_anomaly_adjustment_without_detector(self):
        if hasattr(market_anomaly_detector, "get_current_anomaly_multiplier"):
            delattr(market_anomaly_detector, "get_current_anomaly_multiplier")
        mult = self.engine._get_anomaly_adjustment()
        self.assertEqual(mult, 1.0)

    def test_export_report_calls_exporter(self):
        report_id = f"rep_{uuid.uuid4().hex[:8]}"
        loss_limit = round(random.uniform(1000.0, 10000.0), 2)
        expected_export_result = {"report_id": report_id, "status": uuid.uuid4().hex}

        with patch("skills.market_portfolio_data_exporter.export", return_value=expected_export_result) as mock_export:
            res = self.engine.export_report(report_id, loss_limit)
            mock_export.assert_called_once_with(report_id, loss_limit)
            self.assertEqual(res, expected_export_result)

    def test_consume_stream_calls_gateway(self):
        stream_data = io.BytesIO(uuid.uuid4().bytes)
        with patch("skills.market_portfolio_api_gateway.stream_payload", return_value=stream_data) as mock_stream:
            res = self.engine.consume_stream()
            mock_stream.assert_called_once()
            self.assertEqual(res, stream_data)

    def test_run_monte_carlo_stress_test_function(self):
        scenario_params = {
            "volatility": self.volatility,
            "drift": self.drift,
            "horizon_days": self.horizon_days
        }
        iterations = random.randint(15, 45)

        result = run_monte_carlo_stress_test(
            portfolio_id=self.portfolio_id,
            portfolio_value=self.initial_value,
            scenario_params=scenario_params,
            iterations=iterations
        )

        self.assertIn("simulation_id", result)
        self.assertTrue(result["simulation_id"].startswith("sim_"))
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["initial_value"], self.initial_value)
        self.assertEqual(result["iterations"], iterations)
        self.assertIsInstance(result["var_95"], float)
        self.assertIsInstance(result["expected_shortfall"], float)


if __name__ == "__main__":
    unittest.main()