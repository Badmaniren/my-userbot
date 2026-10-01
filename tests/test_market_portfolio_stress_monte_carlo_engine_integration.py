import unittest
import uuid
import random
from skills import market_portfolio_stress_monte_carlo_engine
from skills import db_storage

class TestMarketPortfolioStressMonteCarloIntegration(unittest.TestCase):
    def test_monte_carlo_engine_integration_workflow(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        initial_value = round(random.uniform(50000.0, 500000.0), 2)
        simulations_count = random.randint(100, 500)
        horizon = random.randint(5, 30)

        if not hasattr(db_storage, "_in_memory_db"):
            db_storage._in_memory_db = {}

        db_storage._in_memory_db[portfolio_id] = {
            "portfolio_id": portfolio_id,
            "initial_value": initial_value,
            "volatility": 0.25,
            "drift": 0.05
        }

        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        result = engine.run_simulation(portfolio_id, simulations=simulations_count, horizon_days=horizon)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertIn("simulation_results", result)
        self.assertIn("var_95", result)
        self.assertIn("cvar_95", result)
        self.assertEqual(len(result["simulation_results"]), simulations_count)

        scenario_params = {
            "volatility": 0.3,
            "drift": 0.02,
            "horizon_days": horizon
        }
        functional_result = market_portfolio_stress_monte_carlo_engine.run_monte_carlo_stress_test(
            portfolio_id=portfolio_id,
            portfolio_value=initial_value,
            scenario_params=scenario_params,
            iterations=simulations_count
        )

        self.assertIsInstance(functional_result, dict)
        self.assertTrue(functional_result["simulation_id"].startswith("sim_"))
        self.assertEqual(functional_result["portfolio_id"], portfolio_id)
        self.assertEqual(functional_result["initial_value"], initial_value)
        self.assertEqual(functional_result["iterations"], simulations_count)
        self.assertGreaterEqual(functional_result["var_95"], 0.0)
        self.assertGreaterEqual(functional_result["expected_shortfall"], 0.0)

if __name__ == "__main__":
    unittest.main()