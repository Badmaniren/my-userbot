import unittest
from unittest.mock import patch
import random
import uuid
import math
import io

from skills import market_portfolio_stress_monte_carlo_engine
from skills import market_anomaly_detector
from skills import market_portfolio_data_exporter
from skills import market_portfolio_api_gateway


class TestMonteCarloStressEngine(unittest.TestCase):

    def setUp(self):
        self.engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        self.portfolio_id = uuid.uuid4().hex
        self.simulations = random.randint(10, 50)
        self.horizon_days = random.randint(1, 10)
        self.initial_value = random.uniform(50000.0, 150000.0)
        self.volatility = random.uniform(0.1, 0.4)
        self.drift = random.uniform(-0.05, 0.05)

    def test_run_simulation_success(self):
        portfolio_data = {
            "portfolio_id": self.portfolio_id,
            "initial_value": self.initial_value,
            "volatility": self.volatility,
            "drift": self.drift
        }
        with patch("skills.db_storage.fetch_portfolio", return_value=portfolio_data) as mock_fetch:
            result = self.engine.run_simulation(self.portfolio_id, self.simulations, self.horizon_days)
            mock_fetch.assert_called_once_with(self.portfolio_id)
            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertIn("simulation_results", result)
            self.assertIn("var_95", result)
            self.assertIn("cvar_95", result)
            self.assertEqual(len(result["simulation_results"]), self.simulations)

    def test_run_simulation_attribute_error_fallback_db(self):
        with patch("skills.db_storage.fetch_portfolio", side_effect=AttributeError("No fetch_portfolio")):
            with patch("skills.db_storage._in_memory_db", {self.portfolio_id: {
                "portfolio_id": self.portfolio_id,
                "initial_value": self.initial_value,
                "volatility": self.volatility,
                "drift": self.drift
            }}, create=True):
                result = self.engine.run_simulation(self.portfolio_id, self.simulations, self.horizon_days)
                self.assertEqual(result["portfolio_id"], self.portfolio_id)
                self.assertIsInstance(result["var_95"], float)
                self.assertIsInstance(result["cvar_95"], float)

    def test_get_anomaly_adjustment_success(self):
        multiplier = random.uniform(1.0, 3.0)
        with patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", return_value=multiplier) as mock_detect:
            res = self.engine._get_anomaly_adjustment()
            mock_detect.assert_called_once()
            self.assertEqual(res, multiplier)

    def test_get_anomaly_adjustment_fallback(self):
        with patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", side_effect=AttributeError):
            res = self.engine._get_anomaly_adjustment()
            self.assertEqual(res, 1.0)

    def test_export_report_success(self):
        report_id = uuid.uuid4().hex
        loss_limit = random.uniform(1000.0, 10000.0)
        expected_ret = {"report_id": report_id, "loss_limit": loss_limit, "status": uuid.uuid4().hex}
        with patch("skills.market_portfolio_data_exporter.export", return_value=expected_ret) as mock_export:
            res = self.engine.export_report(report_id, loss_limit)
            mock_export.assert_called_once_with(report_id, loss_limit)
            self.assertEqual(res, expected_ret)

    def test_export_report_fallback(self):
        report_id = uuid.uuid4().hex
        loss_limit = random.uniform(1000.0, 10000.0)
        with patch("skills.market_portfolio_data_exporter.export", side_effect=AttributeError):
            res = self.engine.export_report(report_id, loss_limit)
            self.assertEqual(res["report_id"], report_id)
            self.assertEqual(res["loss_limit"], loss_limit)

    def test_consume_stream_success(self):
        payload = {"stream_id": uuid.uuid4().hex}
        with patch("skills.market_portfolio_api_gateway.stream_payload", return_value=payload) as mock_stream:
            res = self.engine.consume_stream()
            mock_stream.assert_called_once()
            self.assertEqual(res, payload)

    def test_consume_stream_fallback(self):
        with patch("skills.market_portfolio_api_gateway.stream_payload", side_effect=AttributeError):
            res = self.engine.consume_stream()
            self.assertIsNone(res)

    def test_run_monte_carlo_stress_test_standalone(self):
        scenario_params = {
            "volatility": self.volatility,
            "drift": self.drift,
            "horizon_days": self.horizon_days
        }
        iterations = random.randint(10, 30)
        res = market_portfolio_stress_monte_carlo_engine.run_monte_carlo_stress_test(
            self.portfolio_id,
            self.initial_value,
            scenario_params,
            iterations
        )
        self.assertEqual(res["portfolio_id"], self.portfolio_id)
        self.assertEqual(res["initial_value"], self.initial_value)
        self.assertEqual(res["iterations"], iterations)
        self.assertIn("simulation_id", res)
        self.assertIn("var_95", res)
        self.assertIn("expected_shortfall", res)


if __name__ == "__main__":
    unittest.main()