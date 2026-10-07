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
        self.report_id = f"rep_{uuid.uuid4().hex[:8]}"
        self.simulations = random.randint(10, 50)
        self.horizon_days = random.randint(1, 10)
        self.initial_value = float(random.randint(50000, 200000))
        self.volatility = float(random.uniform(0.1, 0.5))
        self.drift = float(random.uniform(-0.05, 0.05))
        self.loss_limit = float(random.randint(1000, 10000))

    def test_run_simulation_with_explicit_fetch(self):
        mock_portfolio_data = {
            "portfolio_id": self.portfolio_id,
            "initial_value": self.initial_value,
            "volatility": self.volatility,
            "drift": self.drift
        }

        with patch("skills.db_storage.fetch_portfolio", return_value=mock_portfolio_data) as mock_fetch, \
             patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", return_value=1.0) as mock_anomaly, \
             patch("skills.market_portfolio_audit_compliance_hub.log_simulation") as mock_audit:

            result = self.engine.run_simulation(self.portfolio_id, self.simulations, self.horizon_days)

            mock_fetch.assert_called_once_with(self.portfolio_id)
            mock_anomaly.assert_called_once()
            mock_audit.assert_called_once()

            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertIn("simulation_results", result)
            self.assertIn("var_95", result)
            self.assertIn("cvar_95", result)
            self.assertEqual(len(result["simulation_results"]), self.simulations)

    def test_run_simulation_fallback_in_memory_db(self):
        with patch("skills.db_storage.fetch_portfolio", side_effect=AttributeError("No fetch_portfolio")):
            with patch.object(self.engine, "_get_anomaly_adjustment", return_value=1.0):
                with patch("skills.market_portfolio_audit_compliance_hub.log_simulation") as mock_audit:
                    result = self.engine.run_simulation(self.portfolio_id, self.simulations, self.horizon_days)

                    mock_audit.assert_called_once()
                    self.assertEqual(result["portfolio_id"], self.portfolio_id)
                    self.assertEqual(len(result["simulation_results"]), self.simulations)
                    self.assertIsInstance(result["var_95"], float)
                    self.assertIsInstance(result["cvar_95"], float)

    def test_get_anomaly_adjustment_success(self):
        expected_mult = float(random.uniform(0.5, 2.5))
        with patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", return_value=expected_mult) as mock_det:
            mult = self.engine._get_anomaly_adjustment()
            mock_det.assert_called_once()
            self.assertEqual(mult, expected_mult)

    def test_get_anomaly_adjustment_fallback(self):
        with patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", side_effect=AttributeError):
            mult = self.engine._get_anomaly_adjustment()
            self.assertEqual(mult, 1.0)

    def test_export_report_success(self):
        expected_export = {
            "report_id": self.report_id,
            "loss_limit": self.loss_limit,
            "status": f"status_{uuid.uuid4().hex[:6]}"
        }
        with patch("skills.market_portfolio_data_exporter.export", return_value=expected_export) as mock_exp:
            res = self.engine.export_report(self.report_id, self.loss_limit)
            mock_exp.assert_called_once_with(self.report_id, self.loss_limit)
            self.assertEqual(res, expected_export)

    def test_export_report_fallback(self):
        with patch("skills.market_portfolio_data_exporter.export", side_effect=AttributeError):
            res = self.engine.export_report(self.report_id, self.loss_limit)
            self.assertEqual(res["report_id"], self.report_id)
            self.assertEqual(res["loss_limit"], self.loss_limit)

    def test_consume_stream_success(self):
        stream_payload_data = f"stream_data_{uuid.uuid4().hex}".encode('utf-8')
        mock_stream = io.BytesIO(stream_payload_data)
        with patch("skills.market_portfolio_api_gateway.stream_payload", return_value=mock_stream) as mock_gateway:
            res = self.engine.consume_stream()
            mock_gateway.assert_called_once()
            self.assertEqual(res.read(), stream_payload_data)

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

        with patch("skills.market_portfolio_audit_compliance_hub.log_simulation") as mock_audit, \
             patch("skills.market_portfolio_stress_audit_visualizer.visualize_stress_test") as mock_vis:

            res = run_monte_carlo_stress_test(
                portfolio_id=self.portfolio_id,
                portfolio_value=self.initial_value,
                scenario_params=scenario_params,
                iterations=iterations
            )

            mock_audit.assert_called_once()
            mock_vis.assert_called_once()

            self.assertEqual(res["portfolio_id"], self.portfolio_id)
            self.assertEqual(res["initial_value"], self.initial_value)
            self.assertEqual(res["iterations"], iterations)
            self.assertIn("simulation_id", res)
            self.assertIn("var_95", res)
            self.assertIn("expected_shortfall", res)


if __name__ == "__main__":
    unittest.main()