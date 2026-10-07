import unittest
from unittest.mock import patch
import uuid
import random
import io
import math

from skills.market_portfolio_stress_monte_carlo_engine import (
    MonteCarloStressEngine,
    run_monte_carlo_stress_test
)


class TestMonteCarloStressEngine(unittest.TestCase):

    def setUp(self):
        self.engine = MonteCarloStressEngine()
        self.portfolio_id_val = f"port_{uuid.uuid4().hex[:8]}"
        self.simulations_count = random.randint(10, 50)
        self.horizon_val = random.randint(1, 10)
        self.initial_val = round(random.uniform(50000.0, 500000.0), 2)
        self.volatility_val = round(random.uniform(0.1, 0.5), 4)
        self.drift_val = round(random.uniform(-0.05, 0.05), 4)

    def test_run_simulation_success(self):
        with patch("skills.db_storage.fetch_portfolio") as mock_fetch, \
             patch("skills.market_portfolio_audit_compliance_hub.log_simulation") as mock_log:
            
            mock_fetch.return_value = {
                "portfolio_id": self.portfolio_id_val,
                "initial_value": self.initial_val,
                "volatility": self.volatility_val,
                "drift": self.drift_val
            }

            result = self.engine.run_simulation(
                portfolio_id=self.portfolio_id_val,
                simulations=self.simulations_count,
                horizon_days=self.horizon_val
            )

            self.assertIsInstance(result, dict)
            self.assertEqual(result["portfolio_id"], self.portfolio_id_val)
            self.assertIn("simulation_results", result)
            self.assertEqual(len(result["simulation_results"]), self.simulations_count)
            self.assertIsInstance(result["var_95"], float)
            self.assertIsInstance(result["cvar_95"], float)
            mock_log.assert_called_once()

    def test_run_simulation_fallback_db(self):
        with patch("skills.db_storage.fetch_portfolio", side_effect=AttributeError), \
             patch("skills.db_storage._in_memory_db", {self.portfolio_id_val: {
                 "portfolio_id": self.portfolio_id_val,
                 "initial_value": self.initial_val,
                 "volatility": self.volatility_val,
                 "drift": self.drift_val
             }}):

            result = self.engine.run_simulation(
                portfolio_id=self.portfolio_id_val,
                simulations=self.simulations_count,
                horizon_days=self.horizon_val
            )

            self.assertIsInstance(result, dict)
            self.assertEqual(result["portfolio_id"], self.portfolio_id_val)
            self.assertEqual(len(result["simulation_results"]), self.simulations_count)

    def test_get_anomaly_adjustment_success(self):
        expected_mult = round(random.uniform(1.0, 3.0), 2)
        with patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", return_value=expected_mult):
            mult = self.engine._get_anomaly_adjustment()
            self.assertEqual(mult, expected_mult)

    def test_get_anomaly_adjustment_fallback(self):
        with patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", side_effect=AttributeError):
            mult = self.engine._get_anomaly_adjustment()
            self.assertEqual(mult, 1.0)

    def test_export_report_success(self):
        report_id_val = f"rep_{uuid.uuid4().hex[:6]}"
        loss_limit_val = round(random.uniform(1000.0, 10000.0), 2)
        expected_ret = {"report_id": report_id_val, "loss_limit": loss_limit_val, "status": f"exported_{uuid.uuid4().hex[:4]}"}

        with patch("skills.market_portfolio_data_exporter.export", return_value=expected_ret):
            res = self.engine.export_report(report_id_val, loss_limit_val)
            self.assertEqual(res, expected_ret)

    def test_export_report_fallback(self):
        report_id_val = f"rep_{uuid.uuid4().hex[:6]}"
        loss_limit_val = round(random.uniform(1000.0, 10000.0), 2)

        with patch("skills.market_portfolio_data_exporter.export", side_effect=AttributeError):
            res = self.engine.export_report(report_id_val, loss_limit_val)
            self.assertEqual(res["report_id"], report_id_val)
            self.assertEqual(res["loss_limit"], loss_limit_val)

    def test_consume_stream_success(self):
        stream_data = f"stream_payload_{uuid.uuid4().hex}".encode('utf-8')
        mock_stream = io.BytesIO(stream_data)

        with patch("skills.market_portfolio_api_gateway.stream_payload", return_value=mock_stream):
            stream = self.engine.consume_stream()
            self.assertEqual(stream.read(), stream_data)

    def test_consume_stream_fallback(self):
        with patch("skills.market_portfolio_api_gateway.stream_payload", side_effect=AttributeError):
            res = self.engine.consume_stream()
            self.assertIsNone(res)

    def test_run_monte_carlo_stress_test_standalone(self):
        scenario_params = {
            "volatility": self.volatility_val,
            "drift": self.drift_val,
            "horizon_days": self.horizon_val
        }

        with patch("skills.market_portfolio_audit_compliance_hub.log_simulation") as mock_log, \
             patch("skills.market_portfolio_stress_audit_visualizer.visualize_stress_test") as mock_vis:

            res = run_monte_carlo_stress_test(
                portfolio_id=self.portfolio_id_val,
                portfolio_value=self.initial_val,
                scenario_params=scenario_params,
                iterations=self.simulations_count
            )

            self.assertIsInstance(res, dict)
            self.assertEqual(res["portfolio_id"], self.portfolio_id_val)
            self.assertEqual(res["initial_value"], self.initial_val)
            self.assertEqual(res["iterations"], self.simulations_count)
            self.assertIn("simulation_id", res)
            self.assertIn("var_95", res)
            self.assertIn("expected_shortfall", res)
            mock_log.assert_called_once()
            mock_vis.assert_called_once()


if __name__ == "__main__":
    unittest.main()