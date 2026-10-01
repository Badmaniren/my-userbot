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
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.report_id = f"rep_{uuid.uuid4().hex[:8]}"
        self.loss_limit = round(random.uniform(5000.0, 50000.0), 2)
        self.simulations = random.randint(10, 50)
        self.horizon_days = random.randint(5, 30)
        self.initial_value = round(random.uniform(50000.0, 200000.0), 2)
        self.volatility = round(random.uniform(0.1, 0.5), 4)
        self.drift = round(random.uniform(-0.05, 0.05), 4)

    def test_run_simulation_with_db_storage(self):
        mock_portfolio_data = {
            "portfolio_id": self.portfolio_id,
            "initial_value": self.initial_value,
            "volatility": self.volatility,
            "drift": self.drift
        }

        with patch("skills.db_storage.fetch_portfolio", return_value=mock_portfolio_data) as mock_fetch, \
             patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", return_value=1.0) as mock_anomaly:

            result = self.engine.run_simulation(self.portfolio_id, self.simulations, self.horizon_days)

            mock_fetch.assert_called_once_with(self.portfolio_id)
            mock_anomaly.assert_called_once()

            self.assertIsInstance(result, dict)
            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertIn("simulation_results", result)
            self.assertIn("var_95", result)
            self.assertIn("cvar_95", result)
            self.assertEqual(len(result["simulation_results"]), self.simulations)
            for path in result["simulation_results"]:
                self.assertEqual(len(path), self.horizon_days)

    def test_run_simulation_fallback_in_memory_db(self):
        fallback_data = {
            "portfolio_id": self.portfolio_id,
            "initial_value": self.initial_value,
            "volatility": self.volatility,
            "drift": self.drift
        }

        with patch("skills.db_storage.fetch_portfolio", side_effect=AttributeError), \
             patch("skills.db_storage._in_memory_db", {self.portfolio_id: fallback_data}, create=True) as mock_mem_db:

            result = self.engine.run_simulation(self.portfolio_id, self.simulations, self.horizon_days)

            self.assertIsInstance(result, dict)
            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertEqual(len(result["simulation_results"]), self.simulations)

    def test_get_anomaly_adjustment_success(self):
        expected_mult = round(random.uniform(1.1, 2.5), 2)
        with patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", return_value=expected_mult) as mock_anomaly:
            mult = self.engine._get_anomaly_adjustment()
            mock_anomaly.assert_called_once()
            self.assertEqual(mult, expected_mult)

    def test_get_anomaly_adjustment_attribute_error(self):
        with patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", side_effect=AttributeError):
            mult = self.engine._get_anomaly_adjustment()
            self.assertEqual(mult, 1.0)

    def test_export_report_success(self):
        expected_export = {
            "report_id": self.report_id,
            "loss_limit": self.loss_limit,
            "status": uuid.uuid4().hex
        }
        with patch("skills.market_portfolio_data_exporter.export", return_value=expected_export) as mock_export:
            res = self.engine.export_report(self.report_id, self.loss_limit)
            mock_export.assert_called_once_with(self.report_id, self.loss_limit)
            self.assertEqual(res, expected_export)

    def test_export_report_attribute_error(self):
        with patch("skills.market_portfolio_data_exporter.export", side_effect=AttributeError):
            res = self.engine.export_report(self.report_id, self.loss_limit)
            self.assertEqual(res, {"report_id": self.report_id, "loss_limit": self.loss_limit})

    def test_consume_stream_success(self):
        stream_payload_mock = {"payload_id": uuid.uuid4().hex, "data": random.randint(100, 999)}
        with patch("skills.market_portfolio_api_gateway.stream_payload", return_value=stream_payload_mock) as mock_stream:
            res = self.engine.consume_stream()
            mock_stream.assert_called_once()
            self.assertEqual(res, stream_payload_mock)

    def test_consume_stream_attribute_error(self):
        with patch("skills.market_portfolio_api_gateway.stream_payload", side_effect=AttributeError):
            res = self.engine.consume_stream()
            self.assertIsNone(res)

    def test_run_monte_carlo_stress_test_functional(self):
        iterations = random.randint(20, 60)
        scenario_params = {
            "volatility": self.volatility,
            "drift": self.drift,
            "horizon_days": self.horizon_days
        }

        result = run_monte_carlo_stress_test(
            portfolio_id=self.portfolio_id,
            portfolio_value=self.initial_value,
            scenario_params=scenario_params,
            iterations=iterations
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["initial_value"], self.initial_value)
        self.assertEqual(result["iterations"], iterations)
        self.assertIn("simulation_id", result)
        self.assertIn("var_95", result)
        self.assertIn("expected_shortfall", result)
        self.assertTrue(result["simulation_id"].startswith("sim_"))


if __name__ == "__main__":
    unittest.main()