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


class TestMonteCarloStressEngine(unittest.TestCase):

    def setUp(self):
        self.engine = MonteCarloStressEngine()
        self.portfolio_id = uuid.uuid4().hex
        self.simulations = random.randint(10, 50)
        self.horizon_days = random.randint(1, 10)
        self.initial_value = random.uniform(50000.0, 150000.0)
        self.volatility = random.uniform(0.1, 0.4)
        self.drift = random.uniform(-0.05, 0.05)

    def test_run_simulation_with_db_storage(self):
        with patch("skills.db_storage.fetch_portfolio") as mock_fetch:
            mock_fetch.return_value = {
                "portfolio_id": self.portfolio_id,
                "initial_value": self.initial_value,
                "volatility": self.volatility,
                "drift": self.drift
            }
            with patch("skills.market_anomaly_detector.get_current_anomaly_multiplier") as mock_anomaly:
                anomaly_mult = random.uniform(0.8, 1.5)
                mock_anomaly.return_value = anomaly_mult
                with patch("skills.market_portfolio_audit_compliance_hub.log_simulation") as mock_audit:
                    result = self.engine.run_simulation(self.portfolio_id, self.simulations, self.horizon_days)

                    self.assertIsInstance(result, dict)
                    self.assertEqual(result["portfolio_id"], self.portfolio_id)
                    self.assertIn("simulation_results", result)
                    self.assertIn("var_95", result)
                    self.assertIn("cvar_95", result)
                    self.assertEqual(len(result["simulation_results"]), self.simulations)
                    mock_audit.assert_called_once()

    def test_run_simulation_attribute_error_fallback(self):
        with patch("skills.db_storage.fetch_portfolio", side_effect=AttributeError):
            with patch("skills.db_storage._in_memory_db", {self.portfolio_id: {
                "portfolio_id": self.portfolio_id,
                "initial_value": self.initial_value,
                "volatility": self.volatility,
                "drift": self.drift
            }}):
                result = self.engine.run_simulation(self.portfolio_id, self.simulations, self.horizon_days)
                self.assertIsInstance(result, dict)
                self.assertEqual(result["portfolio_id"], self.portfolio_id)
                self.assertEqual(len(result["simulation_results"]), self.simulations)

    def test_get_anomaly_adjustment_exception(self):
        with patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", side_effect=AttributeError):
            adj = self.engine._get_anomaly_adjustment()
            self.assertEqual(adj, 1.0)

    def test_export_report_success_and_fallback(self):
        report_id = uuid.uuid4().hex
        loss_limit = random.uniform(1000.0, 10000.0)
        with patch("skills.market_portfolio_data_exporter.export") as mock_export:
            expected_dict = {"report_id": report_id, "loss_limit": loss_limit, "status": uuid.uuid4().hex}
            mock_export.return_value = expected_dict
            res = self.engine.export_report(report_id, loss_limit)
            self.assertEqual(res, expected_dict)

        with patch("skills.market_portfolio_data_exporter.export", side_effect=AttributeError):
            res_fallback = self.engine.export_report(report_id, loss_limit)
            self.assertEqual(res_fallback["report_id"], report_id)
            self.assertEqual(res_fallback["loss_limit"], loss_limit)

    def test_consume_stream_success_and_fallback(self):
        stream_data = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))
        with patch("skills.market_portfolio_api_gateway.stream_payload") as mock_stream:
            mock_stream.return_value = stream_data
            res = self.engine.consume_stream()
            self.assertEqual(res, stream_data)

        with patch("skills.market_portfolio_api_gateway.stream_payload", side_effect=AttributeError):
            res_fallback = self.engine.consume_stream()
            self.assertIsNone(res_fallback)

    def test_run_monte_carlo_stress_test_function(self):
        iterations = random.randint(15, 30)
        scenario_params = {
            "volatility": random.uniform(0.15, 0.35),
            "drift": random.uniform(-0.02, 0.02),
            "horizon_days": random.randint(1, 5)
        }
        with patch("skills.market_portfolio_audit_compliance_hub.log_simulation") as mock_audit:
            res = run_monte_carlo_stress_test(
                portfolio_id=self.portfolio_id,
                portfolio_value=self.initial_value,
                scenario_params=scenario_params,
                iterations=iterations
            )
            self.assertIsInstance(res, dict)
            self.assertEqual(res["portfolio_id"], self.portfolio_id)
            self.assertEqual(res["initial_value"], self.initial_value)
            self.assertEqual(res["iterations"], iterations)
            self.assertIn("simulation_id", res)
            self.assertIn("var_95", res)
            self.assertIn("expected_shortfall", res)
            mock_audit.assert_called_once()


if __name__ == "__main__":
    unittest.main()