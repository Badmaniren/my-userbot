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

    def test_run_simulation_with_mocked_db_and_compliance(self):
        portfolio_id = uuid.uuid4().hex
        simulations = random.randint(10, 50)
        horizon_days = random.randint(1, 10)
        initial_value = random.uniform(50000.0, 150000.0)
        volatility = random.uniform(0.1, 0.4)
        drift = random.uniform(-0.05, 0.05)

        mock_portfolio_data = {
            "portfolio_id": portfolio_id,
            "initial_value": initial_value,
            "volatility": volatility,
            "drift": drift
        }

        with patch("skills.db_storage.fetch_portfolio", return_value=mock_portfolio_data) as mock_fetch, \
             patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", return_value=1.0) as mock_anomaly, \
             patch("skills.market_portfolio_audit_compliance_hub.log_simulation") as mock_log:

            engine = MonteCarloStressEngine()
            result = engine.run_simulation(portfolio_id=portfolio_id, simulations=simulations, horizon_days=horizon_days)

            mock_fetch.assert_called_once_with(portfolio_id)
            mock_anomaly.assert_called_once()
            mock_log.assert_called_once()

            self.assertIn("portfolio_id", result)
            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertIn("simulation_results", result)
            self.assertEqual(len(result["simulation_results"]), simulations)
            self.assertIn("var_95", result)
            self.assertIn("cvar_95", result)
            self.assertIsInstance(result["var_95"], float)
            self.assertIsInstance(result["cvar_95"], float)

    def test_run_simulation_attribute_error_fallback(self):
        portfolio_id = uuid.uuid4().hex
        simulations = 20
        horizon_days = 5
        initial_value = 100000.0

        with patch("skills.db_storage.fetch_portfolio", side_effect=AttributeError("No fetch_portfolio")), \
             patch("skills.db_storage._in_memory_db", {portfolio_id: {"initial_value": initial_value}}):

            engine = MonteCarloStressEngine()
            result = engine.run_simulation(portfolio_id=portfolio_id, simulations=simulations, horizon_days=horizon_days)

            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertEqual(len(result["simulation_results"]), simulations)
            self.assertGreaterEqual(result["var_95"], 0.0)

    def test_get_anomaly_adjustment_success_and_exception(self):
        engine = MonteCarloStressEngine()
        rand_mult = random.uniform(1.1, 2.5)

        with patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", return_value=rand_mult):
            val = engine._get_anomaly_adjustment()
            self.assertEqual(val, rand_mult)

        with patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", side_effect=AttributeError("Missing")):
            val_fallback = engine._get_anomaly_adjustment()
            self.assertEqual(val_fallback, 1.0)

    def test_export_report_success_and_exception(self):
        engine = MonteCarloStressEngine()
        report_id = uuid.uuid4().hex
        loss_limit = random.uniform(1000.0, 50000.0)
        expected_dict = {"report_id": report_id, "loss_limit": loss_limit, "status": uuid.uuid4().hex}

        with patch("skills.market_portfolio_data_exporter.export", return_value=expected_dict):
            res = engine.export_report(report_id, loss_limit)
            self.assertEqual(res, expected_dict)

        with patch("skills.market_portfolio_data_exporter.export", side_effect=AttributeError("Missing")):
            res_fallback = engine.export_report(report_id, loss_limit)
            self.assertEqual(res_fallback["report_id"], report_id)
            self.assertEqual(res_fallback["loss_limit"], loss_limit)

    def test_consume_stream_success_and_exception(self):
        engine = MonteCarloStressEngine()
        stream_data = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))

        with patch("skills.market_portfolio_api_gateway.stream_payload", return_value=stream_data):
            res = engine.consume_stream()
            self.assertEqual(res, stream_data)

        with patch("skills.market_portfolio_api_gateway.stream_payload", side_effect=AttributeError("Missing")):
            res_fallback = engine.consume_stream()
            self.assertIsNone(res_fallback)

    def test_run_monte_carlo_stress_test_functional(self):
        portfolio_id = uuid.uuid4().hex
        portfolio_value = random.uniform(10000.0, 500000.0)
        iterations = random.randint(15, 60)
        volatility = random.uniform(0.05, 0.5)
        drift = random.uniform(-0.02, 0.02)
        horizon_days = random.randint(1, 15)

        scenario_params = {
            "volatility": volatility,
            "drift": drift,
            "horizon_days": horizon_days
        }

        with patch("skills.market_portfolio_audit_compliance_hub.log_simulation") as mock_log:
            result = run_monte_carlo_stress_test(
                portfolio_id=portfolio_id,
                portfolio_value=portfolio_value,
                scenario_params=scenario_params,
                iterations=iterations
            )

            mock_log.assert_called_once()
            self.assertIn("simulation_id", result)
            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertEqual(result["initial_value"], portfolio_value)
            self.assertEqual(result["iterations"], iterations)
            self.assertIsInstance(result["var_95"], float)
            self.assertIsInstance(result["expected_shortfall"], float)