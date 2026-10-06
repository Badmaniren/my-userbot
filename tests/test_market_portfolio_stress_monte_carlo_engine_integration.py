import unittest
import uuid
import random
from skills import db_storage
from skills import market_portfolio_stress_monte_carlo_engine

class TestMarketPortfolioStressMonteCarloEngineIntegration(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.initial_value = round(random.uniform(50000.0, 500000.0), 2)
        
        if not hasattr(db_storage, "_in_memory_db"):
            db_storage._in_memory_db = {}
            
        db_storage._in_memory_db[self.portfolio_id] = {
            "portfolio_id": self.portfolio_id,
            "initial_value": self.initial_value,
            "volatility": round(random.uniform(0.1, 0.4), 2),
            "drift": round(random.uniform(-0.05, 0.05), 4)
        }

    def tearDown(self):
        if hasattr(db_storage, "_in_memory_db") and self.portfolio_id in db_storage._in_memory_db:
            del db_storage._in_memory_db[self.portfolio_id]

    def test_monte_carlo_engine_simulation_and_function(self):
        simulations_count = random.randint(50, 200)
        horizon = random.randint(5, 30)
        
        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        result = engine.run_simulation(
            portfolio_id=self.portfolio_id,
            simulations=simulations_count,
            horizon_days=horizon
        )
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertIn("var_95", result)
        self.assertIn("cvar_95", result)
        self.assertIn("simulation_results", result)
        self.assertEqual(len(result["simulation_results"]), simulations_count)

        iterations_count = random.randint(50, 150)
        scenario_params = {
            "volatility": round(random.uniform(0.15, 0.35), 2),
            "drift": 0.01,
            "horizon_days": random.randint(1, 10)
        }
        
        func_result = market_portfolio_stress_monte_carlo_engine.run_monte_carlo_stress_test(
            portfolio_id=self.portfolio_id,
            portfolio_value=self.initial_value,
            scenario_params=scenario_params,
            iterations=iterations_count
        )
        
        self.assertIsInstance(func_result, dict)
        self.assertEqual(func_result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(func_result.get("initial_value"), self.initial_value)
        self.assertIn("simulation_id", func_result)
        self.assertTrue(func_result["simulation_id"].startswith("sim_"))
        self.assertIn("var_95", func_result)
        self.assertIn("expected_shortfall", func_result)
        self.assertEqual(func_result["iterations"], iterations_count)

if __name__ == "__main__":
    unittest.main()