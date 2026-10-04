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
        self.portfolio_id = f"port_{uuid.uuid4().hex}"
        self.simulations = random.randint(10, 50)
        self.horizon_days = random.randint(5, 30)
        self.initial_value = round(random.uniform(50000.0, 500000.0), 2)
        self.volatility = round(random.uniform(0.1, 0.5), 2)
        self.drift = round(random.uniform(-0.05, 0.05), 4)

    def test_run_simulation_with_db_storage(self):
        mock_portfolio_data = {
            "portfolio_id": self.portfolio_id,
            "initial_value": self.initial_value,
            "volatility": self.volatility,
            "drift": self.drift
        }

        with patch("skills.market_portfolio_stress_monte_carlo_engine.db_storage") as mock_db, \
             patch("skills.market_portfolio_stress_monte_carlo_engine.market_portfolio_audit_compliance_hub") as mock_audit:

            mock_db.fetch_portfolio.return_value = mock_portfolio_data
            mock_audit.log_simulation = MagicMock()

            result = self.engine.run_simulation(
                self.portfolio_id,
                self.simulations,
                self.horizon_days
            )

            self.assertIsInstance(result, dict)
            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertIn("simulation_results", result)
            self.assertIn("var_95", result)
            self.assertIn("cvar_95", result)
            self.assertEqual(len(result["simulation_results"]), self.simulations)
            for path in result["simulation_results"]:
                self.assertEqual(len(path), self.horizon_days)

            mock_db.fetch_portfolio.assert_called_once_with(self.portfolio_id)

    def test_run_simulation_fallback_in_memory(self):
        with patch("skills.market_portfolio_stress_monte_carlo_engine.db_storage") as mock_db:
            del mock_db.fetch_portfolio
            mock_db._in_memory_db = {
                self.portfolio_id: {
                    "portfolio_id": self.portfolio_id,
                    "initial_value": self.initial_value,
                    "volatility": self.volatility,
                    "drift": self.drift
                }
            }

            result = self.engine.run_simulation(
                self.portfolio_id,
                self.simulations,
                self.horizon_days
            )

            self.assertIsInstance(result, dict)
            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertIsInstance(result["var_95"], float)
            self.assertIsInstance(result["cvar_95"], float)

    def test_get_anomaly_adjustment(self):
        expected_multiplier = round(random.uniform(1.0, 3.0), 2)
        with patch("skills.market_portfolio_stress_monte_carlo_engine.market_anomaly_detector") as mock_detector:
            mock_detector.get_current_anomaly_multiplier.return_value = expected_multiplier
            multiplier = self.engine._get_anomaly_adjustment()
            self.assertEqual(multiplier, expected_multiplier)

    def test_export_report(self):
        report_id = f"rep_{uuid.uuid4().hex}"
        loss_limit = round(random.uniform(1000.0, 10000.0), 2)
        expected_response = {"report_id": report_id, "loss_limit": loss_limit, "status": f"exported_{uuid.uuid4().hex}"}

        with patch("skills.market_portfolio_stress_monte_carlo_engine.market_portfolio_data_exporter") as mock_exporter:
            mock_exporter.export.return_value = expected_response
            response = self.engine.export_report(report_id, loss_limit)
            self.assertEqual(response, expected_response)
            mock_exporter.export.assert_called_once_with(report_id, loss_limit)

    def test_consume_stream(self):
        stream_data = f"payload_{uuid.uuid4().hex}".encode('utf-8')
        mock_stream = io.BytesIO(stream_data)

        with patch("skills.market_portfolio_stress_monte_carlo_engine.market_portfolio_api_gateway") as mock_gateway:
            mock_gateway.stream_payload.return_value = mock_stream
            res = self.engine.consume_stream()
            self.assertEqual(res.read(), stream_data)

    def test_run_monte_carlo_stress_test(self):
        scenario_params = {
            "volatility": self.volatility,
            "drift": self.drift,
            "horizon_days": self.horizon_days
        }
        iterations = random.randint(20, 60)

        with patch("skills.market_portfolio_stress_monte_carlo_engine.market_portfolio_audit_compliance_hub") as mock_audit, \
             patch("skills.market_portfolio_stress_monte_carlo_engine.market_portfolio_stress_audit_visualizer") as mock_vis:

            mock_audit.log_simulation = MagicMock()
            mock_vis.visualize_stress_test = MagicMock()

            result = run_monte_carlo_stress_test(
                self.portfolio_id,
                self.initial_value,
                scenario_params,
                iterations
            )

            self.assertIsInstance(result, dict)
            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertEqual(result["initial_value"], self.initial_value)
            self.assertEqual(result["iterations"], iterations)
            self.assertIn("simulation_id", result)
            self.assertIn("var_95", result)
            self.assertIn("expected_shortfall", result)

            mock_audit.log_simulation.assert_called_once()
            mock_vis.visualize_stress_test.assert_called_once_with(result)


if __name__ == "__main__":
    unittest.main()