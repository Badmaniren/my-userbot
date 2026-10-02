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

    def test_run_simulation_with_in_memory_db(self):
        portfolio_id = uuid.uuid4().hex
        initial_value = float(random.randint(10000, 500000))
        volatility = random.uniform(0.1, 0.5)
        drift = random.uniform(-0.05, 0.05)
        simulations = random.randint(10, 50)
        horizon_days = random.randint(5, 30)

        custom_portfolio_data = {
            "portfolio_id": portfolio_id,
            "initial_value": initial_value,
            "volatility": volatility,
            "drift": drift
        }

        engine = MonteCarloStressEngine()

        with patch("skills.db_storage.fetch_portfolio", side_effect=AttributeError):
            with patch("skills.db_storage._in_memory_db", {portfolio_id: custom_portfolio_data}, create=True):
                result = engine.run_simulation(portfolio_id, simulations, horizon_days)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertIn("simulation_results", result)
        self.assertIn("var_95", result)
        self.assertIn("cvar_95", result)
        self.assertEqual(len(result["simulation_results"]), simulations)
        for path in result["simulation_results"]:
            self.assertEqual(len(path), horizon_days)

    def test_run_simulation_with_active_db_and_anomaly(self):
        portfolio_id = uuid.uuid4().hex
        initial_value = float(random.randint(50000, 200000))
        volatility = 0.2
        drift = 0.01
        simulations = 20
        horizon_days = 10
        anomaly_mult = random.uniform(1.1, 2.0)

        mock_db_data = {
            "portfolio_id": portfolio_id,
            "initial_value": initial_value,
            "volatility": volatility,
            "drift": drift
        }

        engine = MonteCarloStressEngine()

        with patch("skills.db_storage.fetch_portfolio", return_value=mock_db_data):
            with patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", return_value=anomaly_mult):
                result = engine.run_simulation(portfolio_id, simulations, horizon_days)

        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertIsInstance(result["var_95"], float)
        self.assertIsInstance(result["cvar_95"], float)

    def test_export_report_fallback(self):
        report_id = uuid.uuid4().hex
        loss_limit = float(random.randint(1000, 50000))

        engine = MonteCarloStressEngine()

        with patch("skills.market_portfolio_data_exporter.export", side_effect=AttributeError):
            res = engine.export_report(report_id, loss_limit)

        self.assertIsInstance(res, dict)
        self.assertEqual(res["report_id"], report_id)
        self.assertEqual(res["loss_limit"], loss_limit)

    def test_export_report_success(self):
        report_id = uuid.uuid4().hex
        loss_limit = float(random.randint(1000, 50000))
        expected_payload = {"report_id": report_id, "loss_limit": loss_limit, "status": uuid.uuid4().hex}

        engine = MonteCarloStressEngine()

        with patch("skills.market_portfolio_data_exporter.export", return_value=expected_payload) as mock_export:
            res = engine.export_report(report_id, loss_limit)
            mock_export.assert_called_once_with(report_id, loss_limit)

        self.assertEqual(res, expected_payload)

    def test_consume_stream_fallback(self):
        engine = MonteCarloStressEngine()

        with patch("skills.market_portfolio_api_gateway.stream_payload", side_effect=AttributeError):
            res = engine.consume_stream()

        self.assertIsNone(res)

    def test_consume_stream_success(self):
        expected_stream_data = {"stream_token": uuid.uuid4().hex}
        engine = MonteCarloStressEngine()

        with patch("skills.market_portfolio_api_gateway.stream_payload", return_value=expected_stream_data) as mock_stream:
            res = engine.consume_stream()
            mock_stream.assert_called_once()

        self.assertEqual(res, expected_stream_data)

    def test_run_monte_carlo_stress_test_function(self):
        portfolio_id = uuid.uuid4().hex
        portfolio_value = float(random.randint(100000, 1000000))
        iterations = random.randint(50, 150)
        
        scenario_params = {
            "volatility": random.uniform(0.1, 0.4),
            "drift": random.uniform(-0.02, 0.02),
            "horizon_days": random.randint(1, 15)
        }

        result = run_monte_carlo_stress_test(portfolio_id, portfolio_value, scenario_params, iterations)

        self.assertIsInstance(result, dict)
        self.assertTrue(result["simulation_id"].startswith("sim_"))
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["initial_value"], portfolio_value)
        self.assertEqual(result["iterations"], iterations)
        self.assertIsInstance(result["var_95"], float)
        self.assertIsInstance(result["expected_shortfall"], float)


if __name__ == "__main__":
    unittest.main()