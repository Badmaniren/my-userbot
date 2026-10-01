import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import math

from skills.market_portfolio_stress_monte_carlo_engine import (
    MonteCarloStressEngine,
    run_monte_carlo_stress_test
)


class TestMonteCarloStressEngine(unittest.TestCase):

    def setUp(self):
        self.engine = MonteCarloStressEngine()
        self.portfolio_id = uuid.uuid4().hex
        self.simulations = random.randint(10, 50)
        self.horizon_days = random.randint(5, 30)
        self.report_id = uuid.uuid4().hex
        self.loss_limit = round(random.uniform(1000.0, 50000.0), 2)

    def test_run_simulation_with_db_storage(self):
        initial_value = round(random.uniform(50000.0, 200000.0), 2)
        volatility = round(random.uniform(0.1, 0.5), 2)
        drift = round(random.uniform(-0.05, 0.05), 2)

        mock_portfolio_data = {
            "portfolio_id": self.portfolio_id,
            "initial_value": initial_value,
            "volatility": volatility,
            "drift": drift
        }

        with patch("skills.db_storage.fetch_portfolio", return_value=mock_portfolio_data) as mock_fetch, \
             patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", return_value=1.0) as mock_anomaly:

            result = self.engine.run_simulation(self.portfolio_id, self.simulations, self.horizon_days)

            mock_fetch.assert_called_once_with(self.portfolio_id)
            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertIn("simulation_results", result)
            self.assertIn("var_95", result)
            self.assertIn("cvar_95", result)
            self.assertEqual(len(result["simulation_results"]), self.simulations)
            for path in result["simulation_results"]:
                self.assertEqual(len(path), self.horizon_days)

    def test_run_simulation_fallback_in_memory(self):
        initial_value = round(random.uniform(10000.0, 50000.0), 2)
        in_memory_data = {
            self.portfolio_id: {
                "portfolio_id": self.portfolio_id,
                "initial_value": initial_value,
                "volatility": 0.25,
                "drift": 0.01
            }
        }

        with patch("skills.db_storage.fetch_portfolio", side_effect=AttributeError), \
             patch("skills.db_storage._in_memory_db", in_memory_data, create=True), \
             patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", return_value=1.2):

            result = self.engine.run_simulation(self.portfolio_id, self.simulations, self.horizon_days)

            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertEqual(len(result["simulation_results"]), self.simulations)
            self.assertIsInstance(result["var_95"], float)
            self.assertIsInstance(result["cvar_95"], float)

    def test_export_report_success(self):
        expected_export_result = {
            "report_id": self.report_id,
            "status": uuid.uuid4().hex,
            "loss_limit": self.loss_limit
        }

        with patch("skills.market_portfolio_data_exporter.export", create=True, return_value=expected_export_result) as mock_export:
            result = self.engine.export_report(self.report_id, self.loss_limit)
            mock_export.assert_called_once_with(self.report_id, self.loss_limit)
            self.assertEqual(result, expected_export_result)

    def test_export_report_fallback(self):
        with patch("skills.market_portfolio_data_exporter.export", create=True, side_effect=AttributeError):
            result = self.engine.export_report(self.report_id, self.loss_limit)
            self.assertEqual(result["report_id"], self.report_id)
            self.assertEqual(result["loss_limit"], self.loss_limit)

    def test_consume_stream_success(self):
        payload_data = {
            "stream_id": uuid.uuid4().hex,
            "data": uuid.uuid4().hex
        }

        with patch("skills.market_portfolio_api_gateway.stream_payload", create=True, return_value=payload_data) as mock_stream:
            result = self.engine.consume_stream()
            mock_stream.assert_called_once()
            self.assertEqual(result, payload_data)

    def test_consume_stream_fallback(self):
        with patch("skills.market_portfolio_api_gateway.stream_payload", create=True, side_effect=AttributeError):
            result = self.engine.consume_stream()
            self.assertIsNone(result)

    def test_run_monte_carlo_stress_test_standalone(self):
        portfolio_value = round(random.uniform(50000.0, 500000.0), 2)
        scenario_params = {
            "volatility": round(random.uniform(0.15, 0.45), 2),
            "drift": round(random.uniform(-0.02, 0.02), 2),
            "horizon_days": random.randint(1, 10)
        }
        iterations = random.randint(20, 100)

        result = run_monte_carlo_stress_test(
            portfolio_id=self.portfolio_id,
            portfolio_value=portfolio_value,
            scenario_params=scenario_params,
            iterations=iterations
        )

        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["initial_value"], portfolio_value)
        self.assertEqual(result["iterations"], iterations)
        self.assertIn("simulation_id", result)
        self.assertTrue(result["simulation_id"].startswith("sim_"))
        self.assertIsInstance(result["var_95"], float)
        self.assertIsInstance(result["expected_shortfall"], float)


if __name__ == "__main__":
    unittest.main()