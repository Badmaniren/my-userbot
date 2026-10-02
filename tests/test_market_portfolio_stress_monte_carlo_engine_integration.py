import unittest
import uuid
import random

from skills import db_storage
from skills import market_anomaly_detector
from skills import market_portfolio_data_exporter
from skills import market_portfolio_api_gateway
from skills import market_portfolio_stress_monte_carlo_engine


class TestMonteCarloStressEngineIntegration(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.report_id = f"rep_{uuid.uuid4().hex[:8]}"
        self.initial_value = round(random.uniform(50000.0, 500000.0), 2)
        self.volatility = round(random.uniform(0.1, 0.5), 4)
        self.drift = round(random.uniform(-0.05, 0.05), 4)

        if hasattr(db_storage, "_in_memory_db") and isinstance(db_storage._in_memory_db, dict):
            db_storage._in_memory_db[self.portfolio_id] = {
                "portfolio_id": self.portfolio_id,
                "initial_value": self.initial_value,
                "volatility": self.volatility,
                "drift": self.drift
            }

    def test_monte_carlo_engine_simulation_flow(self):
        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        simulations_count = random.randint(10, 50)
        horizon = random.randint(5, 30)

        result = engine.run_simulation(
            portfolio_id=self.portfolio_id,
            simulations=simulations_count,
            horizon_days=horizon
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertIn("simulation_results", result)
        self.assertIn("var_95", result)
        self.assertIn("cvar_95", result)
        self.assertEqual(len(result["simulation_results"]), simulations_count)
        self.assertGreaterEqual(result["var_95"], 0.0)
        self.assertGreaterEqual(result["cvar_95"], 0.0)

    def test_standalone_stress_function_execution(self):
        iterations = random.randint(20, 100)
        scenario_params = {
            "volatility": self.volatility,
            "drift": self.drift,
            "horizon_days": random.randint(1, 15)
        }

        result = market_portfolio_stress_monte_carlo_engine.run_monte_carlo_stress_test(
            portfolio_id=self.portfolio_id,
            portfolio_value=self.initial_value,
            scenario_params=scenario_params,
            iterations=iterations
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(result.get("initial_value"), self.initial_value)
        self.assertEqual(result.get("iterations"), iterations)
        self.assertIn("simulation_id", result)
        self.assertTrue(result["simulation_id"].startswith("sim_"))
        self.assertIn("var_95", result)
        self.assertIn("expected_shortfall", result)

    def test_engine_export_and_stream(self):
        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        loss_limit = round(random.uniform(1000.0, 10000.0), 2)

        export_res = engine.export_report(self.report_id, loss_limit)
        self.assertIsInstance(export_res, dict)
        self.assertEqual(export_res.get("report_id"), self.report_id)
        self.assertEqual(export_res.get("loss_limit"), loss_limit)

        stream_res = engine.consume_stream()
        self.assertTrue(stream_res is None or isinstance(stream_res, (dict, str, bytes)))


if __name__ == "__main__":
    unittest.main()