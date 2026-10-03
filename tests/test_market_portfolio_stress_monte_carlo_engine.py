import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import math
import io

from skills import db_storage
from skills import market_anomaly_detector
from skills import market_portfolio_data_exporter
from skills import market_portfolio_api_gateway
from skills import market_portfolio_audit_compliance_hub
from skills.market_portfolio_stress_monte_carlo_engine import (
    MonteCarloStressEngine,
    run_monte_carlo_stress_test
)


class TestMonteCarloStressEngine(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.simulations = random.randint(10, 50)
        self.horizon_days = random.randint(1, 10)
        self.initial_value = random.uniform(50000.0, 500000.0)
        self.engine = MonteCarloStressEngine()

    def test_run_simulation_success(self):
        portfolio_mock_data = {
            "portfolio_id": self.portfolio_id,
            "initial_value": self.initial_value,
            "volatility": random.uniform(0.1, 0.4),
            "drift": random.uniform(-0.05, 0.05)
        }

        with patch.object(db_storage, "fetch_portfolio", return_value=portfolio_mock_data) as mock_fetch, \
             patch.object(market_anomaly_detector, "get_current_anomaly_multiplier", return_value=1.0) as mock_anomaly, \
             patch.object(market_portfolio_audit_compliance_hub, "log_simulation") as mock_audit:

            result = self.engine.run_simulation(self.portfolio_id, self.simulations, self.horizon_days)

            mock_fetch.assert_called_once_with(self.portfolio_id)
            mock_anomaly.assert_called_once()
            mock_audit.assert_called_once()

            self.assertIn("portfolio_id", result)
            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertIn("simulation_results", result)
            self.assertIn("var_95", result)
            self.assertIn("cvar_95", result)
            self.assertEqual(len(result["simulation_results"]), self.simulations)

    def test_run_simulation_missing_fetch_attribute(self):
        portfolio_key = f"mem_{uuid.uuid4().hex[:8]}"
        in_memory_data = {
            portfolio_key: {
                "portfolio_id": portfolio_key,
                "initial_value": self.initial_value,
                "volatility": 0.2,
                "drift": 0.0
            }
        }

        with patch.object(db_storage, "fetch_portfolio", side_effect=AttributeError("No fetch")):
            with patch.object(db_storage, "_in_memory_db", in_memory_data, create=True):
                with patch.object(market_portfolio_audit_compliance_hub, "log_simulation"):
                    result = self.engine.run_simulation(portfolio_key, self.simulations, self.horizon_days)
                    self.assertEqual(result["portfolio_id"], portfolio_key)
                    self.assertIsInstance(result["var_95"], float)

    def test_get_anomaly_adjustment_fallback(self):
        with patch.object(market_anomaly_detector, "get_current_anomaly_multiplier", side_effect=AttributeError):
            mult = self.engine._get_anomaly_adjustment()
            self.assertEqual(mult, 1.0)

    def test_export_report_success(self):
        report_id = f"rep_{uuid.uuid4().hex[:8]}"
        loss_limit = random.uniform(1000.0, 10000.0)
        expected_dict = {"report_id": report_id, "loss_limit": loss_limit, "status": "exported"}

        with patch.object(market_portfolio_data_exporter, "export", return_value=expected_dict) as mock_export:
            res = self.engine.export_report(report_id, loss_limit)
            mock_export.assert_called_once_with(report_id, loss_limit)
            self.assertEqual(res, expected_dict)

    def test_export_report_fallback(self):
        report_id = f"rep_{uuid.uuid4().hex[:8]}"
        loss_limit = random.uniform(1000.0, 10000.0)

        with patch.object(market_portfolio_data_exporter, "export", side_effect=AttributeError):
            res = self.engine.export_report(report_id, loss_limit)
            self.assertEqual(res["report_id"], report_id)
            self.assertEqual(res["loss_limit"], loss_limit)

    def test_consume_stream_success(self):
        payload_data = f"stream_data_{uuid.uuid4().hex}"
        with patch.object(market_portfolio_api_gateway, "stream_payload", return_value=payload_data) as mock_stream:
            res = self.engine.consume_stream()
            mock_stream.assert_called_once()
            self.assertEqual(res, payload_data)

    def test_consume_stream_fallback(self):
        with patch.object(market_portfolio_api_gateway, "stream_payload", side_effect=AttributeError):
            res = self.engine.consume_stream()
            self.assertIsNone(res)

    def test_run_monte_carlo_stress_test_function(self):
        scenario_params = {
            "volatility": random.uniform(0.1, 0.5),
            "drift": random.uniform(-0.02, 0.02),
            "horizon_days": random.randint(1, 5)
        }
        iterations = random.randint(10, 30)

        with patch.object(market_portfolio_audit_compliance_hub, "log_simulation") as mock_audit:
            result = run_monte_carlo_stress_test(
                portfolio_id=self.portfolio_id,
                portfolio_value=self.initial_value,
                scenario_params=scenario_params,
                iterations=iterations
            )

            mock_audit.assert_called_once()
            self.assertIn("simulation_id", result)
            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertEqual(result["initial_value"], self.initial_value)
            self.assertEqual(result["iterations"], iterations)
            self.assertIsInstance(result["var_95"], float)
            self.assertIsInstance(result["expected_shortfall"], float)


if __name__ == "__main__":
    unittest.main()