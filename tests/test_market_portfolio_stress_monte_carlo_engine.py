import unittest
from unittest.mock import patch
import uuid
import random

from skills.market_portfolio_stress_monte_carlo_engine import (
    MonteCarloStressEngine,
    run_monte_carlo_stress_test
)


class TestMonteCarloStressEngine(unittest.TestCase):

    def test_run_simulation_success_and_invariants(self):
        engine = MonteCarloStressEngine()
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        simulations = random.randint(50, 150)
        horizon_days = random.randint(5, 15)

        with patch("skills.db_storage.fetch_portfolio") as mock_fetch:
            mock_fetch.return_value = {
                "portfolio_id": portfolio_id,
                "initial_value": float(random.randint(50000, 200000)),
                "volatility": float(random.uniform(0.1, 0.4)),
                "drift": float(random.uniform(-0.05, 0.05))
            }

            result = engine.run_simulation(portfolio_id, simulations, horizon_days)

            self.assertIsInstance(result, dict)
            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertIn("simulation_results", result)
            self.assertIn("var_95", result)
            self.assertIn("cvar_95", result)
            self.assertEqual(len(result["simulation_results"]), simulations)
            self.assertGreaterEqual(result["cvar_95"], result["var_95"])

    def test_run_simulation_attribute_error_fallback(self):
        engine = MonteCarloStressEngine()
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        simulations = 20
        horizon_days = 3

        with patch("skills.db_storage.fetch_portfolio", side_effect=AttributeError("No fetch_portfolio")):
            result = engine.run_simulation(portfolio_id, simulations, horizon_days)

            self.assertIsInstance(result, dict)
            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertIn("var_95", result)
            self.assertIn("cvar_95", result)
            self.assertGreaterEqual(result["cvar_95"], result["var_95"])

    def test_export_report_fallback(self):
        engine = MonteCarloStressEngine()
        report_id = f"rep_{uuid.uuid4().hex[:8]}"
        loss_limit = float(random.randint(1000, 50000))

        with patch("skills.market_portfolio_data_exporter.export", side_effect=AttributeError("No export")):
            res = engine.export_report(report_id, loss_limit)
            self.assertEqual(res["report_id"], report_id)
            self.assertEqual(res["loss_limit"], loss_limit)

    def test_consume_stream_fallback(self):
        engine = MonteCarloStressEngine()
        with patch("skills.market_portfolio_api_gateway.stream_payload", side_effect=AttributeError("No stream")):
            res = engine.consume_stream()
            self.assertIsNone(res)

    def test_run_monte_carlo_stress_test_execution(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        portfolio_value = float(random.randint(10000, 500000))
        iterations = random.randint(30, 100)
        scenario_params = {
            "volatility": float(random.uniform(0.1, 0.5)),
            "drift": float(random.uniform(-0.1, 0.1)),
            "horizon_days": int(random.randint(1, 10))
        }

        result = run_monte_carlo_stress_test(portfolio_id, portfolio_value, scenario_params, iterations)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["initial_value"], portfolio_value)
        self.assertEqual(result["iterations"], iterations)
        self.assertIn("simulation_id", result)
        self.assertIn("var_95", result)
        self.assertIn("expected_shortfall", result)
        self.assertGreaterEqual(result["expected_shortfall"], result["var_95"])


if __name__ == "__main__":
    unittest.main()