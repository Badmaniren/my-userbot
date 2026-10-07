import unittest
from unittest.mock import patch, MagicMock
import uuid
import random

from skills import market_portfolio_stress_monte_carlo_engine
from skills import db_storage
from skills import market_anomaly_detector
from skills import market_portfolio_data_exporter
from skills import market_portfolio_api_gateway
from skills import market_portfolio_audit_compliance_hub
from skills import market_portfolio_stress_audit_visualizer


class TestMonteCarloStressEngine(unittest.TestCase):

    def setUp(self):
        self.engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        self.portfolio_id = uuid.uuid4().hex
        self.initial_value = random.uniform(50000.0, 500000.0)
        self.volatility = random.uniform(0.1, 0.5)
        self.drift = random.uniform(-0.05, 0.05)
        self.simulations = random.randint(10, 50)
        self.horizon_days = random.randint(1, 10)

        if not hasattr(db_storage, "_in_memory_db"):
            db_storage._in_memory_db = {}
        db_storage._in_memory_db[self.portfolio_id] = {
            "portfolio_id": self.portfolio_id,
            "initial_value": self.initial_value,
            "volatility": self.volatility,
            "drift": self.drift
        }

    def test_run_simulation_success(self):
        result = self.engine.run_simulation(
            portfolio_id=self.portfolio_id,
            simulations=self.simulations,
            horizon_days=self.horizon_days
        )

        self.assertIn("portfolio_id", result)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertIn("simulation_results", result)
        self.assertEqual(len(result["simulation_results"]), self.simulations)
        self.assertIn("var_95", result)
        self.assertIn("cvar_95", result)
        self.assertIsInstance(result["var_95"], float)
        self.assertIsInstance(result["cvar_95"], float)

    def test_run_simulation_with_anomaly_detector(self):
        anomaly_mult = random.uniform(1.1, 2.5)
        with patch.object(market_anomaly_detector, "get_current_anomaly_multiplier", return_value=anomaly_mult) as mock_detector:
            result = self.engine.run_simulation(
                portfolio_id=self.portfolio_id,
                simulations=self.simulations,
                horizon_days=self.horizon_days
            )
            mock_detector.assert_called_once()
            self.assertIn("var_95", result)

    def test_get_anomaly_adjustment_fallback(self):
        if hasattr(market_anomaly_detector, "get_current_anomaly_multiplier"):
            delattr(market_anomaly_detector, "get_current_anomaly_multiplier")
        
        mult = self.engine._get_anomaly_adjustment()
        self.assertEqual(mult, 1.0)

        setattr(market_anomaly_detector, "get_current_anomaly_multiplier", lambda: 1.0)

    def test_export_report(self):
        report_id = uuid.uuid4().hex
        loss_limit = random.uniform(1000.0, 10000.0)

        with patch.object(market_portfolio_data_exporter, "export", return_value={"report_id": report_id, "loss_limit": loss_limit}) as mock_export:
            res = self.engine.export_report(report_id, loss_limit)
            mock_export.assert_called_once_with(report_id, loss_limit)
            self.assertEqual(res["report_id"], report_id)
            self.assertEqual(res["loss_limit"], loss_limit)

    def test_consume_stream(self):
        stream_data = {"stream_id": uuid.uuid4().hex}
        with patch.object(market_portfolio_api_gateway, "stream_payload", return_value=stream_data) as mock_stream:
            res = self.engine.consume_stream()
            mock_stream.assert_called_once()
            self.assertEqual(res, stream_data)

    def test_run_monte_carlo_stress_test_function(self):
        portfolio_val = random.uniform(10000.0, 1000000.0)
        scenario_params = {
            "volatility": random.uniform(0.1, 0.4),
            "drift": random.uniform(-0.02, 0.02),
            "horizon_days": random.randint(1, 5)
        }
        iterations = random.randint(20, 60)

        with patch.object(market_portfolio_audit_compliance_hub, "log_simulation") as mock_audit, \
             patch.object(market_portfolio_stress_audit_visualizer, "visualize_stress_test") as mock_vis:
            
            res = market_portfolio_stress_monte_carlo_engine.run_monte_carlo_stress_test(
                portfolio_id=self.portfolio_id,
                portfolio_value=portfolio_val,
                scenario_params=scenario_params,
                iterations=iterations
            )

            self.assertIn("simulation_id", res)
            self.assertEqual(res["portfolio_id"], self.portfolio_id)
            self.assertEqual(res["initial_value"], portfolio_val)
            self.assertEqual(res["iterations"], iterations)
            self.assertIn("var_95", res)
            self.assertIn("expected_shortfall", res)

            mock_audit.assert_called_once()
            mock_vis.assert_called_once()


if __name__ == "__main__":
    unittest.main()