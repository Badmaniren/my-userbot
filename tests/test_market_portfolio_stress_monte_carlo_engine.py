import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
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
from skills import market_portfolio_audit_compliance_hub
from skills import market_portfolio_stress_audit_visualizer


class TestMonteCarloStressEngine(unittest.TestCase):

    def setUp(self):
        self.engine = MonteCarloStressEngine()
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.report_id = f"rep_{uuid.uuid4().hex[:8]}"
        self.simulations = random.randint(10, 50)
        self.horizon_days = random.randint(1, 10)
        self.initial_value = random.uniform(50000.0, 150000.0)
        self.volatility = random.uniform(0.1, 0.4)
        self.drift = random.uniform(-0.05, 0.05)
        self.loss_limit = random.uniform(1000.0, 10000.0)

    def test_run_simulation_success(self):
        portfolio_mock_data = {
            "portfolio_id": self.portfolio_id,
            "initial_value": self.initial_value,
            "volatility": self.volatility,
            "drift": self.drift
        }

        with patch("skills.db_storage.fetch_portfolio", return_value=portfolio_mock_data) as mock_fetch, \
             patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", return_value=1.0) as mock_anomaly, \
             patch("skills.market_portfolio_audit_compliance_hub.log_simulation") as mock_audit:
            
            result = self.engine.run_simulation(self.portfolio_id, self.simulations, self.horizon_days)

            mock_fetch.assert_called_once_with(self.portfolio_id)
            mock_anomaly.assert_called_once()
            mock_audit.assert_called_once()

            self.assertIn("portfolio_id", result)
            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertIn("simulation_results", result)
            self.assertEqual(len(result["simulation_results"]), self.simulations)
            self.assertIn("var_95", result)
            self.assertIn("cvar_95", result)
            self.assertIsInstance(result["var_95"], float)
            self.assertIsInstance(result["cvar_95"], float)

    def test_run_simulation_attribute_error_fallback(self):
        with patch("skills.db_storage.fetch_portfolio", side_effect=AttributeError), \
             patch.object(db_storage, "_in_memory_db", {self.portfolio_id: {"initial_value": self.initial_value}}, create=True):
            
            result = self.engine.run_simulation(self.portfolio_id, self.simulations, self.horizon_days)
            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertEqual(len(result["simulation_results"]), self.simulations)

    def test_get_anomaly_adjustment_exception(self):
        with patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", side_effect=AttributeError):
            mult = self.engine._get_anomaly_adjustment()
            self.assertEqual(mult, 1.0)

    def test_export_report_success(self):
        expected_output = {"report_id": self.report_id, "loss_limit": self.loss_limit, "status": f"ok_{uuid.uuid4().hex[:4]}"}
        with patch("skills.market_portfolio_data_exporter.export", return_value=expected_output) as mock_export:
            res = self.engine.export_report(self.report_id, self.loss_limit)
            mock_export.assert_called_once_with(self.report_id, self.loss_limit)
            self.assertEqual(res, expected_output)

    def test_export_report_attribute_error(self):
        with patch("skills.market_portfolio_data_exporter.export", side_effect=AttributeError):
            res = self.engine.export_report(self.report_id, self.loss_limit)
            self.assertEqual(res["report_id"], self.report_id)
            self.assertEqual(res["loss_limit"], self.loss_limit)

    def test_consume_stream_success(self):
        stream_data = io.BytesIO(uuid.uuid4().bytes)
        with patch("skills.market_portfolio_api_gateway.stream_payload", return_value=stream_data) as mock_stream:
            res = self.engine.consume_stream()
            mock_stream.assert_called_once()
            self.assertEqual(res, stream_data)

    def test_consume_stream_attribute_error(self):
        with patch("skills.market_portfolio_api_gateway.stream_payload", side_effect=AttributeError):
            res = self.engine.consume_stream()
            self.assertIsNone(res)

    def test_run_monte_carlo_stress_test_functional(self):
        scenario_params = {
            "volatility": self.volatility,
            "drift": self.drift,
            "horizon_days": self.horizon_days
        }

        with patch("skills.market_portfolio_audit_compliance_hub.log_simulation") as mock_log, \
             patch("skills.market_portfolio_stress_audit_visualizer.visualize_stress_test") as mock_viz:
            
            result = run_monte_carlo_stress_test(
                portfolio_id=self.portfolio_id,
                portfolio_value=self.initial_value,
                scenario_params=scenario_params,
                iterations=self.simulations
            )

            mock_log.assert_called_once()
            mock_viz.assert_called_once()

            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertEqual(result["initial_value"], self.initial_value)
            self.assertEqual(result["iterations"], self.simulations)
            self.assertIn("simulation_id", result)
            self.assertIn("var_95", result)
            self.assertIn("expected_shortfall", result)
            self.assertTrue(result["simulation_id"].startswith("sim_"))


if __name__ == "__main__":
    unittest.main()