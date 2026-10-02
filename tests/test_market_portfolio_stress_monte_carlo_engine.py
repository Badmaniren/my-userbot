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
        self.engine = MonteCarloStressEngine()
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.simulations = random.randint(50, 150)
        self.horizon_days = random.randint(5, 30)
        self.initial_value = random.uniform(50000.0, 500000.0)
        self.volatility = random.uniform(0.1, 0.5)
        self.drift = random.uniform(-0.05, 0.05)

    def test_run_simulation_with_database_storage(self):
        portfolio_data = {
            "portfolio_id": self.portfolio_id,
            "initial_value": self.initial_value,
            "volatility": self.volatility,
            "drift": self.drift
        }

        with patch("skills.db_storage.fetch_portfolio", return_value=portfolio_data) as mock_fetch, \
             patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", return_value=1.1) as mock_anomaly:

            result = self.engine.run_simulation(self.portfolio_id, self.simulations, self.horizon_days)

            mock_fetch.assert_called_once_with(self.portfolio_id)
            mock_anomaly.assert_called_once()

            self.assertIn("portfolio_id", result)
            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertIn("simulation_results", result)
            self.assertEqual(len(result["simulation_results"]), self.simulations)
            self.assertIn("var_95", result)
            self.assertIn("cvar_95", result)
            self.assertIsInstance(result["var_95"], float)
            self.assertIsInstance(result["cvar_95"], float)

    def test_run_simulation_fallback_in_memory(self):
        random_key = uuid.uuid4().hex
        in_memory_mock = {
            random_key: {
                "portfolio_id": random_key,
                "initial_value": self.initial_value,
                "volatility": self.volatility,
                "drift": self.drift
            }
        }

        with patch("skills.db_storage.fetch_portfolio", side_effect=AttributeError), \
             patch("skills.db_storage._in_memory_db", in_memory_mock, create=True):

            result = self.engine.run_simulation(random_key, self.simulations, self.horizon_days)

            self.assertEqual(result["portfolio_id"], random_key)
            self.assertEqual(len(result["simulation_results"]), self.simulations)

    def test_get_anomaly_adjustment_exception_handling(self):
        with patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", side_effect=AttributeError):
            adjustment = self.engine._get_anomaly_adjustment()
            self.assertEqual(adjustment, 1.0)

    def test_export_report_success_and_fallback(self):
        report_id = f"rep_{uuid.uuid4().hex[:6]}"
        loss_limit = random.uniform(1000.0, 10000.0)

        with patch("skills.market_portfolio_data_exporter.export", return_value={"status": "success", "id": report_id}) as mock_export:
            res = self.engine.export_report(report_id, loss_limit)
            mock_export.assert_called_once_with(report_id, loss_limit)
            self.assertEqual(res["id"], report_id)

        with patch("skills.market_portfolio_data_exporter.export", side_effect=AttributeError):
            res_fallback = self.engine.export_report(report_id, loss_limit)
            self.assertEqual(res_fallback["report_id"], report_id)
            self.assertEqual(res_fallback["loss_limit"], loss_limit)

    def test_consume_stream_success_and_fallback(self):
        stream_data = io.BytesIO(uuid.uuid4().bytes)

        with patch("skills.market_portfolio_api_gateway.stream_payload", return_value=stream_data) as mock_stream:
            res = self.engine.consume_stream()
            mock_stream.assert_called_once()
            self.assertEqual(res, stream_data)

        with patch("skills.market_portfolio_api_gateway.stream_payload", side_effect=AttributeError):
            res_fallback = self.engine.consume_stream()
            self.assertIsNone(res_fallback)


class TestRunMonteCarloStressTestFunction(unittest.TestCase):

    def test_run_monte_carlo_stress_test_execution(self):
        portfolio_id = f"pid_{uuid.uuid4().hex[:8]}"
        portfolio_value = random.uniform(10000.0, 1000000.0)
        iterations = random.randint(30, 100)
        scenario_params = {
            "volatility": random.uniform(0.05, 0.4),
            "drift": random.uniform(-0.02, 0.02),
            "horizon_days": random.randint(1, 10)
        }

        result = run_monte_carlo_stress_test(
            portfolio_id=portfolio_id,
            portfolio_value=portfolio_value,
            scenario_params=scenario_params,
            iterations=iterations
        )

        self.assertIn("simulation_id", result)
        self.assertTrue(result["simulation_id"].startswith("sim_"))
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["initial_value"], portfolio_value)
        self.assertEqual(result["iterations"], iterations)
        self.assertIsInstance(result["var_95"], float)
        self.assertIsInstance(result["expected_shortfall"], float)


if __name__ == "__main__":
    unittest.main()