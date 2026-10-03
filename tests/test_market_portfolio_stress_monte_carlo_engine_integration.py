import unittest
import uuid
import random

from skills import db_storage
from skills import market_portfolio_audit_compliance_hub
from skills import market_portfolio_stress_monte_carlo_engine


class TestMonteCarloStressEngineIntegration(unittest.TestCase):

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

    def test_run_simulation_integration_and_audit(self):
        simulations = random.randint(50, 200)
        horizon_days = random.randint(5, 30)

        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        result = engine.run_simulation(
            portfolio_id=self.portfolio_id,
            simulations=simulations,
            horizon_days=horizon_days
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertIn("simulation_results", result)
        self.assertIn("var_95", result)
        self.assertIn("cvar_95", result)
        self.assertEqual(len(result["simulation_results"]), simulations)
        self.assertGreaterEqual(result["var_95"], 0.0)
        self.assertGreaterEqual(result["cvar_95"], 0.0)

    def test_run_monte_carlo_stress_test_function(self):
        iterations = random.randint(50, 150)
        scenario_params = {
            "volatility": round(random.uniform(0.1, 0.4), 2),
            "drift": round(random.uniform(-0.05, 0.05), 2),
            "horizon_days": random.randint(1, 15)
        }

        result = market_portfolio_stress_monte_carlo_engine.run_monte_carlo_stress_test(
            portfolio_id=self.portfolio_id,
            portfolio_value=self.initial_value,
            scenario_params=scenario_params,
            iterations=iterations
        )

        self.assertIsInstance(result, dict)
        self.assertTrue(result["simulation_id"].startswith("sim_"))
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["initial_value"], self.initial_value)
        self.assertEqual(result["iterations"], iterations)
        self.assertIn("var_95", result)
        self.assertIn("expected_shortfall", result)


if __name__ == "__main__":
    unittest.main()