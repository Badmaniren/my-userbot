import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import math
import io

from skills import market_portfolio_stress_monte_carlo_engine as engine


class TestMonteCarloStressEngine(unittest.TestCase):

    def setUp(self):
        self.engine_instance = engine.MonteCarloStressEngine()
        self.portfolio_id_val = f"port_{uuid.uuid4().hex[:8]}"
        self.simulations_count = random.randint(10, 50)
        self.horizon_val = random.randint(1, 10)
        self.initial_val = round(random.uniform(50000.0, 150000.0), 2)
        self.volatility_val = round(random.uniform(0.1, 0.4), 2)
        self.drift_val = round(random.uniform(-0.05, 0.05), 4)

    def test_run_simulation_success(self):
        portfolio_data = {
            "portfolio_id": self.portfolio_id_val,
            "initial_value": self.initial_val,
            "volatility": self.volatility_val,
            "drift": self.drift_val
        }

        with patch("skills.db_storage.fetch_portfolio", return_value=portfolio_data), \
             patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", return_value=1.0), \
             patch("skills.market_portfolio_audit_compliance_hub.log_simulation") as mock_log:

            result = self.engine_instance.run_simulation(
                portfolio_id=self.portfolio_id_val,
                simulations=self.simulations_count,
                horizon_days=self.horizon_val
            )

            self.assertIsInstance(result, dict)
            self.assertEqual(result["portfolio_id"], self.portfolio_id_val)
            self.assertIn("simulation_results", result)
            self.assertIn("var_95", result)
            self.assertIn("cvar_95", result)
            self.assertGreaterEqual(result["cvar_95"], result["var_95"])
            self.assertEqual(len(result["simulation_results"]), self.simulations_count)
            mock_log.assert_called_once()

    def test_run_simulation_fallback_db(self):
        with patch("skills.db_storage.fetch_portfolio", side_effect=AttributeError), \
             patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", side_effect=AttributeError):

            in_memory_mock = {self.portfolio_id_val: {"initial_value": self.initial_val, "volatility": self.volatility_val}}
            with patch.object(engine.db_storage, "_in_memory_db", in_memory_mock, create=True):
                result = self.engine_instance.run_simulation(
                    portfolio_id=self.portfolio_id_val,
                    simulations=self.simulations_count,
                    horizon_days=self.horizon_val
                )

                self.assertIsInstance(result, dict)
                self.assertEqual(result["portfolio_id"], self.portfolio_id_val)
                self.assertIsInstance(result["var_95"], float)
                self.assertIsInstance(result["cvar_95"], float)

    def test_export_report(self):
        report_id_val = f"rep_{uuid.uuid4().hex[:8]}"
        loss_limit_val = round(random.uniform(1000.0, 50000.0), 2)

        expected_response = {"report_id": report_id_val, "loss_limit": loss_limit_val}
        with patch("skills.market_portfolio_data_exporter.export", return_value=expected_response) as mock_export:
            res = self.engine_instance.export_report(report_id_val, loss_limit_val)
            self.assertEqual(res, expected_response)
            mock_export.assert_called_once_with(report_id_val, loss_limit_val)

    def test_export_report_exception(self):
        report_id_val = f"rep_{uuid.uuid4().hex[:8]}"
        loss_limit_val = round(random.uniform(1000.0, 50000.0), 2)

        with patch("skills.market_portfolio_data_exporter.export", side_effect=AttributeError):
            res = self.engine_instance.export_report(report_id_val, loss_limit_val)
            self.assertEqual(res["report_id"], report_id_val)
            self.assertEqual(res["loss_limit"], loss_limit_val)

    def test_consume_stream(self):
        payload_mock = f"stream_data_{uuid.uuid4().hex}"
        with patch("skills.market_portfolio_api_gateway.stream_payload", return_value=payload_mock) as mock_stream:
            res = self.engine_instance.consume_stream()
            self.assertEqual(res, payload_mock)
            mock_stream.assert_called_once()

    def test_consume_stream_exception(self):
        with patch("skills.market_portfolio_api_gateway.stream_payload", side_effect=AttributeError):
            res = self.engine_instance.consume_stream()
            self.assertIsNone(res)

    def test_run_monte_carlo_stress_test_global(self):
        scenario_params = {
            "volatility": self.volatility_val,
            "drift": self.drift_val,
            "horizon_days": self.horizon_val
        }

        with patch("skills.market_portfolio_audit_compliance_hub.log_simulation") as mock_log, \
             patch("skills.market_portfolio_stress_audit_visualizer.visualize_stress_test") as mock_viz:

            res = engine.run_monte_carlo_stress_test(
                portfolio_id=self.portfolio_id_val,
                portfolio_value=self.initial_val,
                scenario_params=scenario_params,
                iterations=self.simulations_count
            )

            self.assertIsInstance(res, dict)
            self.assertEqual(res["portfolio_id"], self.portfolio_id_val)
            self.assertEqual(res["initial_value"], self.initial_val)
            self.assertIn("simulation_id", res)
            self.assertIn("var_95", res)
            self.assertIn("expected_shortfall", res)
            self.assertGreaterEqual(res["expected_shortfall"], res["var_95"])
            mock_log.assert_called_once()
            mock_viz.assert_called_once()


if __name__ == "__main__":
    unittest.main()