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

    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.report_id = uuid.uuid4().hex
        self.loss_limit = round(random.uniform(1000.0, 50000.0), 2)
        self.simulations = random.randint(10, 50)
        self.horizon_days = random.randint(1, 10)
        self.portfolio_value = round(random.uniform(50000.0, 500000.0), 2)
        self.volatility = round(random.uniform(0.1, 0.5), 4)
        self.drift = round(random.uniform(-0.05, 0.05), 4)
        self.iterations = random.randint(10, 50)

    def test_run_simulation_success(self):
        engine = MonteCarloStressEngine()
        mock_portfolio_data = {
            "portfolio_id": self.portfolio_id,
            "initial_value": self.portfolio_value,
            "volatility": self.volatility,
            "drift": self.drift
        }
        mock_anomaly_mult = round(random.uniform(0.8, 2.0), 2)

        with patch("skills.db_storage.fetch_portfolio", return_value=mock_portfolio_data) as mock_fetch, \
             patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", return_value=mock_anomaly_mult) as mock_anomaly:

            result = engine.run_simulation(self.portfolio_id, self.simulations, self.horizon_days)

            mock_fetch.assert_called_once_with(self.portfolio_id)
            mock_anomaly.assert_called_once()

            self.assertIsInstance(result, dict)
            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertIn("simulation_results", result)
            self.assertIn("var_95", result)
            self.assertIn("cvar_95", result)
            self.assertEqual(len(result["simulation_results"]), self.simulations)
            self.assertIsInstance(result["var_95"], float)
            self.assertIsInstance(result["cvar_95"], float)

    def test_run_simulation_fallback(self):
        engine = MonteCarloStressEngine()
        mock_anomaly_mult = round(random.uniform(0.5, 1.5), 2)

        with patch("skills.db_storage.fetch_portfolio", side_effect=AttributeError("No such method")) as mock_fetch, \
             patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", return_value=mock_anomaly_mult) as mock_anomaly:

            result = engine.run_simulation(self.portfolio_id, self.simulations, self.horizon_days)

            mock_fetch.assert_called_once_with(self.portfolio_id)
            self.assertIsInstance(result, dict)
            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertIn("simulation_results", result)
            self.assertIn("var_95", result)
            self.assertIn("cvar_95", result)

    def test_get_anomaly_adjustment_fallback(self):
        engine = MonteCarloStressEngine()

        with patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", side_effect=AttributeError("Missing")):
            mult = engine._get_anomaly_adjustment()
            self.assertEqual(mult, 1.0)

    def test_export_report_success(self):
        engine = MonteCarloStressEngine()
        expected_response = {
            "report_id": self.report_id,
            "loss_limit": self.loss_limit,
            "status": uuid.uuid4().hex
        }

        with patch("skills.market_portfolio_data_exporter.export", return_value=expected_response) as mock_export:
            res = engine.export_report(self.report_id, self.loss_limit)
            mock_export.assert_called_once_with(self.report_id, self.loss_limit)
            self.assertEqual(res, expected_response)

    def test_export_report_fallback(self):
        engine = MonteCarloStressEngine()

        with patch("skills.market_portfolio_data_exporter.export", side_effect=AttributeError("Missing")):
            res = engine.export_report(self.report_id, self.loss_limit)
            self.assertEqual(res, {"report_id": self.report_id, "loss_limit": self.loss_limit})

    def test_consume_stream_success(self):
        engine = MonteCarloStressEngine()
        stream_data = uuid.uuid4().hex.encode('utf-8')
        stream_mock = io.BytesIO(stream_data)

        with patch("skills.market_portfolio_api_gateway.stream_payload", return_value=stream_mock) as mock_stream:
            res = engine.consume_stream()
            mock_stream.assert_called_once()
            self.assertEqual(res, stream_mock)

    def test_consume_stream_fallback(self):
        engine = MonteCarloStressEngine()

        with patch("skills.market_portfolio_api_gateway.stream_payload", side_effect=AttributeError("Missing")):
            res = engine.consume_stream()
            self.assertIsNone(res)

    def test_run_monte_carlo_stress_test(self):
        scenario_params = {
            "volatility": self.volatility,
            "drift": self.drift,
            "horizon_days": self.horizon_days
        }

        result = run_monte_carlo_stress_test(
            self.portfolio_id,
            self.portfolio_value,
            scenario_params,
            self.iterations
        )

        self.assertIsInstance(result, dict)
        self.assertTrue(result["simulation_id"].startswith("sim_"))
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["initial_value"], self.portfolio_value)
        self.assertEqual(result["iterations"], self.iterations)
        self.assertIsInstance(result["var_95"], float)
        self.assertIsInstance(result["expected_shortfall"], float)


if __name__ == "__main__":
    unittest.main()