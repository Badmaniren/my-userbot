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
        self.simulations = random.randint(50, 200)
        self.horizon_days = random.randint(5, 30)
        self.initial_value = round(random.uniform(50000.0, 500000.0), 2)
        self.volatility = round(random.uniform(0.1, 0.5), 4)
        self.drift = round(random.uniform(-0.05, 0.05), 4)

    def test_run_simulation_success_path(self):
        mock_portfolio_data = {
            "portfolio_id": self.portfolio_id,
            "initial_value": self.initial_value,
            "volatility": self.volatility,
            "drift": self.drift
        }

        with patch("skills.db_storage.fetch_portfolio", return_value=mock_portfolio_data) as mock_fetch, \
             patch("skills.market_portfolio_audit_compliance_hub.log_simulation") as mock_audit:

            result = self.engine.run_simulation(
                portfolio_id=self.portfolio_id,
                simulations=self.simulations,
                horizon_days=self.horizon_days
            )

            mock_fetch.assert_called_once_with(self.portfolio_id)
            mock_audit.assert_called_once()

            self.assertIn("portfolio_id", result)
            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertIn("simulation_results", result)
            self.assertEqual(len(result["simulation_results"]), self.simulations)
            self.assertIn("var_95", result)
            self.assertIn("cvar_95", result)
            self.assertGreaterEqual(result["cvar_95"], result["var_95"])

    def test_run_simulation_attribute_error_fallback(self):
        with patch("skills.db_storage.fetch_portfolio", side_effect=AttributeError), \
             patch("skills.db_storage._in_memory_db", {self.portfolio_id: {
                 "portfolio_id": self.portfolio_id,
                 "initial_value": self.initial_value,
                 "volatility": self.volatility,
                 "drift": self.drift
             }}):

            result = self.engine.run_simulation(
                portfolio_id=self.portfolio_id,
                simulations=self.simulations,
                horizon_days=self.horizon_days
            )

            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertIsInstance(result["var_95"], float)
            self.assertIsInstance(result["cvar_95"], float)

    def test_get_anomaly_adjustment_with_value(self):
        expected_mult = round(random.uniform(1.1, 2.5), 2)
        with patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", return_value=expected_mult):
            mult = self.engine._get_anomaly_adjustment()
            self.assertEqual(mult, expected_mult)

    def test_get_anomaly_adjustment_attribute_error_fallback(self):
        with patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", side_effect=AttributeError):
            mult = self.engine._get_anomaly_adjustment()
            self.assertEqual(mult, 1.0)

    def test_export_report_success(self):
        report_id = f"rep_{uuid.uuid4().hex[:8]}"
        loss_limit = round(random.uniform(1000.0, 50000.0), 2)
        expected_response = {"report_id": report_id, "loss_limit": loss_limit, "status": f"exported_{uuid.uuid4().hex[:4]}"}

        with patch("skills.market_portfolio_data_exporter.export", return_value=expected_response) as mock_export:
            res = self.engine.export_report(report_id, loss_limit)
            mock_export.assert_called_once_with(report_id, loss_limit)
            self.assertEqual(res, expected_response)

    def test_export_report_fallback(self):
        report_id = f"rep_{uuid.uuid4().hex[:8]}"
        loss_limit = round(random.uniform(1000.0, 50000.0), 2)

        with patch("skills.market_portfolio_data_exporter.export", side_effect=AttributeError):
            res = self.engine.export_report(report_id, loss_limit)
            self.assertEqual(res["report_id"], report_id)
            self.assertEqual(res["loss_limit"], loss_limit)

    def test_consume_stream_success(self):
        stream_data = f"stream_payload_{uuid.uuid4().hex[:8]}"
        with patch("skills.market_portfolio_api_gateway.stream_payload", return_value=stream_data) as mock_stream:
            res = self.engine.consume_stream()
            mock_stream.assert_called_once()
            self.assertEqual(res, stream_data)

    def test_consume_stream_fallback(self):
        with patch("skills.market_portfolio_api_gateway.stream_payload", side_effect=AttributeError):
            res = self.engine.consume_stream()
            self.assertIsNone(res)

    def test_run_monte_carlo_stress_test_standalone(self):
        scenario_params = {
            "volatility": self.volatility,
            "drift": self.drift,
            "horizon_days": self.horizon_days
        }
        iterations = random.randint(20, 100)

        with patch("skills.market_portfolio_audit_compliance_hub.log_simulation") as mock_audit, \
             patch("skills.market_portfolio_stress_audit_visualizer.visualize_stress_test") as mock_visualize:

            res = run_monte_carlo_stress_test(
                portfolio_id=self.portfolio_id,
                portfolio_value=self.initial_value,
                scenario_params=scenario_params,
                iterations=iterations
            )

            mock_audit.assert_called_once()
            mock_visualize.assert_called_once()

            self.assertEqual(res["portfolio_id"], self.portfolio_id)
            self.assertEqual(res["initial_value"], self.initial_value)
            self.assertEqual(res["iterations"], iterations)
            self.assertIn("simulation_id", res)
            self.assertIn("var_95", res)
            self.assertIn("expected_shortfall", res)
            self.assertGreaterEqual(res["expected_shortfall"], res["var_95"])


if __name__ == "__main__":
    unittest.main()