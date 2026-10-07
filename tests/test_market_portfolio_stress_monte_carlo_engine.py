import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import math

from skills.market_portfolio_stress_monte_carlo_engine import (
    MonteCarloStressEngine,
    run_monte_carlo_stress_test
)
from skills import db_storage


class TestMonteCarloStressEngine(unittest.TestCase):

    def setUp(self):
        self.engine = MonteCarloStressEngine()
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.initial_value = round(random.uniform(50000.0, 500000.0), 2)
        self.volatility = round(random.uniform(0.1, 0.5), 4)
        self.drift = round(random.uniform(-0.05, 0.05), 4)
        self.simulations = random.randint(50, 200)
        self.horizon_days = random.randint(5, 30)

    def test_run_simulation_integration_db_storage(self):
        with patch.object(db_storage, "fetch_portfolio", return_value={
            "portfolio_id": self.portfolio_id,
            "initial_value": self.initial_value,
            "volatility": self.volatility,
            "drift": self.drift
        }) as mock_fetch:
            
            result = self.engine.run_simulation(
                portfolio_id=self.portfolio_id,
                simulations=self.simulations,
                horizon_days=self.horizon_days
            )

            mock_fetch.assert_called_once_with(self.portfolio_id)
            self.assertIn("portfolio_id", result)
            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertIn("simulation_results", result)
            self.assertIn("var_95", result)
            self.assertIn("cvar_95", result)
            self.assertEqual(len(result["simulation_results"]), self.simulations)
            self.assertIsInstance(result["var_95"], float)
            self.assertIsInstance(result["cvar_95"], float)

    def test_run_simulation_fallback_in_memory_db(self):
        with patch.object(db_storage, "fetch_portfolio", side_effect=AttributeError("No fetch_portfolio")):
            in_memory = getattr(db_storage, "_in_memory_db", {})
            in_memory[self.portfolio_id] = {
                "portfolio_id": self.portfolio_id,
                "initial_value": self.initial_value,
                "volatility": self.volatility,
                "drift": self.drift
            }
            setattr(db_storage, "_in_memory_db", in_memory)

            result = self.engine.run_simulation(
                portfolio_id=self.portfolio_id,
                simulations=self.simulations,
                horizon_days=self.horizon_days
            )

            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertEqual(len(result["simulation_results"]), self.simulations)

    def test_export_report_method(self):
        report_id = f"rep_{uuid.uuid4().hex[:8]}"
        loss_limit = round(random.uniform(1000.0, 10000.0), 2)

        with patch("skills.market_portfolio_data_exporter.export", return_value={"report_id": report_id, "loss_limit": loss_limit, "status": "exported"}) as mock_export:
            res = self.engine.export_report(report_id, loss_limit)
            mock_export.assert_called_once_with(report_id, loss_limit)
            self.assertEqual(res["report_id"], report_id)
            self.assertEqual(res["loss_limit"], loss_limit)

    def test_consume_stream_method(self):
        payload_token = f"stream_{uuid.uuid4().hex[:6]}"
        with patch("skills.market_portfolio_api_gateway.stream_payload", return_value={"token": payload_token}) as mock_stream:
            res = self.engine.consume_stream()
            mock_stream.assert_called_once()
            self.assertEqual(res["token"], payload_token)

    def test_run_monte_carlo_stress_test_function(self):
        scenario_params = {
            "volatility": self.volatility,
            "drift": self.drift,
            "horizon_days": self.horizon_days
        }

        with patch("skills.market_portfolio_audit_compliance_hub.log_simulation") as mock_log, \
             patch("skills.market_portfolio_stress_audit_visualizer.visualize_stress_test") as mock_vis:
            
            res = run_monte_carlo_stress_test(
                portfolio_id=self.portfolio_id,
                portfolio_value=self.initial_value,
                scenario_params=scenario_params,
                iterations=self.simulations
            )

            self.assertEqual(res["portfolio_id"], self.portfolio_id)
            self.assertEqual(res["initial_value"], self.initial_value)
            self.assertEqual(res["iterations"], self.simulations)
            self.assertIn("simulation_id", res)
            self.assertIn("var_95", res)
            self.assertIn("expected_shortfall", res)
            
            mock_log.assert_called_once()
            mock_vis.assert_called_once()


if __name__ == "__main__":
    unittest.main()