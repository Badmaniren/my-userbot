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


class TestMonteCarloStressEngine(unittest.TestCase):

    def setUp(self):
        self.engine = MonteCarloStressEngine()
        self.portfolio_id = uuid.uuid4().hex
        self.simulations = random.randint(10, 50)
        self.horizon_days = random.randint(1, 10)
        self.initial_value = random.uniform(50000.0, 150000.0)
        self.volatility = random.uniform(0.1, 0.4)
        self.drift = random.uniform(-0.05, 0.05)

    def test_run_simulation_with_fallback_db(self):
        with patch("skills.db_storage.fetch_portfolio", side_effect=AttributeError):
            with patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", return_value=1.0):
                result = self.engine.run_simulation(
                    portfolio_id=self.portfolio_id,
                    simulations=self.simulations,
                    horizon_days=self.horizon_days
                )

        self.assertIn("portfolio_id", result)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertIn("simulation_results", result)
        self.assertEqual(len(result["simulation_results"]), self.simulations)
        self.assertIn("var_95", result)
        self.assertIn("cvar_95", result)
        self.assertIsInstance(result["var_95"], float)
        self.assertIsInstance(result["cvar_95"], float)

    def test_run_simulation_with_db_storage(self):
        mock_portfolio_data = {
            "portfolio_id": self.portfolio_id,
            "initial_value": self.initial_value,
            "volatility": self.volatility,
            "drift": self.drift
        }
        with patch("skills.db_storage.fetch_portfolio", return_value=mock_portfolio_data):
            with patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", return_value=1.2):
                result = self.engine.run_simulation(
                    portfolio_id=self.portfolio_id,
                    simulations=self.simulations,
                    horizon_days=self.horizon_days
                )

        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(len(result["simulation_results"]), self.simulations)
        for path in result["simulation_results"]:
            self.assertEqual(len(path), self.horizon_days)

    def test_export_report_fallback(self):
        report_id = uuid.uuid4().hex
        loss_limit = random.uniform(1000.0, 50000.0)

        with patch("skills.market_portfolio_data_exporter.export", side_effect=AttributeError):
            res = self.engine.export_report(report_id, loss_limit)

        self.assertEqual(res["report_id"], report_id)
        self.assertEqual(res["loss_limit"], loss_limit)

    def test_export_report_success(self):
        report_id = uuid.uuid4().hex
        loss_limit = random.uniform(1000.0, 50000.0)
        expected_dict = {"report_id": report_id, "loss_limit": loss_limit, "status": "exported"}

        with patch("skills.market_portfolio_data_exporter.export", return_value=expected_dict) as mock_export:
            res = self.engine.export_report(report_id, loss_limit)
            mock_export.assert_called_once_with(report_id, loss_limit)

        self.assertEqual(res, expected_dict)

    def test_consume_stream_fallback(self):
        with patch("skills.market_portfolio_api_gateway.stream_payload", side_effect=AttributeError):
            res = self.engine.consume_stream()

        self.assertIsNone(res)

    def test_consume_stream_success(self):
        stream_data = io.BytesIO(uuid.uuid4().bytes)
        with patch("skills.market_portfolio_api_gateway.stream_payload", return_value=stream_data):
            res = self.engine.consume_stream()

        self.assertEqual(res, stream_data)


class TestRunMonteCarloStressTestFunction(unittest.TestCase):

    def test_run_monte_carlo_stress_test(self):
        portfolio_id = uuid.uuid4().hex
        portfolio_value = random.uniform(10000.0, 500000.0)
        iterations = random.randint(20, 100)
        scenario_params = {
            "volatility": random.uniform(0.15, 0.35),
            "drift": random.uniform(-0.02, 0.02),
            "horizon_days": random.randint(1, 5)
        }

        result = run_monte_carlo_stress_test(
            portfolio_id=portfolio_id,
            portfolio_value=portfolio_value,
            scenario_params=scenario_params,
            iterations=iterations
        )

        self.assertIn("simulation_id", result)
        self.assertTrue(result["simulation_id"].startswith("sim_"))
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["initial_value"], portfolio_value)
        self.assertEqual(result["iterations"], iterations)
        self.assertIsInstance(result["var_95"], float)
        self.assertIsInstance(result["expected_shortfall"], float)


if __name__ == "__main__":
    unittest.main()