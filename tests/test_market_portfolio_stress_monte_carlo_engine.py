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

    def test_run_simulation_calculates_metrics_correctly(self):
        portfolio_id = uuid.uuid4().hex
        simulations = random.randint(50, 150)
        horizon_days = random.randint(5, 15)
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
             patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", return_value=1.0) as mock_anomaly:

            engine = MonteCarloStressEngine()
            result = engine.run_simulation(portfolio_id, simulations, horizon_days)

            mock_fetch.assert_called_once_with(portfolio_id)
            mock_anomaly.assert_called_once()

            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertIn("simulation_results", result)
            self.assertIn("var_95", result)
            self.assertIn("cvar_95", result)
            self.assertEqual(len(result["simulation_results"]), simulations)
            for path in result["simulation_results"]:
                self.assertEqual(len(path), horizon_days)
            self.assertIsInstance(result["var_95"], float)
            self.assertIsInstance(result["cvar_95"], float)

    def test_run_simulation_fallback_db_storage(self):
        portfolio_id = uuid.uuid4().hex
        simulations = random.randint(10, 30)
        horizon_days = random.randint(2, 5)

        with patch("skills.db_storage.fetch_portfolio", side_effect=AttributeError), \
             patch("skills.db_storage._in_memory_db", {portfolio_id: {"portfolio_id": portfolio_id, "initial_value": 75000.0}}):

            engine = MonteCarloStressEngine()
            result = engine.run_simulation(portfolio_id, simulations, horizon_days)

            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertEqual(len(result["simulation_results"]), simulations)

    def test_export_report_calls_exporter(self):
        report_id = uuid.uuid4().hex
        loss_limit = random.uniform(1000.0, 50000.0)
        expected_export_result = {"report_id": report_id, "loss_limit": loss_limit, "status": "exported"}

        with patch("skills.market_portfolio_data_exporter.export", return_value=expected_export_result) as mock_export:
            engine = MonteCarloStressEngine()
            result = engine.export_report(report_id, loss_limit)

            mock_export.assert_called_once_with(report_id, loss_limit)
            self.assertEqual(result, expected_export_result)

    def test_export_report_fallback(self):
        report_id = uuid.uuid4().hex
        loss_limit = random.uniform(1000.0, 50000.0)

        with patch("skills.market_portfolio_data_exporter.export", side_effect=AttributeError):
            engine = MonteCarloStressEngine()
            result = engine.export_report(report_id, loss_limit)

            self.assertEqual(result["report_id"], report_id)
            self.assertEqual(result["loss_limit"], loss_limit)

    def test_consume_stream_calls_gateway(self):
        stream_data = io.BytesIO(uuid.uuid4().bytes)

        with patch("skills.market_portfolio_api_gateway.stream_payload", return_value=stream_data) as mock_stream:
            engine = MonteCarloStressEngine()
            result = engine.consume_stream()

            mock_stream.assert_called_once()
            self.assertEqual(result, stream_data)

    def test_consume_stream_fallback(self):
        with patch("skills.market_portfolio_api_gateway.stream_payload", side_effect=AttributeError):
            engine = MonteCarloStressEngine()
            result = engine.consume_stream()

            self.assertIsNone(result)

    def test_run_monte_carlo_stress_test_standalone(self):
        portfolio_id = uuid.uuid4().hex
        portfolio_value = random.uniform(10000.0, 500000.0)
        iterations = random.randint(20, 100)
        scenario_params = {
            "volatility": random.uniform(0.15, 0.35),
            "drift": random.uniform(-0.02, 0.02),
            "horizon_days": random.randint(1, 10)
        }

        result = run_monte_carlo_stress_test(portfolio_id, portfolio_value, scenario_params, iterations)

        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["initial_value"], portfolio_value)
        self.assertEqual(result["iterations"], iterations)
        self.assertIn("simulation_id", result)
        self.assertTrue(result["simulation_id"].startswith("sim_"))
        self.assertIsInstance(result["var_95"], float)
        self.assertIsInstance(result["expected_shortfall"], float)


if __name__ == "__main__":
    unittest.main()