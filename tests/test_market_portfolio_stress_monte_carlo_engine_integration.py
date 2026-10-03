import unittest
import uuid
import random

from skills import market_portfolio_stress_monte_carlo_engine
from skills import market_portfolio_audit_log_exporter
from skills import db_storage

class TestIntegrationMonteCarloStressEngine(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.initial_value = round(random.uniform(50000.0, 500000.0), 2)
        
        if hasattr(db_storage, "_in_memory_db") and isinstance(db_storage._in_memory_db, dict):
            db_storage._in_memory_db[self.portfolio_id] = {
                "portfolio_id": self.portfolio_id,
                "initial_value": self.initial_value,
                "volatility": 0.25,
                "drift": 0.02
            }

    def test_run_simulation_strict_and_audit_integration(self):
        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        simulations_count = random.randint(10, 50)
        horizon = random.randint(5, 30)

        result = engine.run_simulation(
            portfolio_id=self.portfolio_id,
            simulations=simulations_count,
            horizon_days=horizon
        )

        self.assertIn("portfolio_id", result)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertIn("simulation_results", result)
        self.assertIn("var_95", result)
        self.assertIn("cvar_95", result)
        self.assertEqual(len(result["simulation_results"]), simulations_count)

        audit_data = market_portfolio_audit_log_exporter.export_logs() if hasattr(market_portfolio_audit_log_exporter, "export_logs") else {}
        self.assertIsNotNone(audit_data)

    def test_standalone_stress_function_randomized(self):
        scenario_params = {
            "volatility": round(random.uniform(0.1, 0.4), 2),
            "drift": round(random.uniform(-0.05, 0.05), 2),
            "horizon_days": random.randint(1, 15)
        }
        iterations = random.randint(20, 100)

        res = market_portfolio_stress_monte_carlo_engine.run_monte_carlo_stress_test(
            portfolio_id=self.portfolio_id,
            portfolio_value=self.initial_value,
            scenario_params=scenario_params,
            iterations=iterations
        )

        self.assertIn("simulation_id", res)
        self.assertTrue(res["simulation_id"].startswith("sim_"))
        self.assertEqual(res["portfolio_id"], self.portfolio_id)
        self.assertEqual(res["initial_value"], self.initial_value)
        self.assertEqual(res["iterations"], iterations)
        self.assertGreaterEqual(res["var_95"], 0.0)

if __name__ == "__main__":
    unittest.main()