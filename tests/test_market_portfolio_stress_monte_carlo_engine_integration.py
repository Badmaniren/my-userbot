import unittest
import uuid
import random
from skills import db_storage
from skills import market_anomaly_detector
from skills import market_portfolio_stress_monte_carlo_engine

class TestMonteCarloStressEngineIntegration(unittest.TestCase):
    def test_end_to_end_monte_carlo_simulation(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        initial_value = float(random.randint(50000, 200000))
        volatility = round(random.uniform(0.1, 0.4), 2)
        drift = round(random.uniform(-0.05, 0.05), 4)

        if not hasattr(db_storage, "_in_memory_db"):
            setattr(db_storage, "_in_memory_db", {})
        
        db_storage._in_memory_db[portfolio_id] = {
            "portfolio_id": portfolio_id,
            "initial_value": initial_value,
            "volatility": volatility,
            "drift": drift
        }

        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        simulations_count = 100
        horizon = 10

        result = engine.run_simulation(portfolio_id, simulations=simulations_count, horizon_days=horizon)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertIn("simulation_results", result)
        self.assertIn("var_95", result)
        self.assertIn("cvar_95", result)
        
        sim_results = result["simulation_results"]
        self.assertEqual(len(sim_results), simulations_count)
        for path in sim_results:
            self.assertEqual(len(path), horizon)

        scenario_params = {
            "volatility": volatility,
            "drift": drift,
            "horizon_days": horizon
        }
        standalone_result = market_portfolio_stress_monte_carlo_engine.run_monte_carlo_stress_test(
            portfolio_id=portfolio_id,
            portfolio_value=initial_value,
            scenario_params=scenario_params,
            iterations=simulations_count
        )

        self.assertIsInstance(standalone_result, dict)
        self.assertEqual(standalone_result.get("portfolio_id"), portfolio_id)
        self.assertEqual(standalone_result.get("initial_value"), initial_value)
        self.assertEqual(standalone_result.get("iterations"), simulations_count)
        self.assertIn("simulation_id", standalone_result)
        self.assertTrue(standalone_result["simulation_id"].startswith("sim_"))

if __name__ == "__main__":
    unittest.main()