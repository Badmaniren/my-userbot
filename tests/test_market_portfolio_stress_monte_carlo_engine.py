import unittest
from unittest.mock import patch
import uuid
import random

from skills.market_portfolio_stress_monte_carlo_engine import (
    MonteCarloStressEngine,
    run_monte_carlo_stress_test
)


class TestMonteCarloStressEngine(unittest.TestCase):

    def test_run_simulation_success(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        simulations = random.randint(10, 50)
        horizon_days = random.randint(1, 5)
        
        mock_portfolio = {
            "portfolio_id": portfolio_id,
            "initial_value": round(random.uniform(50000.0, 150000.0), 2),
            "volatility": round(random.uniform(0.1, 0.4), 2),
            "drift": round(random.uniform(-0.05, 0.05), 2)
        }

        with patch("skills.db_storage.fetch_portfolio", return_value=mock_portfolio) as mock_fetch, \
             patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", return_value=1.0) as mock_anomaly, \
             patch("skills.market_portfolio_audit_compliance_hub.log_simulation") as mock_audit:

            engine = MonteCarloStressEngine()
            result = engine.run_simulation(portfolio_id, simulations, horizon_days)

            mock_fetch.assert_called_once_with(portfolio_id)
            mock_anomaly.assert_called_once()
            mock_audit.assert_called_once()

            self.assertIn("portfolio_id", result)
            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertIn("simulation_results", result)
            self.assertEqual(len(result["simulation_results"]), simulations)
            self.assertIn("var_95", result)
            self.assertIn("cvar_95", result)
            self.assertIsInstance(result["var_95"], float)
            self.assertIsInstance(result["cvar_95"], float)

    def test_run_simulation_fallback_db(self):
        portfolio_id = f"port_fb_{uuid.uuid4().hex[:8]}"
        simulations = 10
        horizon_days = 2

        with patch("skills.db_storage.fetch_portfolio", side_effect=AttributeError), \
             patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", side_effect=AttributeError), \
             patch("skills.market_portfolio_audit_compliance_hub.log_simulation") as mock_audit:

            engine = MonteCarloStressEngine()
            result = engine.run_simulation(portfolio_id, simulations, horizon_days)

            mock_audit.assert_called_once()
            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertEqual(len(result["simulation_results"]), simulations)

    def test_export_report(self):
        report_id = f"rep_{uuid.uuid4().hex[:8]}"
        loss_limit = round(random.uniform(1000.0, 10000.0), 2)
        expected_dict = {"report_id": report_id, "loss_limit": loss_limit, "status": "exported"}

        with patch("skills.market_portfolio_data_exporter.export", return_value=expected_dict) as mock_export:
            engine = MonteCarloStressEngine()
            res = engine.export_report(report_id, loss_limit)

            mock_export.assert_called_once_with(report_id, loss_limit)
            self.assertEqual(res, expected_dict)

    def test_export_report_fallback(self):
        report_id = f"rep_fb_{uuid.uuid4().hex[:8]}"
        loss_limit = round(random.uniform(500.0, 5000.0), 2)

        with patch("skills.market_portfolio_data_exporter.export", side_effect=AttributeError):
            engine = MonteCarloStressEngine()
            res = engine.export_report(report_id, loss_limit)

            self.assertEqual(res["report_id"], report_id)
            self.assertEqual(res["loss_limit"], loss_limit)

    def test_consume_stream(self):
        payload_data = {"stream_id": uuid.uuid4().hex, "data": random.randint(1, 100)}

        with patch("skills.market_portfolio_api_gateway.stream_payload", return_value=payload_data) as mock_stream:
            engine = MonteCarloStressEngine()
            res = engine.consume_stream()

            mock_stream.assert_called_once()
            self.assertEqual(res, payload_data)

    def test_consume_stream_fallback(self):
        with patch("skills.market_portfolio_api_gateway.stream_payload", side_effect=AttributeError):
            engine = MonteCarloStressEngine()
            res = engine.consume_stream()

            self.assertIsNone(res)

    def test_run_monte_carlo_stress_test(self):
        portfolio_id = f"p_stress_{uuid.uuid4().hex[:8]}"
        portfolio_value = round(random.uniform(10000.0, 500000.0), 2)
        iterations = random.randint(15, 30)
        scenario_params = {
            "volatility": round(random.uniform(0.15, 0.35), 2),
            "drift": round(random.uniform(-0.02, 0.02), 2),
            "horizon_days": random.randint(1, 10)
        }

        with patch("skills.market_portfolio_audit_compliance_hub.log_simulation") as mock_log, \
             patch("skills.market_portfolio_stress_audit_visualizer.visualize_stress_test") as mock_vis:

            res = run_monte_carlo_stress_test(portfolio_id, portfolio_value, scenario_params, iterations)

            mock_log.assert_called_once()
            mock_vis.assert_called_once()

            self.assertEqual(res["portfolio_id"], portfolio_id)
            self.assertEqual(res["initial_value"], portfolio_value)
            self.assertEqual(res["iterations"], iterations)
            self.assertIn("simulation_id", res)
            self.assertTrue(res["simulation_id"].startswith("sim_"))
            self.assertIsInstance(res["var_95"], float)
            self.assertIsInstance(res["expected_shortfall"], float)


if __name__ == "__main__":
    unittest.main()