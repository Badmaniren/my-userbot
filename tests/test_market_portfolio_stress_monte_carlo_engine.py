import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import math
import io

from skills import db_storage
from skills import market_anomaly_detector
from skills import market_portfolio_data_exporter
from skills import market_portfolio_api_gateway
from skills import market_portfolio_audit_compliance_hub
from skills import market_portfolio_stress_audit_visualizer
from skills.market_portfolio_stress_monte_carlo_engine import (
    MonteCarloStressEngine,
    run_monte_carlo_stress_test
)


class TestMonteCarloStressEngine(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.report_id = uuid.uuid4().hex
        self.simulations = random.randint(10, 50)
        self.horizon_days = random.randint(1, 10)
        self.iterations = random.randint(10, 50)
        self.portfolio_value = round(random.uniform(50000.0, 500000.0), 2)
        self.loss_limit = round(random.uniform(1000.0, 10000.0), 2)

    def test_run_simulation_success(self):
        engine = MonteCarloStressEngine()
        mock_portfolio_data = {
            "portfolio_id": self.portfolio_id,
            "initial_value": self.portfolio_value,
            "volatility": 0.15,
            "drift": 0.05
        }

        with patch("skills.db_storage.fetch_portfolio", return_value=mock_portfolio_data) as mock_fetch, \
             patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", return_value=1.1) as mock_anomaly, \
             patch("skills.market_portfolio_audit_compliance_hub.log_simulation") as mock_audit:

            result = engine.run_simulation(self.portfolio_id, self.simulations, self.horizon_days)

            mock_fetch.assert_called_once_with(self.portfolio_id)
            mock_anomaly.assert_called_once()
            mock_audit.assert_called_once()

            self.assertIn("portfolio_id", result)
            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertIn("simulation_results", result)
            self.assertEqual(len(result["simulation_results"]), self.simulations)
            self.assertIn("var_95", result)
            self.assertIn("cvar_95", result)
            self.assertIsInstance(result["var_95"], float)
            self.assertIsInstance(result["cvar_95"], float)

    def test_run_simulation_attribute_error_fallback(self):
        engine = MonteCarloStressEngine()
        
        with patch.object(db_storage, "fetch_portfolio", side_effect=AttributeError), \
             patch.object(market_anomaly_detector, "get_current_anomaly_multiplier", side_effect=AttributeError), \
             patch("skills.market_portfolio_audit_compliance_hub.log_simulation") as mock_audit:

            setattr(db_storage, "_in_memory_db", {
                self.portfolio_id: {
                    "portfolio_id": self.portfolio_id,
                    "initial_value": self.portfolio_value,
                    "volatility": 0.2,
                    "drift": 0.0
                }
            })

            result = engine.run_simulation(self.portfolio_id, self.simulations, self.horizon_days)

            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertEqual(len(result["simulation_results"]), self.simulations)
            self.assertIsInstance(result["var_95"], float)
            self.assertIsInstance(result["cvar_95"], float)
            mock_audit.assert_called_once()

    def test_export_report_success(self):
        engine = MonteCarloStressEngine()
        expected_export = {"report_id": self.report_id, "loss_limit": self.loss_limit}

        with patch("skills.market_portfolio_data_exporter.export", return_value=expected_export) as mock_export:
            result = engine.export_report(self.report_id, self.loss_limit)
            mock_export.assert_called_once_with(self.report_id, self.loss_limit)
            self.assertEqual(result, expected_export)

    def test_export_report_attribute_error_fallback(self):
        engine = MonteCarloStressEngine()

        with patch.object(market_anomaly_detector, "get_current_anomaly_multiplier", side_effect=AttributeError), \
             patch.object(market_portfolio_data_exporter, "export", side_effect=AttributeError):
            result = engine.export_report(self.report_id, self.loss_limit)
            self.assertEqual(result["report_id"], self.report_id)
            self.assertEqual(result["loss_limit"], self.loss_limit)

    def test_consume_stream_success(self):
        engine = MonteCarloStressEngine()
        stream_payload_data = uuid.uuid4().hex

        with patch("skills.market_portfolio_api_gateway.stream_payload", return_value=stream_payload_data) as mock_stream:
            result = engine.consume_stream()
            mock_stream.assert_called_once()
            self.assertEqual(result, stream_payload_data)

    def test_consume_stream_attribute_error_fallback(self):
        engine = MonteCarloStressEngine()

        with patch.object(market_portfolio_api_gateway, "stream_payload", side_effect=AttributeError):
            result = engine.consume_stream()
            self.assertIsNone(result)

    def test_run_monte_carlo_stress_test_function(self):
        scenario_params = {
            "volatility": 0.18,
            "drift": 0.02,
            "horizon_days": self.horizon_days
        }

        with patch("skills.market_portfolio_audit_compliance_hub.log_simulation") as mock_audit, \
             patch("skills.market_portfolio_stress_audit_visualizer.visualize_stress_test") as mock_visualizer:

            result = run_monte_carlo_stress_test(
                portfolio_id=self.portfolio_id,
                portfolio_value=self.portfolio_value,
                scenario_params=scenario_params,
                iterations=self.iterations
            )

            mock_audit.assert_called_once()
            mock_visualizer.assert_called_once()

            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertEqual(result["initial_value"], self.portfolio_value)
            self.assertEqual(result["iterations"], self.iterations)
            self.assertIn("simulation_id", result)
            self.assertIn("var_95", result)
            self.assertIn("expected_shortfall", result)
            self.assertIsInstance(result["var_95"], float)
            self.assertIsInstance(result["expected_shortfall"], float)


if __name__ == "__main__":
    unittest.main()