import unittest
from unittest.mock import patch
import uuid
import random
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
        self.portfolio_id = uuid.uuid4().hex
        self.simulations = random.randint(10, 50)
        self.horizon_days = random.randint(1, 10)
        self.initial_value = round(random.uniform(50000.0, 500000.0), 2)
        self.volatility = round(random.uniform(0.1, 0.5), 4)
        self.drift = round(random.uniform(-0.05, 0.05), 4)

    def test_run_simulation_basic(self):
        engine = MonteCarloStressEngine()
        
        in_mem = getattr(db_storage, "_in_memory_db", {})
        in_mem[self.portfolio_id] = {
            "portfolio_id": self.portfolio_id,
            "initial_value": self.initial_value,
            "volatility": self.volatility,
            "drift": self.drift
        }
        setattr(db_storage, "_in_memory_db", in_mem)

        result = engine.run_simulation(self.portfolio_id, self.simulations, self.horizon_days)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertIn("simulation_results", result)
        self.assertIn("var_95", result)
        self.assertIn("cvar_95", result)
        self.assertEqual(len(result["simulation_results"]), self.simulations)
        for path in result["simulation_results"]:
            self.assertEqual(len(path), self.horizon_days)

    def test_run_simulation_with_anomaly_detector_mock(self):
        engine = MonteCarloStressEngine()
        custom_multiplier = round(random.uniform(1.1, 3.0), 2)

        with patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", return_value=custom_multiplier) as mock_anomaly:
            in_mem = getattr(db_storage, "_in_memory_db", {})
            in_mem[self.portfolio_id] = {
                "portfolio_id": self.portfolio_id,
                "initial_value": self.initial_value,
                "volatility": self.volatility,
                "drift": self.drift
            }
            setattr(db_storage, "_in_memory_db", in_mem)

            result = engine.run_simulation(self.portfolio_id, self.simulations, self.horizon_days)
            mock_anomaly.assert_called_once()
            self.assertIsInstance(result, dict)
            self.assertEqual(result["portfolio_id"], self.portfolio_id)

    def test_export_report_delegation(self):
        engine = MonteCarloStressEngine()
        report_id = uuid.uuid4().hex
        loss_limit = round(random.uniform(1000.0, 50000.0), 2)

        with patch("skills.market_portfolio_data_exporter.export", return_value={"report_id": report_id, "loss_limit": loss_limit}) as mock_export:
            res = engine.export_report(report_id, loss_limit)
            mock_export.assert_called_once_with(report_id, loss_limit)
            self.assertEqual(res["report_id"], report_id)
            self.assertEqual(res["loss_limit"], loss_limit)

    def test_consume_stream_delegation(self):
        engine = MonteCarloStressEngine()
        garbage_stream = io.BytesIO(uuid.uuid4().bytes)

        with patch("skills.market_portfolio_api_gateway.stream_payload", return_value=garbage_stream) as mock_stream:
            res = engine.consume_stream()
            mock_stream.assert_called_once()
            self.assertEqual(res, garbage_stream)

    def test_run_monte_carlo_stress_test_function(self):
        scenario_params = {
            "volatility": self.volatility,
            "drift": self.drift,
            "horizon_days": self.horizon_days
        }

        with patch("skills.market_portfolio_audit_compliance_hub.log_simulation") as mock_log, \
             patch("skills.market_portfolio_stress_audit_visualizer.visualize_stress_test") as mock_viz:
            
            res = run_monte_carlo_stress_test(
                portfolio_id=self.portfolio_id,
                portfolio_value=self.initial_value,
                scenario_params=scenario_params,
                iterations=self.simulations
            )

            self.assertIsInstance(res, dict)
            self.assertEqual(res["portfolio_id"], self.portfolio_id)
            self.assertEqual(res["initial_value"], self.initial_value)
            self.assertEqual(res["iterations"], self.simulations)
            self.assertIn("simulation_id", res)
            self.assertIn("var_95", res)
            self.assertIn("expected_shortfall", res)

            mock_log.assert_called_once()
            mock_viz.assert_called_once()
            visualized_arg = mock_viz.call_args[0][0]
            self.assertEqual(visualized_arg["portfolio_id"], self.portfolio_id)
            self.assertEqual(visualized_arg["simulation_id"], res["simulation_id"])


if __name__ == "__main__":
    unittest.main()