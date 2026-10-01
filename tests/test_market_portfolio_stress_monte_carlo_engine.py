import unittest
from unittest.mock import patch
import uuid
import random

from skills.market_portfolio_stress_monte_carlo_engine import (
    MonteCarloStressEngine,
    run_monte_carlo_stress_test
)


class TestMonteCarloStressEngine(unittest.TestCase):

    def test_run_simulation_success(self):
        rand_portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        rand_init_val = float(random.randint(50000, 150000))
        rand_vol = round(random.uniform(0.1, 0.4), 2)
        rand_drift = round(random.uniform(-0.05, 0.05), 4)

        simulations_count = random.randint(10, 50)
        horizon_days = random.randint(5, 15)

        mock_portfolio_data = {
            "portfolio_id": rand_portfolio_id,
            "initial_value": rand_init_val,
            "volatility": rand_vol,
            "drift": rand_drift
        }

        with patch("skills.db_storage.fetch_portfolio", return_value=mock_portfolio_data) as mock_fetch, \
             patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", return_value=1.0) as mock_anomaly:
            
            engine = MonteCarloStressEngine()
            result = engine.run_simulation(rand_portfolio_id, simulations_count, horizon_days)

            mock_fetch.assert_called_once_with(rand_portfolio_id)
            mock_anomaly.assert_called_once()

            self.assertIn("portfolio_id", result)
            self.assertEqual(result["portfolio_id"], rand_portfolio_id)
            self.assertIn("simulation_results", result)
            self.assertEqual(len(result["simulation_results"]), simulations_count)
            for path in result["simulation_results"]:
                self.assertEqual(len(path), horizon_days)
            self.assertIn("var_95", result)
            self.assertIn("cvar_95", result)
            self.assertIsInstance(result["var_95"], float)
            self.assertIsInstance(result["cvar_95"], float)

    def test_run_simulation_fallback_db(self):
        rand_portfolio_id = f"fallback_{uuid.uuid4().hex[:8]}"
        simulations_count = random.randint(5, 20)
        horizon_days = random.randint(3, 10)

        with patch("skills.db_storage.fetch_portfolio", side_effect=AttributeError("No fetch_portfolio")):
            engine = MonteCarloStressEngine()
            result = engine.run_simulation(rand_portfolio_id, simulations_count, horizon_days)

            self.assertEqual(result["portfolio_id"], rand_portfolio_id)
            self.assertEqual(len(result["simulation_results"]), simulations_count)

    def test_get_anomaly_adjustment_exception(self):
        with patch("skills.market_anomaly_detector.get_current_anomaly_multiplier", side_effect=AttributeError("No attr")):
            engine = MonteCarloStressEngine()
            mult = engine._get_anomaly_adjustment()
            self.assertEqual(mult, 1.0)

    def test_export_report_success(self):
        rand_report_id = f"rep_{uuid.uuid4().hex[:8]}"
        rand_limit = float(random.randint(1000, 10000))

        expected_response = {"report_id": rand_report_id, "loss_limit": rand_limit, "status": "exported"}

        with patch("skills.market_portfolio_data_exporter.export", return_value=expected_response) as mock_export:
            engine = MonteCarloStressEngine()
            res = engine.export_report(rand_report_id, rand_limit)

            mock_export.assert_called_once_with(rand_report_id, rand_limit)
            self.assertEqual(res, expected_response)

    def test_export_report_exception(self):
        rand_report_id = f"rep_err_{uuid.uuid4().hex[:8]}"
        rand_limit = float(random.randint(500, 5000))

        with patch("skills.market_portfolio_data_exporter.export", side_effect=AttributeError("No export")):
            engine = MonteCarloStressEngine()
            res = engine.export_report(rand_report_id, rand_limit)

            self.assertEqual(res, {"report_id": rand_report_id, "loss_limit": rand_limit})

    def test_consume_stream_success(self):
        rand_payload = {"stream_id": uuid.uuid4().hex, "data": random.randint(1, 100)}

        with patch("skills.market_portfolio_api_gateway.stream_payload", return_value=rand_payload) as mock_stream:
            engine = MonteCarloStressEngine()
            res = engine.consume_stream()

            mock_stream.assert_called_once()
            self.assertEqual(res, rand_payload)

    def test_consume_stream_exception(self):
        with patch("skills.market_portfolio_api_gateway.stream_payload", side_effect=AttributeError("No stream")):
            engine = MonteCarloStressEngine()
            res = engine.consume_stream()

            self.assertIsNone(res)

    def test_run_monte_carlo_stress_test_functional(self):
        rand_portfolio_id = f"func_port_{uuid.uuid4().hex[:8]}"
        rand_portfolio_val = float(random.randint(10000, 500000))
        iterations = random.randint(10, 30)

        scenario_params = {
            "volatility": round(random.uniform(0.15, 0.35), 2),
            "drift": round(random.uniform(-0.02, 0.02), 4),
            "horizon_days": random.randint(1, 7)
        }

        result = run_monte_carlo_stress_test(
            portfolio_id=rand_portfolio_id,
            portfolio_value=rand_portfolio_val,
            scenario_params=scenario_params,
            iterations=iterations
        )

        self.assertIn("simulation_id", result)
        self.assertTrue(result["simulation_id"].startswith("sim_"))
        self.assertEqual(result["portfolio_id"], rand_portfolio_id)
        self.assertEqual(result["initial_value"], rand_portfolio_val)
        self.assertEqual(result["iterations"], iterations)
        self.assertIsInstance(result["var_95"], float)
        self.assertIsInstance(result["expected_shortfall"], float)


if __name__ == "__main__":
    unittest.main()