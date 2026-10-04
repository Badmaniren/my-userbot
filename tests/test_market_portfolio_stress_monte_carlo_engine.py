import unittest
from unittest.mock import patch
import random
import uuid
import math

from skills.market_portfolio_stress_monte_carlo_engine import (
    MonteCarloStressEngine,
    run_monte_carlo_stress_test
)

class TestMonteCarloStressEngine(unittest.TestCase):

    def test_validate_inputs_success(self):
        engine = MonteCarloStressEngine()
        sims = random.randint(10, 100)
        horizon = random.randint(1, 30)
        try:
            engine._validate_inputs(sims, horizon)
        except Exception as e:
            self.fail(f"Validation failed unexpectedly with error: {e}")

    def test_validate_inputs_invalid_simulations(self):
        engine = MonteCarloStressEngine()
        sims = random.choice([0, -random.randint(1, 50), "100", None])
        horizon = random.randint(1, 30)
        with self.assertRaises((ValueError, TypeError)):
            engine._validate_inputs(sims, horizon)

    def test_validate_inputs_invalid_horizon(self):
        engine = MonteCarloStressEngine()
        sims = random.randint(10, 100)
        horizon = random.choice([0, -random.randint(1, 50), "10", None])
        with self.assertRaises((ValueError, TypeError)):
            engine._validate_inputs(sims, horizon)

    def test_run_simulation_with_db_storage(self):
        engine = MonteCarloStressEngine()
        portfolio_id = f"port_{uuid.uuid4().hex}"
        sims = random.randint(5, 20)
        horizon = random.randint(2, 10)
        mock_data = {
            "initial_value": float(random.randint(50000, 150000)),
            "volatility": float(random.uniform(0.1, 0.4)),
            "drift": float(random.uniform(-0.05, 0.05))
        }

        with patch("skills.db_storage.fetch_portfolio", return_value=mock_data) as mock_fetch, \
             patch("skills.market_portfolio_audit_compliance_hub.log_simulation") as mock_log:
            
            result = engine.run_simulation(portfolio_id, sims, horizon)
            
            mock_fetch.assert_called_once_with(portfolio_id)
            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertIn("var_95", result)
            self.assertIn("cvar_95", result)
            self.assertIn("simulation_results", result)
            self.assertEqual(len(result["simulation_results"]), sims)
            mock_log.assert_called_once()

    def test_run_simulation_fallback_to_memory_db(self):
        engine = MonteCarloStressEngine()
        portfolio_id = f"port_{uuid.uuid4().hex}"
        sims = random.randint(5, 20)
        horizon = random.randint(2, 10)
        mock_data = {
            "initial_value": float(random.randint(10000, 50000)),
            "volatility": float(random.uniform(0.1, 0.3)),
            "drift": 0.01
        }

        with patch("skills.db_storage.fetch_portfolio", side_effect=KeyError), \
             patch("skills.db_storage._in_memory_db", {portfolio_id: mock_data}, create=True), \
             patch("skills.market_portfolio_audit_compliance_hub.log_simulation") as mock_log:
            
            result = engine.run_simulation(portfolio_id, sims, horizon)
            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertIsInstance(result["var_95"], float)
            mock_log.assert_called_once()

    def test_get_anomaly_adjustment_success(self):
        engine = MonteCarloStressEngine()
        expected_mult = float(random.uniform(1.1, 2.5))
        with patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", return_value=expected_mult):
            mult = engine._get_anomaly_adjustment()
            self.assertEqual(mult, expected_mult)

    def test_get_anomaly_adjustment_fallback(self):
        engine = MonteCarloStressEngine()
        with patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", side_effect=AttributeError):
            mult = engine._get_anomaly_adjustment()
            self.assertEqual(mult, 1.0)

    def test_export_report_success(self):
        engine = MonteCarloStressEngine()
        report_id = f"rep_{uuid.uuid4().hex}"
        loss_limit = float(random.randint(1000, 10000))
        expected_response = {"status": uuid.uuid4().hex, "report_id": report_id}

        with patch("skills.market_portfolio_data_exporter.export", create=True, return_value=expected_response) as mock_export:
            res = engine.export_report(report_id, loss_limit)
            mock_export.assert_called_once_with(report_id, loss_limit)
            self.assertEqual(res, expected_response)

    def test_export_report_fallback(self):
        engine = MonteCarloStressEngine()
        report_id = f"rep_{uuid.uuid4().hex}"
        loss_limit = float(random.randint(1000, 10000))

        with patch("skills.market_portfolio_data_exporter", create=True) as mock_mod:
            if hasattr(mock_mod, "export"):
                delattr(mock_mod, "export")
            res = engine.export_report(report_id, loss_limit)
            self.assertEqual(res["report_id"], report_id)
            self.assertEqual(res["loss_limit"], loss_limit)

    def test_consume_stream_success(self):
        engine = MonteCarloStressEngine()
        stream_payload_data = {"stream_id": uuid.uuid4().hex, "data": random.randint(1, 100)}

        with patch("skills.market_portfolio_api_gateway.stream_payload", create=True, return_value=stream_payload_data) as mock_stream:
            res = engine.consume_stream()
            mock_stream.assert_called_once()
            self.assertEqual(res, stream_payload_data)

    def test_consume_stream_fallback(self):
        engine = MonteCarloStressEngine()
        with patch("skills.market_portfolio_api_gateway", create=True) as mock_mod:
            if hasattr(mock_mod, "stream_payload"):
                delattr(mock_mod, "stream_payload")
            res = engine.consume_stream()
            self.assertIsNone(res)

    def test_run_monte_carlo_stress_test_success(self):
        portfolio_id = f"port_{uuid.uuid4().hex}"
        portfolio_value = float(random.randint(50000, 500000))
        iterations = random.randint(10, 50)
        scenario_params = {
            "volatility": float(random.uniform(0.1, 0.5)),
            "drift": float(random.uniform(-0.02, 0.02)),
            "horizon_days": random.randint(1, 10)
        }

        with patch("skills.market_portfolio_audit_compliance_hub.log_simulation") as mock_log, \
             patch("skills.market_portfolio_stress_audit_visualizer.visualize_stress_test") as mock_vis:

            res = run_monte_carlo_stress_test(portfolio_id, portfolio_value, scenario_params, iterations)

            self.assertEqual(res["portfolio_id"], portfolio_id)
            self.assertEqual(res["initial_value"], portfolio_value)
            self.assertEqual(res["iterations"], iterations)
            self.assertIn("var_95", res)
            self.assertIn("expected_shortfall", res)
            self.assertIn("simulation_id", res)
            mock_log.assert_called_once()
            mock_vis.assert_called_once()

    def test_run_monte_carlo_stress_test_invalid_iterations(self):
        portfolio_id = f"port_{uuid.uuid4().hex}"
        portfolio_value = float(random.randint(10000, 50000))
        iterations = random.choice([0, -random.randint(1, 10)])
        scenario_params = {}

        with self.assertRaises(ValueError):
            run_monte_carlo_stress_test(portfolio_id, portfolio_value, scenario_params, iterations)