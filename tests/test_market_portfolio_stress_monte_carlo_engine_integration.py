import unittest
import uuid
import random
from skills import db_storage
from skills import market_portfolio_stress_monte_carlo_engine

class TestIntegrationMonteCarloStressEngine(unittest.TestCase):

    def test_run_simulation_and_stress_test_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        initial_value = round(random.uniform(50000.0, 500000.0), 2)
        volatility = round(random.uniform(0.1, 0.5), 4)
        drift = round(random.uniform(-0.05, 0.05), 4)

        if hasattr(db_storage, "save_portfolio"):
            db_storage.save_portfolio({
                "portfolio_id": portfolio_id,
                "initial_value": initial_value,
                "volatility": volatility,
                "drift": drift
            })
        elif hasattr(db_storage, "_in_memory_db"):
            db_storage._in_memory_db[portfolio_id] = {
                "portfolio_id": portfolio_id,
                "initial_value": initial_value,
                "volatility": volatility,
                "drift": drift
            }

        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        simulations_count = random.randint(100, 500)
        horizon_days = random.randint(10, 30)

        sim_result = engine.run_simulation(portfolio_id, simulations=simulations_count, horizon_days=horizon_days)

        self.assertIsInstance(sim_result, dict)
        self.assertEqual(sim_result["portfolio_id"], portfolio_id)
        self.assertIn("simulation_results", sim_result)
        self.assertIn("var_95", sim_result)
        self.assertIn("cvar_95", sim_result)
        self.assertEqual(len(sim_result["simulation_results"]), simulations_count)

        scenario_params = {
            "volatility": volatility,
            "drift": drift,
            "horizon_days": horizon_days
        }
        iterations_count = random.randint(100, 500)

        stress_result = market_portfolio_stress_monte_carlo_engine.run_monte_carlo_stress_test(
            portfolio_id=portfolio_id,
            portfolio_value=initial_value,
            scenario_params=scenario_params,
            iterations=iterations_count
        )

        self.assertIsInstance(stress_result, dict)
        self.assertTrue(stress_result["simulation_id"].startswith("sim_"))
        self.assertEqual(stress_result["portfolio_id"], portfolio_id)
        self.assertEqual(stress_result["initial_value"], initial_value)
        self.assertEqual(stress_result["iterations"], iterations_count)
        self.assertIn("var_95", stress_result)
        self.assertIn("expected_shortfall", stress_result)

if __name__ == "__main__":
    unittest.main()