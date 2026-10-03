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


class TestMonteCarloStressEngine(unittest.TestCase):

    def test_run_simulation_success(self):
        portfolio_id = uuid.uuid4().hex
        simulations = random.randint(10, 50)
        horizon_days = random.randint(5, 15)
        initial_value = float(random.randint(50000, 200000))
        volatility = round(random.uniform(0.1, 0.4), 2)
        drift = round(random.uniform(-0.05, 0.05), 2)

        portfolio_data = {
            "portfolio_id": portfolio_id,
            "initial_value": initial_value,
            "volatility": volatility,
            "drift": drift
        }

        with patch("skills.db_storage.fetch_portfolio", return_value=portfolio_data) as mock_fetch, \
             patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", return_value=1.0) as mock_anomaly:

            engine = MonteCarloStressEngine()
            result = engine.run_simulation(portfolio_id, simulations, horizon_days)

            mock_fetch.assert_called_once_with(portfolio_id)
            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertEqual(len(result["simulation_results"]), simulations)
            self.assertIn("var_95", result)
            self.assertIn("cvar_95", result)
            self.assertIsInstance(result["var_95"], float)
            self.assertIsInstance(result["cvar_95"], float)

    def test_run_simulation_fallback_db(self):
        portfolio_id = uuid.uuid4().hex
        simulations = random.randint(5, 20)
        horizon_days = random.randint(3, 10)

        with patch("skills.db_storage.fetch_portfolio", side_effect=AttributeError), \
             patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", return_value=1.0):

            engine = MonteCarloStressEngine()
            result = engine.run_simulation(portfolio_id, simulations, horizon_days)

            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertEqual(len(result["simulation_results"]), simulations)

    def test_get_anomaly_adjustment_attribute_error(self):
        with patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", side_effect=AttributeError):
            engine = MonteCarloStressEngine()
            adj = engine._get_anomaly_adjustment()
            self.assertEqual(adj, 1.0)

    def test_export_report_success(self):
        report_id = uuid.uuid4().hex
        loss_limit = float(random.randint(1000, 10000))
        expected_export = {"report_id": report_id, "status": uuid.uuid4().hex}

        with patch("skills.market_portfolio_data_exporter.export", create=True, return_value=expected_export) as mock_export:
            engine = MonteCarloStressEngine()
            result = engine.export_report(report_id, loss_limit)
            mock_export.assert_called_once_with(report_id, loss_limit)
            self.assertEqual(result, expected_export)

    def test_export_report_attribute_error(self):
        report_id = uuid.uuid4().hex
        loss_limit = float(random.randint(1000, 10000))

        with patch("skills.market_portfolio_data_exporter.export", create=True, side_effect=AttributeError):
            engine = MonteCarloStressEngine()
            result = engine.export_report(report_id, loss_limit)
            self.assertEqual(result["report_id"], report_id)
            self.assertEqual(result["loss_limit"], loss_limit)

    def test_consume_stream_success(self):
        stream_data = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))

        with patch("skills.market_portfolio_api_gateway.stream_payload", create=True, return_value=stream_data) as mock_stream:
            engine = MonteCarloStressEngine()
            result = engine.consume_stream()
            mock_stream.assert_called_once()
            self.assertEqual(result, stream_data)

    def test_consume_stream_attribute_error(self):
        with patch("skills.market_portfolio_api_gateway.stream_payload", create=True, side_effect=AttributeError):
            engine = MonteCarloStressEngine()
            result = engine.consume_stream()
            self.assertIsNone(result)

    def test_run_monte_carlo_stress_test_standalone(self):
        portfolio_id = uuid.uuid4().hex
        portfolio_value = float(random.randint(10000, 500000))
        iterations = random.randint(10, 100)
        scenario_params = {
            "volatility": round(random.uniform(0.1, 0.5), 2),
            "drift": round(random.uniform(-0.1, 0.1), 2),
            "horizon_days": random.randint(1, 10)
        }

        result = run_monte_carlo_stress_test(portfolio_id, portfolio_value, scenario_params, iterations)

        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["initial_value"], portfolio_value)
        self.assertEqual(result["iterations"], iterations)
        self.assertIn("simulation_id", result)
        self.assertIn("var_95", result)
        self.assertIn("expected_shortfall", result)
        self.assertIsInstance(result["var_95"], float)
        self.assertIsInstance(result["expected_shortfall"], float)