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
        self.initial_value = random.uniform(10000.0, 500000.0)
        self.volatility = random.uniform(0.1, 0.5)
        self.drift = random.uniform(-0.05, 0.05)

    def test_run_simulation_returns_correct_structure(self):
        with patch("skills.db_storage.fetch_portfolio") as mock_fetch, \
             patch("skills.market_anomaly_detector.get_current_anomaly_multiplier") as mock_anomaly, \
             patch("skills.market_portfolio_audit_compliance_hub.log_simulation") as mock_log:

            mock_fetch.return_value = {
                "portfolio_id": self.portfolio_id,
                "initial_value": self.initial_value,
                "volatility": self.volatility,
                "drift": self.drift
            }
            mock_anomaly.return_value = 1.0

            result = self.engine.run_simulation(
                portfolio_id=self.portfolio_id,
                simulations=self.simulations,
                horizon_days=self.horizon_days
            )

            self.assertIsInstance(result, dict)
            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertIn("simulation_results", result)
            self.assertIn("var_95", result)
            self.assertIn("cvar_95", result)
            self.assertEqual(len(result["simulation_results"]), self.simulations)
            self.assertGreaterEqual(result["cvar_95"], result["var_95"])
            mock_log.assert_called_once()

    def test_run_simulation_fallback_db_storage(self):
        with patch("skills.db_storage.fetch_portfolio") as mock_fetch, \
             patch("skills.market_anomaly_detector.get_current_anomaly_multiplier") as mock_anomaly:

            mock_fetch.side_effect = AttributeError("No fetch_portfolio")
            mock_anomaly.side_effect = AttributeError("No anomaly")

            result = self.engine.run_simulation(
                portfolio_id=self.portfolio_id,
                simulations=self.simulations,
                horizon_days=self.horizon_days
            )

            self.assertIsInstance(result, dict)
            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertIn("var_95", result)
            self.assertIn("cvar_95", result)

    def test_export_report_success(self):
        report_id = uuid.uuid4().hex
        loss_limit = random.uniform(5000.0, 50000.0)

        with patch("skills.market_portfolio_data_exporter.export") as mock_export:
            expected_dict = {"report_id": report_id, "loss_limit": loss_limit, "status": uuid.uuid4().hex}
            mock_export.return_value = expected_dict

            res = self.engine.export_report(report_id, loss_limit)
            self.assertEqual(res, expected_dict)
            mock_export.assert_called_once_with(report_id, loss_limit)

    def test_export_report_attribute_error_fallback(self):
        report_id = uuid.uuid4().hex
        loss_limit = random.uniform(1000.0, 10000.0)

        with patch("skills.market_portfolio_data_exporter.export", side_effect=AttributeError):
            res = self.engine.export_report(report_id, loss_limit)
            self.assertEqual(res["report_id"], report_id)
            self.assertEqual(res["loss_limit"], loss_limit)

    def test_consume_stream_success(self):
        stream_data = uuid.uuid4().hex
        with patch("skills.market_portfolio_api_gateway.stream_payload") as mock_stream:
            mock_stream.return_value = stream_data
            res = self.engine.consume_stream()
            self.assertEqual(res, stream_data)

    def test_consume_stream_fallback(self):
        with patch("skills.market_portfolio_api_gateway.stream_payload", side_effect=AttributeError):
            res = self.engine.consume_stream()
            self.assertIsNone(res)

    def test_run_monte_carlo_stress_test_function(self):
        scenario_params = {
            "volatility": self.volatility,
            "drift": self.drift,
            "horizon_days": self.horizon_days
        }
        iterations = random.randint(10, 30)

        with patch("skills.market_portfolio_audit_compliance_hub.log_simulation") as mock_log, \
             patch("skills.market_portfolio_stress_audit_visualizer.visualize_stress_test") as mock_viz:

            res = run_monte_carlo_stress_test(
                portfolio_id=self.portfolio_id,
                portfolio_value=self.initial_value,
                scenario_params=scenario_params,
                iterations=iterations
            )

            self.assertIsInstance(res, dict)
            self.assertEqual(res["portfolio_id"], self.portfolio_id)
            self.assertEqual(res["initial_value"], self.initial_value)
            self.assertEqual(res["iterations"], iterations)
            self.assertIn("simulation_id", res)
            self.assertIn("var_95", res)
            self.assertIn("expected_shortfall", res)
            self.assertGreaterEqual(res["expected_shortfall"], res["var_95"])
            mock_log.assert_called_once()
            mock_viz.assert_called_once()


if __name__ == "__main__":
    unittest.main()