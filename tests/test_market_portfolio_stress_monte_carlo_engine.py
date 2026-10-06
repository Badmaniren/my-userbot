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

    def test_run_simulation_success(self):
        portfolio_id = uuid.uuid4().hex
        simulations = random.randint(10, 50)
        horizon_days = random.randint(1, 10)
        initial_value = float(random.randint(50000, 150000))
        volatility = random.uniform(0.1, 0.4)
        drift = random.uniform(-0.05, 0.05)

        mock_portfolio_data = {
            "portfolio_id": portfolio_id,
            "initial_value": initial_value,
            "volatility": volatility,
            "drift": drift
        }

        with patch.object(db_storage, "fetch_portfolio", return_value=mock_portfolio_data, create=True) as mock_fetch, \
             patch.object(market_anomaly_detector, "get_current_anomaly_multiplier", return_value=1.0, create=True) as mock_anomaly, \
             patch.object(market_portfolio_audit_compliance_hub, "log_simulation", create=True) as mock_audit:

            engine = MonteCarloStressEngine()
            result = engine.run_simulation(portfolio_id, simulations, horizon_days)

            mock_fetch.assert_called_once_with(portfolio_id)
            mock_anomaly.assert_called_once()
            mock_audit.assert_called_once()

            self.assertIn("portfolio_id", result)
            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertIn("simulation_results", result)
            self.assertIn("var_95", result)
            self.assertIn("cvar_95", result)
            self.assertEqual(len(result["simulation_results"]), simulations)
            self.assertTrue(isinstance(result["var_95"], float))
            self.assertTrue(isinstance(result["cvar_95"], float))

    def test_run_simulation_attribute_error_fallback(self):
        portfolio_id = uuid.uuid4().hex
        simulations = random.randint(5, 20)
        horizon_days = random.randint(1, 5)

        if hasattr(db_storage, "fetch_portfolio"):
            delattr(db_storage, "fetch_portfolio")

        in_memory_db = {
            portfolio_id: {
                "portfolio_id": portfolio_id,
                "initial_value": 200000.0,
                "volatility": 0.25,
                "drift": 0.01
            }
        }
        setattr(db_storage, "_in_memory_db", in_memory_db)

        try:
            with patch.object(market_anomaly_detector, "get_current_anomaly_multiplier", side_effect=AttributeError, create=True):
                engine = MonteCarloStressEngine()
                result = engine.run_simulation(portfolio_id, simulations, horizon_days)

                self.assertEqual(result["portfolio_id"], portfolio_id)
                self.assertEqual(len(result["simulation_results"]), simulations)
        finally:
            setattr(db_storage, "fetch_portfolio", lambda pid: getattr(db_storage, "_in_memory_db", {}).get(pid, {"portfolio_id": pid}))

    def test_export_report_success(self):
        report_id = uuid.uuid4().hex
        loss_limit = float(random.randint(1000, 10000))
        expected_output = {"report_id": report_id, "loss_limit": loss_limit, "status": uuid.uuid4().hex}

        with patch.object(market_portfolio_data_exporter, "export", return_value=expected_output, create=True) as mock_export:
            engine = MonteCarloStressEngine()
            result = engine.export_report(report_id, loss_limit)

            mock_export.assert_called_once_with(report_id, loss_limit)
            self.assertEqual(result, expected_output)

    def test_export_report_attribute_error_fallback(self):
        report_id = uuid.uuid4().hex
        loss_limit = float(random.randint(500, 5000))

        if hasattr(market_portfolio_data_exporter, "export"):
            delattr(market_portfolio_data_exporter, "export")

        try:
            engine = MonteCarloStressEngine()
            result = engine.export_report(report_id, loss_limit)
            self.assertEqual(result["report_id"], report_id)
            self.assertEqual(result["loss_limit"], loss_limit)
        finally:
            setattr(market_portfolio_data_exporter, "export", lambda rep_id, limit: {"report_id": rep_id, "loss_limit": limit})

    def test_consume_stream_success(self):
        expected_payload = {"stream_id": uuid.uuid4().hex, "data": uuid.uuid4().hex}

        with patch.object(market_portfolio_api_gateway, "stream_payload", return_value=expected_payload, create=True) as mock_stream:
            engine = MonteCarloStressEngine()
            result = engine.consume_stream()

            mock_stream.assert_called_once()
            self.assertEqual(result, expected_payload)

    def test_consume_stream_attribute_error_fallback(self):
        if hasattr(market_portfolio_api_gateway, "stream_payload"):
            delattr(market_portfolio_api_gateway, "stream_payload")

        try:
            engine = MonteCarloStressEngine()
            result = engine.consume_stream()
            self.assertIsNone(result)
        finally:
            setattr(market_portfolio_api_gateway, "stream_payload", lambda: None)


class TestRunMonteCarloStressTestFunction(unittest.TestCase):

    def test_run_monte_carlo_stress_test_execution(self):
        portfolio_id = uuid.uuid4().hex
        portfolio_value = float(random.randint(10000, 500000))
        iterations = random.randint(10, 50)
        scenario_params = {
            "volatility": random.uniform(0.15, 0.35),
            "drift": random.uniform(-0.02, 0.02),
            "horizon_days": random.randint(1, 7)
        }

        with patch.object(market_portfolio_audit_compliance_hub, "log_simulation", create=True) as mock_audit_log, \
             patch.object(market_portfolio_stress_audit_visualizer, "visualize_stress_test", create=True) as mock_visualizer:

            result = run_monte_carlo_stress_test(
                portfolio_id=portfolio_id,
                portfolio_value=portfolio_value,
                scenario_params=scenario_params,
                iterations=iterations
            )

            mock_audit_log.assert_called_once()
            mock_visualizer.assert_called_once()

            self.assertIn("simulation_id", result)
            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertEqual(result["initial_value"], portfolio_value)
            self.assertEqual(result["iterations"], iterations)
            self.assertIn("var_95", result)
            self.assertIn("expected_shortfall", result)
            self.assertTrue(isinstance(result["var_95"], float))
            self.assertTrue(isinstance(result["expected_shortfall"], float))


if __name__ == "__main__":
    unittest.main()