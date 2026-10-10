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

    def test_run_simulation_success(self):
        portfolio_id = f"port_{uuid.uuid4().hex}"
        simulations = random.randint(10, 50)
        horizon_days = random.randint(1, 5)

        mock_portfolio_data = {
            "portfolio_id": portfolio_id,
            "initial_value": float(random.randint(50000, 150000)),
            "volatility": float(random.uniform(0.1, 0.3)),
            "drift": float(random.uniform(-0.05, 0.05))
        }

        with patch("skills.db_storage.fetch_portfolio", return_value=mock_portfolio_data) as mock_fetch, \
             patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", return_value=1.0) as mock_anomaly, \
             patch("skills.market_portfolio_audit_compliance_hub.log_simulation") as mock_audit:

            engine = MonteCarloStressEngine()
            result = engine.run_simulation(portfolio_id, simulations, horizon_days)

            self.assertIsInstance(result, dict)
            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertIn("simulation_results", result)
            self.assertIn("var_95", result)
            self.assertIn("cvar_95", result)
            self.assertEqual(len(result["simulation_results"]), simulations)
            self.assertGreaterEqual(result["cvar_95"], result["var_95"])

            mock_fetch.assert_called_once_with(portfolio_id)
            mock_anomaly.assert_called_once()
            mock_audit.assert_called_once()

    def test_run_simulation_attribute_error_fallback(self):
        portfolio_id = f"port_{uuid.uuid4().hex}"
        simulations = random.randint(10, 30)
        horizon_days = random.randint(1, 3)

        with patch("skills.db_storage.fetch_portfolio", side_effect=AttributeError), \
             patch("skills.db_storage._in_memory_db", {portfolio_id: {"initial_value": 200000.0, "volatility": 0.25}}), \
             patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", side_effect=AttributeError):

            engine = MonteCarloStressEngine()
            result = engine.run_simulation(portfolio_id, simulations, horizon_days)

            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertIsInstance(result["var_95"], float)
            self.assertIsInstance(result["cvar_95"], float)

    def test_export_report_success(self):
        report_id = f"rep_{uuid.uuid4().hex}"
        loss_limit = float(random.randint(1000, 10000))

        expected_response = {"report_id": report_id, "loss_limit": loss_limit, "status": f"status_{uuid.uuid4().hex}"}

        with patch("skills.market_portfolio_data_exporter.export", return_value=expected_response) as mock_export:
            engine = MonteCarloStressEngine()
            res = engine.export_report(report_id, loss_limit)
            self.assertEqual(res, expected_response)
            mock_export.assert_called_once_with(report_id, loss_limit)

    def test_export_report_attribute_error(self):
        report_id = f"rep_{uuid.uuid4().hex}"
        loss_limit = float(random.randint(500, 5000))

        with patch("skills.market_portfolio_data_exporter.export", side_effect=AttributeError):
            engine = MonteCarloStressEngine()
            res = engine.export_report(report_id, loss_limit)
            self.assertEqual(res["report_id"], report_id)
            self.assertEqual(res["loss_limit"], loss_limit)

    def test_consume_stream_success(self):
        stream_data = f"stream_{uuid.uuid4().hex}"

        with patch("skills.market_portfolio_api_gateway.stream_payload", return_value=stream_data) as mock_stream:
            engine = MonteCarloStressEngine()
            res = engine.consume_stream()
            self.assertEqual(res, stream_data)
            mock_stream.assert_called_once()

    def test_consume_stream_attribute_error(self):
        with patch("skills.market_portfolio_api_gateway.stream_payload", side_effect=AttributeError):
            engine = MonteCarloStressEngine()
            res = engine.consume_stream()
            self.assertIsNone(res)

    def test_run_monte_carlo_stress_test_functional(self):
        portfolio_id = f"pid_{uuid.uuid4().hex}"
        portfolio_value = float(random.randint(10000, 500000))
        iterations = random.randint(20, 100)
        scenario_params = {
            "volatility": float(random.uniform(0.1, 0.4)),
            "drift": float(random.uniform(-0.1, 0.1)),
            "horizon_days": random.randint(1, 10)
        }

        with patch("skills.market_portfolio_audit_compliance_hub.log_simulation") as mock_log, \
             patch("skills.market_portfolio_stress_audit_visualizer.visualize_stress_test") as mock_vis:

            res = run_monte_carlo_stress_test(portfolio_id, portfolio_value, scenario_params, iterations)

            self.assertEqual(res["portfolio_id"], portfolio_id)
            self.assertEqual(res["initial_value"], portfolio_value)
            self.assertEqual(res["iterations"], iterations)
            self.assertIn("simulation_id", res)
            self.assertIn("var_95", res)
            self.assertIn("expected_shortfall", res)
            self.assertGreaterEqual(res["expected_shortfall"], res["var_95"])

            mock_log.assert_called_once()
            mock_vis.assert_called_once()


if __name__ == "__main__":
    unittest.main()