import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import math

from skills.market_portfolio_stress_monte_carlo_engine import (
    MonteCarloStressEngine,
    run_monte_carlo_stress_test
)


class TestMonteCarloStressEngine(unittest.TestCase):

    def setUp(self):
        self.engine = MonteCarloStressEngine()
        self.portfolio_id = uuid.uuid4().hex
        self.simulations = random.randint(10, 50)
        self.horizon_days = random.randint(5, 30)
        self.initial_value = float(random.randint(50000, 200000))
        self.volatility = float(random.uniform(0.1, 0.5))
        self.drift = float(random.uniform(-0.05, 0.05))

    def test_run_simulation_success(self):
        mock_portfolio_data = {
            "portfolio_id": self.portfolio_id,
            "initial_value": self.initial_value,
            "volatility": self.volatility,
            "drift": self.drift
        }

        with patch("skills.db_storage.fetch_portfolio", return_value=mock_portfolio_data) as mock_fetch, \
             patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", return_value=1.0) as mock_anomaly, \
             patch("skills.market_portfolio_audit_compliance_hub.log_simulation") as mock_audit:

            result = self.engine.run_simulation(
                portfolio_id=self.portfolio_id,
                simulations=self.simulations,
                horizon_days=self.horizon_days
            )

            mock_fetch.assert_called_once_with(self.portfolio_id)
            mock_anomaly.assert_called_once()
            mock_audit.assert_called_once()

            self.assertIsInstance(result, dict)
            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertIn("simulation_results", result)
            self.assertIn("var_95", result)
            self.assertIn("cvar_95", result)
            self.assertGreaterEqual(result["cvar_95"], result["var_95"])
            self.assertEqual(len(result["simulation_results"]), self.simulations)

    def test_run_simulation_missing_fetch_attribute(self):
        with patch("skills.db_storage.fetch_portfolio", side_effect=AttributeError), \
             patch("skills.db_storage._in_memory_db", {self.portfolio_id: {"initial_value": self.initial_value}}):

            result = self.engine.run_simulation(
                portfolio_id=self.portfolio_id,
                simulations=self.simulations,
                horizon_days=self.horizon_days
            )

            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertIsInstance(result["var_95"], float)
            self.assertIsInstance(result["cvar_95"], float)

    def test_get_anomaly_adjustment_fallback(self):
        with patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", side_effect=AttributeError):
            mult = self.engine._get_anomaly_adjustment()
            self.assertEqual(mult, 1.0)

    def test_export_report(self):
        report_id = uuid.uuid4().hex
        loss_limit = float(random.randint(1000, 50000))

        with patch("skills.market_portfolio_data_exporter.export", return_value={"report_id": report_id, "loss_limit": loss_limit}) as mock_export:
            res = self.engine.export_report(report_id, loss_limit)
            mock_export.assert_called_once_with(report_id, loss_limit)
            self.assertEqual(res["report_id"], report_id)
            self.assertEqual(res["loss_limit"], loss_limit)

    def test_export_report_fallback(self):
        report_id = uuid.uuid4().hex
        loss_limit = float(random.randint(1000, 50000))

        with patch("skills.market_portfolio_data_exporter.export", side_effect=AttributeError):
            res = self.engine.export_report(report_id, loss_limit)
            self.assertEqual(res["report_id"], report_id)
            self.assertEqual(res["loss_limit"], loss_limit)

    def test_consume_stream(self):
        expected_payload = {"stream_id": uuid.uuid4().hex}
        with patch("skills.market_portfolio_api_gateway.stream_payload", return_value=expected_payload) as mock_stream:
            res = self.engine.consume_stream()
            mock_stream.assert_called_once()
            self.assertEqual(res, expected_payload)

    def test_consume_stream_fallback(self):
        with patch("skills.market_portfolio_api_gateway.stream_payload", side_effect=AttributeError):
            res = self.engine.consume_stream()
            self.assertIsNone(res)

    def test_run_monte_carlo_stress_test_function(self):
        scenario_params = {
            "volatility": float(random.uniform(0.1, 0.4)),
            "drift": float(random.uniform(-0.02, 0.02)),
            "horizon_days": int(random.randint(1, 10))
        }
        iterations = int(random.randint(20, 60))

        with patch("skills.market_portfolio_audit_compliance_hub.log_simulation") as mock_log, \
             patch("skills.market_portfolio_stress_audit_visualizer.visualize_stress_test") as mock_vis:

            res = run_monte_carlo_stress_test(
                portfolio_id=self.portfolio_id,
                portfolio_value=self.initial_value,
                scenario_params=scenario_params,
                iterations=iterations
            )

            mock_log.assert_called_once()
            mock_vis.assert_called_once()

            self.assertEqual(res["portfolio_id"], self.portfolio_id)
            self.assertEqual(res["initial_value"], self.initial_value)
            self.assertEqual(res["iterations"], iterations)
            self.assertIn("simulation_id", res)
            self.assertGreaterEqual(res["expected_shortfall"], res["var_95"])


if __name__ == "__main__":
    unittest.main()