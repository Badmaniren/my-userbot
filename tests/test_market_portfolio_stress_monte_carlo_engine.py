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

    def test_run_simulation_success(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        initial_val = float(random.randint(10000, 500000))
        simulations_count = random.randint(10, 50)
        horizon = random.randint(1, 10)

        mock_portfolio = {
            "portfolio_id": portfolio_id,
            "initial_value": initial_val,
            "volatility": 0.15,
            "drift": 0.02
        }

        with patch("skills.db_storage.fetch_portfolio", return_value=mock_portfolio):
            engine = MonteCarloStressEngine()
            result = engine.run_simulation(portfolio_id, simulations_count, horizon)

            self.assertIn("portfolio_id", result)
            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertIn("simulation_results", result)
            self.assertEqual(len(result["simulation_results"]), simulations_count)
            self.assertIn("var_95", result)
            self.assertIn("cvar_95", result)
            self.assertIsInstance(result["var_95"], float)
            self.assertIsInstance(result["cvar_95"], float)

    def test_run_simulation_fallback_db(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        initial_val = float(random.randint(20000, 100000))
        simulations_count = random.randint(10, 30)
        horizon = random.randint(1, 5)

        with patch("skills.db_storage.fetch_portfolio", side_effect=AttributeError("No fetch_portfolio")):
            with patch("skills.db_storage._in_memory_db", {portfolio_id: {"initial_value": initial_val}}, create=True):
                engine = MonteCarloStressEngine()
                result = engine.run_simulation(portfolio_id, simulations_count, horizon)

                self.assertEqual(result["portfolio_id"], portfolio_id)
                self.assertEqual(len(result["simulation_results"]), simulations_count)
                self.assertIsInstance(result["var_95"], float)
                self.assertIsInstance(result["cvar_95"], float)

    def test_get_anomaly_adjustment_with_detector(self):
        engine = MonteCarloStressEngine()
        mult = float(random.randint(11, 20)) / 10.0
        with patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", return_value=mult):
            res = engine._get_anomaly_adjustment()
            self.assertEqual(res, mult)

    def test_get_anomaly_adjustment_fallback(self):
        engine = MonteCarloStressEngine()
        with patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", side_effect=AttributeError):
            res = engine._get_anomaly_adjustment()
            self.assertEqual(res, 1.0)

    def test_export_report_success(self):
        engine = MonteCarloStressEngine()
        report_id = f"rep_{uuid.uuid4().hex[:8]}"
        loss_limit = float(random.randint(1000, 5000))

        expected = {"report_id": report_id, "loss_limit": loss_limit, "status": "exported"}
        with patch("skills.market_portfolio_data_exporter.export", return_value=expected) as mock_export:
            res = engine.export_report(report_id, loss_limit)
            mock_export.assert_called_once_with(report_id, loss_limit)
            self.assertEqual(res, expected)

    def test_export_report_fallback(self):
        engine = MonteCarloStressEngine()
        report_id = f"rep_{uuid.uuid4().hex[:8]}"
        loss_limit = float(random.randint(1000, 5000))

        with patch("skills.market_portfolio_data_exporter.export", side_effect=AttributeError):
            res = engine.export_report(report_id, loss_limit)
            self.assertEqual(res["report_id"], report_id)
            self.assertEqual(res["loss_limit"], loss_limit)

    def test_consume_stream_success(self):
        engine = MonteCarloStressEngine()
        payload = {"stream_id": uuid.uuid4().hex, "data": random.randint(1, 100)}
        with patch("skills.market_portfolio_api_gateway.stream_payload", return_value=payload):
            res = engine.consume_stream()
            self.assertEqual(res, payload)

    def test_consume_stream_fallback(self):
        engine = MonteCarloStressEngine()
        with patch("skills.market_portfolio_api_gateway.stream_payload", side_effect=AttributeError):
            res = engine.consume_stream()
            self.assertIsNone(res)

    def test_run_monte_carlo_stress_test_standalone(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        portfolio_val = float(random.randint(50000, 200000))
        iterations = random.randint(15, 45)
        scenario_params = {
            "volatility": 0.25,
            "drift": 0.01,
            "horizon_days": random.randint(1, 5)
        }

        res = run_monte_carlo_stress_test(portfolio_id, portfolio_val, scenario_params, iterations)

        self.assertIn("simulation_id", res)
        self.assertEqual(res["portfolio_id"], portfolio_id)
        self.assertEqual(res["initial_value"], portfolio_val)
        self.assertEqual(res["iterations"], iterations)
        self.assertIsInstance(res["var_95"], float)
        self.assertIsInstance(res["expected_shortfall"], float)


if __name__ == "__main__":
    unittest.main()