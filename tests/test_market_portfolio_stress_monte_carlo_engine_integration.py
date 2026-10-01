import unittest
import uuid
import random
from skills import market_portfolio_stress_monte_carlo_engine
from skills import db_storage
from skills import market_anomaly_detector
from skills import market_portfolio_scenario_simulator

class TestIntegrationMonteCarloStressEngine(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.initial_value = round(random.uniform(50000.0, 500000.0), 2)
        self.simulations = random.randint(100, 500)
        self.horizon_days = random.randint(5, 30)
        
        if not hasattr(db_storage, "_in_memory_db"):
            db_storage._in_memory_db = {}
            
        db_storage._in_memory_db[self.portfolio_id] = {
            "portfolio_id": self.portfolio_id,
            "initial_value": self.initial_value,
            "volatility": round(random.uniform(0.1, 0.4), 2),
            "drift": round(random.uniform(-0.05, 0.05), 4)
        }

    def test_monte_carlo_engine_integration_workflow(self):
        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        
        result = engine.run_simulation(
            portfolio_id=self.portfolio_id,
            simulations=self.simulations,
            horizon_days=self.horizon_days
        )
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertIn("simulation_results", result)
        self.assertIn("var_95", result)
        self.assertIn("cvar_95", result)
        
        sim_results = result.get("simulation_results")
        self.assertEqual(len(sim_results), self.simulations)
        
        scenario_params = {
            "volatility": 0.25,
            "drift": 0.01,
            "horizon_days": self.horizon_days
        }
        
        functional_result = market_portfolio_stress_monte_carlo_engine.run_monte_carlo_stress_test(
            portfolio_id=self.portfolio_id,
            portfolio_value=self.initial_value,
            scenario_params=scenario_params,
            iterations=self.simulations
        )
        
        self.assertIsInstance(functional_result, dict)
        self.assertEqual(functional_result.get("portfolio_id"), self.portfolio_id)
        self.assertIn("simulation_id", functional_result)
        self.assertTrue(functional_result.get("simulation_id").startswith("sim_"))
        self.assertEqual(functional_result.get("initial_value"), self.initial_value)
        self.assertGreaterEqual(functional_result.get("var_95"), 0.0)
        self.assertGreaterEqual(functional_result.get("expected_shortfall"), 0.0)

if __name__ == "__main__":
    unittest.main()